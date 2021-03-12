from threading import Thread
from common import posix_path, mk_logger, forbidden_names
from infolabel import InfoLabel
from os import path
import stat


logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


class RemoveRemoteDirectory(Thread):
    def __init__(self, manager, sftp, data):
        super().__init__()
        print('RemoveRemoteDirectory', data)
        self.remote_path = data['remote_path']
        self.sftp = sftp
        self.on_remove = data['on_remove']
        self.progress_box = data['progress_box']
        self.manager = manager

    def run(self):
        self.rmdir(self.remote_path)

    def rmdir(self, _path):

        try:
            for f in self.sftp.listdir_attr(_path):
                rpath = posix_path(_path, f.filename)
                if stat.S_ISDIR(f.st_mode):
                    self.rmdir(rpath)
                else:
                    rpath = posix_path(_path, f.filename)
                    self.sftp.remove(rpath)
                    # avoid to inform about files from directories like .thumbnails
                    for name in forbidden_names:
                        if name in _path:
                            break
                    else:
                        self.info(f.filename)

        except Exception as ex:
            ex_log(f'Failed to remove directory {ex}')
            self.error(ex)
            return

        try:
            self.sftp.rmdir(_path)
        except Exception as ex:
            ex_log(f'Failed to remove directory {ex}')
            self.error(ex)
        else:
            self.info(path.split(_path)[1])
            self.on_remove()

    def forbidden(self, filename):
        if filename in forbidden_names:
            return True
        return False

    def error(self, ex):
        filename = path.split(self.remote_path)[1]
        if not self.forbidden(filename):
            error = InfoLabel(text=f'Failed to remove  {filename}: {type(ex)}')
            self.progress_box.add_bar(error)

    def info(self, filename):
        if not self.forbidden(filename):
            info = InfoLabel(text=f'Successfully removed {filename}')
            self.progress_box.add_bar(info)
