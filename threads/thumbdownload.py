from threading import Thread
from common import mk_logger, posix_path, pure_windows_path, cache_path, thumb_dir


logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


class ThumbDownload(Thread):
    def __init__(self, src_path, thumbnails, dst_path, sftp, callback):
        super().__init__()
        self.src_path = src_path
        self.dst_path = pure_windows_path(cache_path, dst_path.strip('/'))
        self.sftp = sftp
        self.thumbnails = thumbnails
        self.callback = callback

    def run(self):
        for thumbnail in self.thumbnails:
            try:
                src = posix_path(self.src_path, thumbnail)
                if not self.sftp.exists(src):
                    raise FileNotFoundError
                self.sftp.get(src, pure_windows_path(self.dst_path, thumb_dir, thumbnail), preserve_mtime=True)

            except FileNotFoundError:
                pass

            except Exception as ex:
                ex_log(f'Failed to download thumbnail {str(ex)}')
            else:
                if self.callback:
                    self.callback(thumbnail)
