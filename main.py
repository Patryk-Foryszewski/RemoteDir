from common import mk_logger
from kivy.config import Config

Config.set('graphics', 'multisamples', '0')
Config.set('graphics', 'width', '1066')
Config.set('graphics', 'height', '600')
Config.set('input', 'mouse', 'mouse, multitouch_on_demand')
Config.set('kivy', 'exit_on_escape', '0')


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
from associationrow import AssociationRow
from colors import colors
from common import resource_path, img_path, thumbnails, app_name, version
import platform
import os
import sys
import subprocess

logger = mk_logger(__name__)
s_log = mk_logger(f'{__name__}S', _format='#%(message)-100s#').info


class Start:
    def __init__(self):
        # self.add_exclusion()
        self.log()
        self.check_argv()

    @staticmethod
    def log():
        s_log(100 * '#')
        s_log(f' REMOTEDIR {version} RUN')
        s_log(f' PYTHON VERSION {sys.version}')
        s_log(f' PYTHON INFO {sys.version_info}')
        s_log(f' SYSTEM INFO {platform.platform()}')
        s_log(f' SYS ARGV {sys.argv}')
        s_log(100 * '#')

    @staticmethod
    def add_exclusion():
        """
        Add path to windows defender exclusions (Doesn't work at the moment. User
        has to add path manually)
        """

        exe_path = rf'{sys.argv[0]}'
        cmd = f'powershell -inputformat none -outputformat none -NonInteractive ' \
              f'-Command Add-MpPreference -ExclusionPath {exe_path}'
        subprocess.run(["powershell", "-Command", cmd], capture_output=True)

    @staticmethod
    def check_argv():
        """
        Checks sys.argv for specific args and performs action.
        """

        if 'kill' in sys.argv:
            index = sys.argv.index('kill')
            to_kill = sys.argv[index + 1]
            logger.info(f'Killing {to_kill}')
            os.system(f'{os.environ["HOMEDRIVE"]}\windows\system32\\taskkill.exe /f /im {to_kill}')


Start()


class Main(App):

    def build(self):
        setattr(self, 'img_path', img_path)
        setattr(self, 'thumbnails', thumbnails())
        self.title = f'RemoteDir of {app_name}.  {version}'
        self.icon = img_path('dir.png')

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
    Factory.register('AssociationRow', cls=AssociationRow)
    Main().run()
