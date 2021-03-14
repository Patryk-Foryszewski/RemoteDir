from threading import Thread
from common import is_local_file, mk_logger
from paramiko.ssh_exception import SSHException
import os

logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


class Download(Thread):
    def __init__(self, data, manager, sftp, bar, preserve_mtime=False):
        super().__init__()
        self.data = data
        self.src_path = data['src_path']
        self.dst_path = data['dst_path']
        self.dirpath, self.filename = os.path.split(self.src_path)
        self.manager = manager
        self.sftp = sftp
        self.bar = bar
        self.preserve_mtime = preserve_mtime
        self.done = False
        self.waiting_for_directory = None
        self.callback = None

    def run(self):
        logger.info(f'Downloading {self.filename}')
        self.bar.my_thread = self
        overwriting = self.data.get('overwrite')
        if overwriting or not self.exists():
            self.bar.set_values(f'{"Downloading" if not overwriting else "Overwriting"} {self.filename}')
            try:
                self.sftp.get(self.src_path, self.dst_path, callback=self.bar.update, preserve_mtime=self.preserve_mtime)

            except SSHException as she:
                ex_log(f'Failed to download {self.filename}. {str(she)}')
                if 'Server connection dropped' in str(she):
                    self.manager.connection_error()
                    self.bar.hide_actions()
                    # in case the transfer has interrupted because of connection issue overwrite it in next attempt
                    self.manager.put_transfer({**self.data, 'overwrite': True}, bar=self.bar)
            except OSError as ex:
                ex_log(f'Failed to download {self.filename}. {str(ex)}')
            else:
                logger.info(f'File {self.filename} downloaded succesfully')
                self.bar.done()
                self.done = True
                if self.callback:
                    self.callback(self.filename)

        self.manager.thread_queue.put('.')
        self.manager.sftp_queue.put(self.sftp)

    def exists(self):
        if is_local_file(self.dirpath):
            self.waiting_for_directory = True
            self.bar.set_values('Waiting for directory')
            return True
        elif os.path.exists(self.dst_path):
            self.bar.file_exists_error()
            self.bar.set_values(f'File {self.filename} already exists in destination directory.')
            return True
        else:
            return False

    def do_not_overwrite(self):
        self.done = True

    def overwrite(self):
        logger.info(f'Downloading {self.filename} - Skipped')
        if not self.done:
            self.manager.put_transfer({**self.data, 'overwrite': True}, bar=self.bar)
            self.manager.run()

    def skip(self):
        logger.info(f'Downloading {self.filename} - Skipped')
        self.done = True
        self.bar.set_values(f'Downloading {self.filename} - Skipped')
