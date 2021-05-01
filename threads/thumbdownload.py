from threading import Thread
from common import mk_logger, posix_path, pure_windows_path, cache_path, thumb_dir, local_path_exists
from os import makedirs

logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


class ThumbDownload(Thread):
    def __init__(self, manager, sftp, data):
        super().__init__()
        self.manager = manager
        self.src_path = data['src_path']
        self.dst_path = pure_windows_path(cache_path, data['dst_path'].strip('/'), thumb_dir)
        self.thumbnails = data['thumbnails']
        self.callback = data['callback']
        self.sftp = sftp

    def run(self):
        for thumbnail in self.thumbnails:
            try:
                src = posix_path(self.src_path, thumbnail)
                if not local_path_exists(self.dst_path):
                    makedirs(self.dst_path)
                self.sftp.get(src, pure_windows_path(self.dst_path, thumbnail), preserve_mtime=True)

            except FileNotFoundError:
                pass

            except Exception as ex:
                ex_log(f'Failed to download thumbnail {str(ex)}')

        self.manager.thread_queue.put('.')
        self.manager.sftp_queue.put(self.sftp)
        self.manager.next_transfer()
        self.callback()
