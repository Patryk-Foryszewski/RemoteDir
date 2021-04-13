from threading import Thread
from paramiko.ssh_exception import SSHException
from common import posix_path, mk_logger, forbidden_names, filename
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
        self.data = data
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

        except IOError as io:
            ex_log(f'Failed to remove directory {io}')
            if 'Socket is closed' in io:
                self.manager.connection_error()
                self.manager.put_transfer({**self.data})
                ex_log(f'Uploading {filename(self.remote_path)} exception. {io}')
            elif io.errno == 13:  # Permission denied
                logger.warning('Could not list directory. Permission denied.')

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
            if _path == self.remote_path:
                self.on_remove()
        finally:
            self.manager.sftp_queue.put(self.sftp)
            self.manager.thread_queue.put('.')
            self.manager.next_transfer()

    def forbidden(self, _filename):
        if _filename in forbidden_names:
            return True
        return False

    def error(self, ex):
        _filename = path.split(self.remote_path)[1]
        if not self.forbidden(_filename):
            error = InfoLabel(text=f'Failed to remove  {_filename}: {type(ex)}')
            self.progress_box.add_bar(error)

    def info(self, _filename):
        if not self.forbidden(_filename):
            info = InfoLabel(text=f'Successfully removed {_filename}')
            self.progress_box.add_bar(info)
