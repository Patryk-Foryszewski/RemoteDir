from threading import Thread
from common import is_local_file, mk_logger, get_dir_attrs
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
        self.settings = data['settings']

    def run(self):
        logger.info(f'Downloading {self.filename}')
        self.bar.my_thread = self

        self.bar.set_values(f'{"Downloading" if not self.data.get("overwrite") else "Overwriting"} {self.filename}')
        try:
            if self.prepare_to_get():
                self.sftp.get(remotepath=self.src_path,
                              localpath=self.dst_path,
                              callback=self.bar.update,
                              preserve_mtime=self.preserve_mtime)

        except FileExistsError as fe:
            fe = str(fe)
            if fe == 'opt1':
                text = f'File {self.dst_path} already exists'
                logger.info(text)
                self.bar.file_exists_error(text=text)
                self.manager.add_to_existing_files(data=self.data, bar=self.bar, thread=self)

            elif fe == 'opt2':
                self.skip()
                text = f'File {self.dst_path} already exists. Skipped.'
                logger.info(text)

            elif fe == 'opt4':
                self.skip()
                text = f'File {self.dst_path} already exists. Skipped, not newer'
                logger.info(text)

            elif fe == 'opt5':
                self.skip()
                text = f'File {self.dst_path} already exists. Skipped, size not different'
                logger.info(text)

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
        finally:
            self.manager.thread_queue.put('.')
            self.manager.sftp_queue.put(self.sftp)

    def exists(self):
        if is_local_file(self.dirpath):
            self.waiting_for_directory = True
            self.bar.set_values('Waiting for directory')
            return True

    def do_not_overwrite(self):
        self.done = True

    def get_attrs(self):
        try:
            target_attrs = os.lstat(self.src_path)
            source_attrs = get_dir_attrs(self.dst_path, self.sftp)
        except Exception as ex:
            ex_log(f'Could not compare file attrs {ex}')
            return None, None
        else:
            return source_attrs, target_attrs

    def prepare_to_get(self):
        if os.path.exists(self.src_path):
            print('PREPARE TO GET', self.settings, self.data.get('overwrite'))

            if self.data.get('overwrite'):
                os.remove(self.src_path)
                return True

            elif self.settings == 'opt1':
                raise FileExistsError('opt1')

            elif self.settings == 'opt2':
                raise FileExistsError('opt2')

            elif self.settings == 'opt3':
                os.remove(self.src_path)
                return True

            elif self.settings == 'opt4':
                source_attrs, target_attrs = self.get_attrs()
                if source_attrs and source_attrs.st_mtime > target_attrs.st_mtime:
                    os.remove(self.dst_path)
                    return True
                else:
                    raise FileExistsError('opt4')

            elif self.settings == 'opt5':
                remote_attrs, local_attrs = self.get_attrs()
                if remote_attrs and remote_attrs.st_size != local_attrs.st_size:
                    self.sftp.remove(self.full_remote_path)
                    return True
                else:
                    raise FileExistsError('opt5')
        else:
            return True

    def file_exists_behaviour(self):
        if self.settings == 'Overwrite':
            self.data['overwrite'] = True
        elif self.settings == 'Overwrite if size is different':
            try:
                remote_attrs = os.stat(self.src_path).st_size
                local_attrs = get_dir_attrs(self.src_path, self.sftp)
                if remote_attrs.st_size != local_attrs.st_size:
                    self.data['overwrite'] = True
            except Exception as ex:
                ex_log(f'Could not compare file attrs {ex}')

    def overwrite(self):
        logger.info(f'Downloading {self.filename} - Skipped')
        if not self.done:
            self.manager.put_transfer({**self.data, 'overwrite': True}, bar=self.bar)
            self.manager.run()

    def skip(self):
        logger.info(f'Downloading {self.filename} - Skipped')
        self.done = True
        self.bar.set_values(f'Downloading {self.filename} - Skipped')
