from multiprocessing import Process
from threading import Thread
from PIL import Image, UnidentifiedImageError
from common_funcs import mk_logger, pure_windows_path
from common_vars import cache_path, thumb_dir
from os import path, makedirs
from subprocess import check_output
from moviepy.editor import VideoFileClip

logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


class Thumbnail(Thread):

    def __init__(self, src_path, dst_path, size=(300, 200)):
        super().__init__()
        self._thumb_name = None
        self.thumb_name(src_path)
        self.src_path = src_path
        self.size = size
        self.cache_path = pure_windows_path(cache_path, dst_path.strip('/'), thumb_dir)
        self.thumb_path = pure_windows_path(self.cache_path, self._thumb_name)
        self.ok = False
        print('THUMBNAIL')
        print('     SRC', src_path)
        print('     DST', self.thumb_path)

    def run(self):
        if self._thumb_name:
            self.thumbnail()

    def thumbnail(self):
        if not self._thumb_name:
            return

        if not path.exists(self.cache_path):
            makedirs(self.cache_path)

        try:
            im = Image.open(self.src_path)
            im.thumbnail(self.size)
            im.save(self.thumb_path)
        except UnidentifiedImageError:
            pass

        except Exception as ex:
            ex_log(f'Failed to make a thumbnail {ex}')
        else:
            self.ok = True
            return

        try:
            clip = VideoFileClip(self.src_path)
            clip.save_frame(self.thumb_path, t=1.00)
        except Exception as ex:
            ex_log(f'Failed to make a thumbnail {ex}')
        else:
            self.ok = True
            return

    def thumb_name(self, src_path):
        name = path.split(src_path)[1].split('.')
        if len(name) > 1:
            self._thumb_name = '.'.join([name[0], 'jpg'])

