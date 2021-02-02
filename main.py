from colors import colors
from kivy.app import App
from kivy.lang.builder import Builder
from remotedir import RemoteDir
from kivy.factory import Factory
from adjustabletextinput import AdjustableTextInput
import os

from kivy.config import Config
Config.set('graphics', 'multisamples', '0')
Config.set('graphics', 'width', '1066')
Config.set('graphics', 'height', '600')
Config.set('input', 'mouse', 'mouse, multitouch_on_demand')

CONNECTION = None


class Main(App):

    def build(self):

        for color in colors.items():
            setattr(self, color[0], color[1])

        for kv in os.listdir('front'):
            if kv != 'main.kv':
                Builder.load_file(f'front/{kv}')

        return Builder.load_file('front/main.kv')


if __name__ == '__main__':
    Factory.register('AdjustableTextInput', cls=AdjustableTextInput)

    Main().run()
