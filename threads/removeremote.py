from threading import Thread
from common import posix_path, mk_logger
from functools import partial
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
                    rpath = posix_path(path, f.filename)
                    self.sftp.remove(rpath)

        except Exception as ex:
            ex_log(f'Failed to remove directory {ex}')
            return False
        else:
            logger.info(f'Succesfully removed file {path.split(_path)[1]}')

        try:
            self.sftp.rmdir(_path)
        except Exception as ex:
            ex_log(f'Failed to remove directory {ex}')
            return False
        else:
            self.on_remove()
