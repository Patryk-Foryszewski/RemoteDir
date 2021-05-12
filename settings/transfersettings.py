from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.clock import Clock
from common import get_config, config_file, TransferSettingsMapper
from kivy.properties import StringProperty


class TransferSettings(BoxLayout):
    tsm = TransferSettingsMapper()
    download_setting = StringProperty(tsm.options_dict['opt1'])
    upload_setting = StringProperty(tsm.options_dict['opt2'])
    timeshift = StringProperty('0')
    name = 'Transfers'
    tags = ['overwrite', 'transfers']

    def __init__(self):
        super().__init__()
        self.fill()

    def on_timeshift(self, *args):
        if self.timeshift in ['', '-', '+']:
            return
        try:
            int(self.timeshift)
            # if 0 > int(self.timeshift) < 24:
            #     raise ValueError
        # except ValueError:
        #    self.ids.timezone_err.text = 'Wrong value. Must be between -12 and 24'
        #    return
        except Exception as ex:
            self.ids.timezone_err.text = f'Value must be integer {type(ex)}'
            return
        else:
            self.ids.timezone_err.text = ''

        config = get_config()
        # noinspection PyBroadException
        try:
            config.add_section('DEFAULTS', 'timeshift', self.timeshift)
        except Exception:
            pass
        config.set('DEFAULTS', 'timeshift', self.timeshift)

    def on_download_setting(self, *_):
        config = get_config()
        # noinspection PyBroadException
        try:
            config.add_section('DEFAULTS')
        except Exception:
            pass

        config.set('DEFAULTS', 'download', self.tsm._option(self.download_setting))
        with open(config_file, 'w+') as f:
            config.write(f)

    def on_upload_setting(self, *_):
        config = get_config()
        # noinspection PyBroadException
        try:
            config.add_section('DEFAULTS')
        except Exception:
            pass

        config.set('DEFAULTS', 'upload', self.tsm._option(self.upload_setting))
        with open(config_file, 'w+') as f:
            config.write(f)

    def fill(self):
        config = get_config()
        # noinspection PyBroadException
        try:
            self.download_setting = self.tsm._option(config.get('DEFAULTS', 'download'))
        except Exception:
            pass
        # noinspection PyBroadException
        try:
            self.upload_setting = self.tsm._option(config.get('DEFAULTS', 'upload'))
        except Exception:
            pass

    def on_dismiss(self):
        return True
