from kivy.uix.relativelayout import RelativeLayout
from common import config_file, default_remote, download_path, local_path_exists
from configparser import ConfigParser
from kivy.app import App


class Paths(RelativeLayout):
    auto_dismiss = False
    name = 'Paths'
    tags = ['path', 'default', 'download', 'download path', 'remote', 'remote path']

    def __init__(self):
        super().__init__()
        self.fill()

    def fill(self):
        self.ids.download_path.text = download_path()
        self.ids.default_remote.text = default_remote()



    def save_config(self):
        config = ConfigParser()
        download_path = self.ids.download_path.text
        default_remote = self.ids.default_remote.text

        err = False
        if not local_path_exists(download_path):
            self.ids.download_path_err.text = f"Path doesn't exists"
            err = True
        # if not App.get_running_app().root.remote_path_exists(default_remote):
        #     self.ids.default_remote_err.text = f"Path doesn't exists"
        #     err = True
        if err:
            return

        config.read(config_file)
        try:
            config.add_section('SETTINGS')
        except:
            pass

        config.set('SETTINGS', 'download_path', download_path)
        config.set('SETTINGS', 'default_remote', default_remote)
        with open(config_file, 'w') as f:
            config.write(f)
        #self.originator.dismiss()

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            self.save_config()
        super().on_touch_down(touch)
