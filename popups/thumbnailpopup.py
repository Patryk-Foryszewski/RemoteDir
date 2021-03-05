from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.window import Window
from processes.thumbnail import ThumbnailGenerator
from common_funcs import mk_logger, posix_path, pure_windows_path, file_ext
from common_vars import thumb_dir, cache_path
from shutil import copyfile
from os import path, remove

logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


class ThumbnailPopup(BoxLayout):
    def __init__(self, originator, destination, filename, sftp):
        super().__init__()
        self.originator = originator
        self.destination = destination
        self.filename = filename
        self.sftp = sftp
        Window.bind(on_dropfile=self.thumbnail_drop)

    def thumbnail_drop(self, _, src_path):
        print('THUMBNAIL DROP', src_path)
        src_path = src_path.decode(encoding='UTF-8', errors='strict')
        try:
            pic_name = '.'.join([path.split(self.filename)[1], 'jpg'])
            cache_pic = pure_windows_path(cache_path, pic_name)
            if path.exists(cache_pic):
                remove(cache_pic)
            copyfile(src_path, cache_pic)

        except Exception as ex:
            print('FAILED TO MOVE PIC', ex)
            return

        th = ThumbnailGenerator(src_path=cache_pic, dst_path=self.destination)
        th.start()
        th.join()
        if th.ok:
            print('Thumbnail Generated')
            try:
                print('     SRC_PATH', th.thumb_path)
                print('     DST_PATH', posix_path(self.destination, thumb_dir, self.filename))
                self.sftp.put(th.thumb_path, posix_path(self.destination, thumb_dir, self.filename), preserve_mtime=True)
            except Exception as ex:
                ex_log(f'Failed to upload thumbnail for {self.filename}')
            else:
                self.popup.title = 'Thumbnail uploaded succesfully'
                self.originator.refresh_thumbnail(self.filename)

                def dismiss_popup(_):
                    self.popup.dismiss()
                Clock.schedule_once(dismiss_popup, .8)
        else:
            self.popup.title = 'Failed to upload thumbnail'
