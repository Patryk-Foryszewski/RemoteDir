from kivy.uix.relativelayout import RelativeLayout
from common import config_file, thumbnails
from configparser import ConfigParser

class Thumbnails(RelativeLayout):
    auto_dismiss = False
    name = 'Thumbnails'
    tags = ['thumbnail', 'thumbnails']

    def __init__(self):
        super().__init__()
        self.fill()

    def fill(self):
        self.ids.enable_thumbnails.state = 1 if thumbnails() else 0

    def save_config(self):
        config = ConfigParser()
        enable_thumbnails = str(self.ids.enable_thumbnails.active)
        err = False
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

        config.set('SETTINGS', 'enable_thumbnails', enable_thumbnails)
        with open(config_file, 'w') as f:
            config.write(f)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            self.save_config()
        super().on_touch_down(touch)
