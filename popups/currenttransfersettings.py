from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import ListProperty, DictProperty, StringProperty
from kivy.uix.popup import Popup
from kivy.clock import Clock
from common import filename, dst_path, unix_time, convert_file_size, get_config, config_file, TransferSettingsMapper


class CurrentTransferSettings(RelativeLayout):
    tsm = TransferSettingsMapper()
    transfers_list = ListProperty([])
    source = DictProperty({'name': '', 'date': '', 'size': '', 'path': ''})
    target = DictProperty({'name': '', 'date': '', 'size': '', 'path': ''})
    out_of = StringProperty('')
    option_text = StringProperty('')

    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.current_index = 0
        self.transfers_list = []
        self.type = ''
        self.settings_dict = {'option': 'Skip', 'range': 'Ask everytime'}
        self.pop_me()

    def append_transfers_list(self, transfer):
        if len(self.transfers_list) == 0:
            self.type = transfer[0]['type']
            if self.type == 'upload':
                self.option_text = 'Choose option for uploads'
            else:
                self.option_text = 'Choose option for downloads'
            self.set_attrs(transfer[0])

        self.transfers_list.append(transfer)
        self._out_of()
        print('LIST', len(self.transfers_list),  transfer[0]['src_path'])

    def _out_of(self):

        if self.current_index > len(self.transfers_list):
            self.current_index -= 1

        self.out_of = f'{self.current_index + 1}/{len(self.transfers_list)}'

    def set_attrs(self, file):
        #print('SET ATTRS', file)
        source_attrs = file['source_attrs']
        #print('     Source ATTRS', source_attrs)

        self.source = {'name': filename(file['src_path']),
                       'date': unix_time(source_attrs.st_atime),
                       'size': convert_file_size(source_attrs.st_size),
                       'path': dst_path(file['src_path'])}

        target_attrs = file['target_attrs']
        self.target = {'name': target_attrs.filename,
                       'date': unix_time(target_attrs.st_atime),
                       'size': convert_file_size(target_attrs.st_size),
                       'path': file['dst_path']}

    def next_file(self):
        print('NEXT FILE', self.current_index, len(self.transfers_list))
        if self.current_index < len(self.transfers_list) - 1:
            self.current_index += 1
            file = self.transfers_list[self.current_index][0]
            self.set_attrs(file)
            self._out_of()

    def set_option(self, option):
        print('SET OPTION', option)
        self.settings_dict['option'] = option

    def set_range(self, _range):
        self.settings_dict['range'] = _range

    def previous_file(self):
        print('PREVIOUS FILE', self.current_index)
        if self.current_index > 0:
            self.current_index -= 1
            file = self.transfers_list[self.current_index][0]
            self.set_attrs(file)
            self._out_of()

    def pop_me(self):
        def pop(_):
            content = self
            self.popup = Popup(
                title=f'Target file already exists. Choose action to perform',
                auto_dismiss=False,
                content=content,
                size_hint=(0.7, 0.9))

            self.popup.open()

        Clock.schedule_once(pop, .1)

    def overwrite(self, transfer):
        print('OVERWRITE', transfer)
        transfer[0]['overwrite'] = True
        self.manager.put_transfer(data=transfer[0], bar=transfer[1])
        index = self.transfers_list.index(transfer)
        self.transfers_list.pop(index)
        self._out_of()

    def decisive_block(self, transfer):
        option = self.settings_dict['option']
        if option == 'Skip':
            index = self.transfers_list.index(transfer)
            self.set_attrs(self.transfers_list[index][0])
            thread = self.transfers_list[index][2]
            thread.skip()
            self.transfers_list.pop(index)
            self._out_of()
        elif option == 'Overwrite':
            self.overwrite(transfer)
        elif option == 'Overwrite if source is newer':
            if transfer['source_attrs'].st_atime > transfer['target_attrs'].st_atime:
                self.overwrite(transfer)
        elif option == 'Overwrite if size is different':
            if transfer[0]['source_attrs'].st_size != transfer[0]['target_attrs'].st_size:
                self.overwrite(transfer)

    def skip(self, transfer):
        self.set_attrs(transfer[0])
        thread = transfer[2]
        thread.skip()
        self.transfers_list.remove(transfer)
        self._out_of()

    def skip_or_renew(self, option, transfer):
        if option == 'Skip':
            self.skip(transfer)
        else:
            transfer[0]['settings'] = option
            self.manager.put_transfer(data=transfer[0], bar=transfer[1])

    def set_for_all_transfers(self, option):
        for i in range(len(self.transfers_list) - 1, -1, -1):
            transfer = self.transfers_list[i]
            self.skip_or_renew(option, transfer)

    def ok(self):
        print('OK', self.settings_dict)
        _range = self.tsm._range(self.settings_dict['range'])
        option = self.tsm._option(self.settings_dict['option'])

        if _range == 'rng1':    # Ask everytime
            transfer = self.transfers_list[self.current_index]
            self.skip_or_renew(option, transfer)

        elif _range == 'rng2':  # Apply only for this session'
            if self.type == 'upload':
                self.manager.set_transfer_settings(uploads=option)
            else:
                self.manager.set_transfer_settings(downloads=option)
            self.set_for_all_transfers(option)
            self.popup.dismiss()

        elif _range == 'rng3':  # 'Set as default':
            config = get_config()
            # noinspection PyBroadException
            try:
                config.add_section('DEFAULTS')
            except Exception:
                pass
            config.set('DEFAULTS', self.type, option)
            with open(config_file, 'w+') as f:
                config.write(f)

            self.manager.get_default_settings()
            self.set_for_all_transfers(option)

            self.popup.dismiss()
        self.manager.start_transfers()

        if len(self.transfers_list) == 0:
            self.popup.dismiss()

    def cancel(self):
        self.popup.dismiss()
