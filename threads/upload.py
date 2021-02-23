from threading import Thread
from common_funcs import posix_path, mk_logger
import os

logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


class Upload(Thread):
    def __init__(self, data, manager, bar, sftp, preserve_mtime=False):
        super().__init__()
        self.data = data
        self.dst_path = data['dst_path']
        self.src_path = data['src_path']
        self.file_name = os.path.split(self.src_path)[1]
        self.full_remote_path = posix_path(self.dst_path, self.file_name)
        self.manager = manager
        self.bar = bar
        self.sftp = sftp
        self.preserve_mtime = preserve_mtime or data.get('preserve_mtime')
        self.done = False
        self.waiting_for_directory = None
        self.attrs = None

    def run(self):
        self.bar.my_thread = self
        logger.info(f'Uploading file - {self.file_name}')
        self.bar.set_values(f'Uploading {self.src_path} to {self.dst_path}')
        try:
            if self.data.get('overwrite'):
                self.sftp.remove(self.full_remote_path)
            else:
                self.file_exists()
            self.put()

        except FileExistsError:
            logger.info(f'File {self.file_name} exists')
            self.bar.file_exists_error()

        except IOError as io:
            ex_log(f'Uploading {self.file_name} exception. {io}')
            if 'Socket is closed' in str(io):
                self.manager.connection_error()
                self.manager.put_transfer({**self.data, 'overwrite': True}, bar=self.bar)
            else:
                self.waiting_for_directory = True
                self.bar.set_values(f'Waiting for directory')

        except EOFError as eer:
            ex_log(f'Uploading {self.file_name} exception. {eer}')
            self.manager.put_transfer({**self.data, 'overwrite': True}, bar=self.bar)

        except Exception as ex:
            ex_log(f'Uploading {self.file_name} unknown exception. {ex}')

        else:
            logger.info(f'Uploading {self.file_name} completed successfully')
            self.done = True
            self.bar.done()
            self.manager.uploaded(self.dst_path, self.attrs)

        finally:
            self.manager.sftp_queue.put(self.sftp)
            self.manager.thread_queue.put('.')

    def file_exists(self):
        if self.sftp.exists(self.full_remote_path):
            raise FileExistsError

    def put(self):
        self.attrs = self.sftp.put(localpath=self.src_path,
                                   remotepath=self.full_remote_path,
                                   callback=self.bar.update,
                                   preserve_mtime=self.preserve_mtime)
        if self.attrs.st_size == 0:
            self.bar.update(1, 1)
        self.attrs.filename = self.file_name
        self.attrs.longname = str(self.attrs)

    def overwrite(self):
        if not self.done:
            self.manager.put_transfer({**self.data, 'overwrite': True}, bar=self.bar)
            self.manager.run()

    def skip(self):
        self.done = True
        self.bar.set_values(f'Uploading {self.src_path} to {self.dst_path} - Skipped')
