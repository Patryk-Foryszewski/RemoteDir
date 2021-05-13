from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.window import Window
from processes.thumbnail import ThumbnailGenerator
from common import mk_logger, pure_posix_path, pure_windows_path, thumb_dir, cache_path, dst_path
from shutil import copyfile
from os import path, remove, makedirs

logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


class ThumbnailPopup(BoxLayout):
    def __init__(self, originator, destination, filename, sftp, on_popup):
        super().__init__()
        self.originator = originator
        self.destination = destination
        self.filename = filename
        self.sftp = sftp
        self.pic_name = None
        self.thumbnail = None
        Window.bind(on_dropfile=self.thumbnail_drop)
        Clock.schedule_once(on_popup, 0.1)

    def thumbnail_drop(self, _, src_path):
        src_path = src_path.decode(encoding='UTF-8', errors='strict')
        self.thumbnail = path.split(src_path)[1]
        self.pic_name = f'{self.filename}.jpg'
        cache_pic = pure_windows_path(cache_path, self.thumbnail)
        try:
            if path.exists(cache_pic):
                remove(cache_pic)
            if not path.exists(cache_path):
                makedirs(cache_path)
            copyfile(src_path, cache_pic)

        except Exception as ex:
            self.popup.title = f'Failed to generate thumbnail {ex}'
            return

        th = ThumbnailGenerator(src_path=cache_pic, dst_path='')
        th.start()
        th.join()
        if th.ok:
            self.popup.title = 'Thumbnail generated'
            cache_pic = pure_windows_path(cache_path, self.destination.strip('/'), thumb_dir, self.pic_name)

            try:
                if not path.exists(dst_path(cache_pic)):
                    makedirs(dst_path(cache_pic))
                
                if path.exists(cache_pic):
                    remove(cache_pic)

                copyfile(th.thumb_path, cache_pic)
                self.sftp.put(cache_pic, pure_posix_path(self.destination, thumb_dir, self.pic_name), preserve_mtime=True)
            except Exception as ex:
                self.popup.title = f'Failed to upload thumbnail for {self.filename} {type(ex)}'
                ex_log(f'Failed to upload thumbnail for {self.filename} {ex}')
            else:
                self.popup.title = 'Thumbnail uploaded succesfully'
                self.originator.bind_external_drop()

                def dismiss_popup(_):
                    self.popup.dismiss()
                    self.originator.refresh_thumbnail(self.filename)
                Clock.schedule_once(dismiss_popup, .8)
                Window.unbind(on_dropfile=self.thumbnail_drop)
        else:
            self.popup.title = 'Failed to upload thumbnail'
