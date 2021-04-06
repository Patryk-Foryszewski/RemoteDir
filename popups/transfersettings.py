from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.clock import Clock
from common import get_config, config_file
from kivy.properties import StringProperty, BoundedNumericProperty


class TransferSettings(BoxLayout):
    download_setting = StringProperty('Ask everytime')
    upload_setting = StringProperty('Ask everytime')
    timeshift = StringProperty('0')

    def __init__(self):
        super().__init__()
        self.fill()
        self.pop_me()

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

        config.set('DEFAULTS', 'download', self.download_setting)
        with open(config_file, 'w+') as f:
            config.write(f)

    def on_upload_setting(self, *_):
        config = get_config()
        # noinspection PyBroadException
        try:
            config.add_section('DEFAULTS')
        except Exception:
            pass

        config.set('DEFAULTS', 'upload', self.upload_setting)
        with open(config_file, 'w+') as f:
            config.write(f)

    def fill(self):
        config = get_config()
        # noinspection PyBroadException
        try:
            self.download_setting = config.get('DEFAULTS', 'download')
        except Exception:
            pass
        # noinspection PyBroadException
        try:
            self.upload_setting = config.get('DEFAULTS', 'upload')
        except Exception:
            pass

    def pop_me(self):
        def pop(_):
            content = self
            self.popup = Popup(
                title=f'Set default action to perform if file already exists',
                auto_dismiss=True,
                content=content,
                size_hint=(0.7, 0.7))

            self.popup.open()

        Clock.schedule_once(pop, .1)
