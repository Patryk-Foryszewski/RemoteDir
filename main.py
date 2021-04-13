from common_funcs import mk_logger
from kivy.config import Config

Config.set('graphics', 'multisamples', '0')
Config.set('graphics', 'width', '1066')
Config.set('graphics', 'height', '600')
Config.set('input', 'mouse', 'mouse, multitouch_on_demand')

from colors import colors
from common import resource_path, img_path, thumbnails
from kivy.app import App
from kivy.lang.builder import Builder
from remotedir import RemoteDir
from kivy.factory import Factory
from adjustabletextinput import AdjustableTextInput
from threestatecheckbox import ThreeStateCheckbox
from bulbtextinput import BulbTextInput
from bulbimage import BulbImage
from progressbox import ProgressBox
from filesspace import FilesSpace
import os
logger = mk_logger(__name__)


class Main(App):
    def build(self):
        logger.info('APP STARTED')
        setattr(self, 'img_path', img_path)
        setattr(self, 'thumbnails', thumbnails())

        for color in colors.items():
            setattr(self, color[0], color[1])

        try:
            for kv in os.listdir(resource_path('front')):
                if kv != 'main.kv':
                    Builder.load_file(resource_path('front', kv))
        except Exception as ex:
            logger.exception(f'Failed to load .kv {ex}')
        else:
            return Builder.load_file(resource_path('front', 'main.kv'))


if __name__ == '__main__':
    Factory.register('RemoteDir', cls=RemoteDir)
    Factory.register('AdjustableTextInput', cls=AdjustableTextInput)
    Factory.register('FilesSpace', cls=FilesSpace)
    Factory.register('ProgressBox', cls=ProgressBox)
    Factory.register('ThreeStateCheckbox', cls=ThreeStateCheckbox)
    Factory.register('BulbTextInput', cls=BulbTextInput)
    Factory.register('BulbImage', cls=BulbImage)
    Main().run()
