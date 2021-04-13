from threading import Thread
from common import posix_path, mk_logger, thumb_dir, get_dir_attrs
from processes.thumbnail import ThumbnailGenerator
import os
from paramiko.ssh_exception import SSHException


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
        self.thumbnails = data['thumbnails']
        self.settings = data['settings']

    def run(self):
        self.bar.my_thread = self
        logger.info(f'Uploading file - {self.file_name}')
        self.bar.set_values(f'Uploading {self.src_path} to {self.dst_path}')

        try:
            if not self.sftp.exists(self.dst_path):
                self.sftp.makedirs(self.dst_path)

            if self.prepared_to_put():
                self.put(self.src_path, self.full_remote_path, self.preserve_mtime)

        except FileNotFoundError:
            ex_log(f'File {self.file_name} does\'t exists')
            self.bar.set_values(desc=f'File {self.file_name} does\'t exists')

        except FileExistsError as fe:
            print('FILE EXISTS ERROR', self.data)
            fe = str(fe)
            if fe == 'opt1':
                text = f'File {self.full_remote_path} already exists'
                logger.info(text)
                self.bar.file_exists_error(text=text)
                self.manager.existing_files_popup(data=self.data, bar=self.bar, thread=self)

            elif fe == 'opt2':
                self.skip()
                text = f'File {self.full_remote_path} already exists. Skipped.'
                logger.info(text)

            elif fe == 'opt4':
                self.skip()
                text = f'File {self.full_remote_path} already exists. Skipped, not newer'
                logger.info(text)

            elif fe == 'opt5':
                self.skip()
                text = f'File {self.full_remote_path} already exists. Skipped, size not different'
                logger.info(text)

        except IOError as io:
            io = str(io)
            if 'Socket is closed' in io:
                self.manager.connection_error()
                self.manager.put_transfer({**self.data, 'overwrite': True}, bar=self.bar)
                ex_log(f'Uploading {self.file_name} exception. {io}')
            elif 'size mismatch in put' in io:
                text = f'Uploading {self.file_name} exception. {io}. Remote disc is probably full'
                ex_log(text)
                self.bar.set_values(text)
            else:
                text = f'Uploading {self.file_name} exception. {io}'
                ex_log(text)
                self.bar.set_values(text)

        except EOFError as eer:
            ex_log(f'Uploading {self.file_name} exception. {eer}')
            self.manager.put_transfer({**self.data, 'overwrite': True}, bar=self.bar)

        except Exception as ex:
            ex_log(f'Uploading {self.file_name} unknown excetpion. {type(ex)}. {ex}')

        else:
            logger.info(f'Uploading {self.file_name} completed successfully')
            self.done = True
            self.upload_thumbnail()
            self.manager.uploaded(self.dst_path, self.attrs)
            self.bar.done()
        finally:
            self.manager.sftp_queue.put(self.sftp)
            self.manager.thread_queue.put('.')
            self.manager.next_transfer()

    def upload_thumbnail(self):
        if self.thumbnails:
            try:
                th = ThumbnailGenerator(self.src_path, self.dst_path)
                th.start()
                th.join()
                if th.ok:
                    self.bar.flush()
                    self.bar.set_values(f'Uploading thumbnail of {self.file_name}')

                    if self.thumb_dir_exists():
                        self.put(th.thumb_path, posix_path(self.dst_path, thumb_dir, th.thumb_name), True)
                    else:
                        logger.info(f'Thumbnail for {self.file_name} not uploaded')
            except Exception as ex:
                ex_log(f'Failed to upload thumbnail for {self.file_name}. {ex}')

    def get_attrs(self):
        try:
            target_attrs = get_dir_attrs(self.full_remote_path, self.sftp)
            source_attrs = os.lstat(self.src_path)
        except Exception as ex:
            ex_log(f'Could not compare file attrs {ex}')
            return None, None
        else:
            self.data['source_attrs'] = source_attrs
            self.data['target_attrs'] = target_attrs
            return source_attrs, target_attrs

    def prepared_to_put(self):
        if self.sftp.exists(self.full_remote_path):
            print('PREPARE TO PUT', self.settings, self.data.get('overwrite'))

            if self.data.get('overwrite'):
                self.sftp.remove(self.full_remote_path)
                return True

            elif self.settings == 'opt1':
                self.get_attrs()
                raise FileExistsError('opt1')

            elif self.settings == 'opt2':
                self.get_attrs()
                raise FileExistsError('opt2')

            elif self.settings == 'opt3':
                print('REMOVE', self.full_remote_path)
                self.sftp.remove(self.full_remote_path)
                return True

            elif self.settings == 'opt4':
                remote_attrs, local_attrs = self.get_attrs()
                if remote_attrs and local_attrs.st_mtime > remote_attrs.st_mtime:
                    self.sftp.remove(self.full_remote_path)
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

    def put(self, localpath, remotepath, preserve_mtime):
        self.attrs = self.sftp.put(localpath=localpath,
                                   remotepath=remotepath,
                                   callback=self.bar.update,
                                   preserve_mtime=preserve_mtime)
        # in case when empty file is uploaded 'put' does not call callback
        if self.attrs.st_size == 0:
            self.bar.update(1, 1)
        self.attrs.filename = self.file_name
        self.attrs.longname = str(self.attrs)

    def thumb_dir_exists(self):
        thdr = None
        try:
            thdr = posix_path(self.dst_path, thumb_dir)
            if not self.sftp.exists(thdr):
                self.sftp.makedirs(thdr)
        except Exception as ex:
            ex_log(f'Failed to make thumbnail directory {thdr}, {ex}')
            return False
        else:
            return True

    def overwrite(self):
        if not self.done:
            self.manager.put_transfer({**self.data, 'overwrite': True}, bar=self.bar)
            self.manager.run()

    def skip(self):
        print('SKIP')
        self.done = True
        self.bar.set_values(f'Uploading {self.src_path} to {self.dst_path} - Skipped')
