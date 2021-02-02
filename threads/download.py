from threading import Thread
from common_funcs import is_local_file
from paramiko.ssh_exception import SSHException
import os


class Download(Thread):
    def __init__(self, data, manager, sftp, bar, preserve_mtime=False):
        super().__init__()
        print('DOWNLOAD', data)
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

    def run(self):
        # print('RUN DOWNLOAD', self.src_path, '#', self.dst_path )
        # self.dst_path = 'C:/Users\Patryk\Desktop\download'
        self.bar.my_thread = self
        self.bar.set_values(f'Downloading {self.filename}')
        if self.data.get('overwrite') or not self.exists():
            try:
                self.sftp.get(self.src_path, self.dst_path, callback=self.bar.update, preserve_mtime=self.preserve_mtime)

            except SSHException as she:
                print('DOWNLOAD EX', type(she), she)
                if 'Server connection dropped' in str(she):
                    print('     CONNECTION DROPPED')
                    self.manager.connection_error()
                    self.bar.hide_actions()
                    # in case the transfer has interrupted because of connection issue overwrite it in next attempt
                    self.manager.put_transfer({**self.data, 'overwrite': True}, bar=self.bar)
            except OSError as ex:
                print('UNKNOWN DOWNLOAD ERROR', type(ex), ex)
                # if 'Socket is closed' in str(ex):
                #    self.manager.connection_error()
                #    self.bar.hide_actions()
                #    # in case the transfer has interrupted because of connection issue overwrite it in next attempt
                #    self.manager.put_transfer({**self.data, 'overwrite': True}, bar=self.bar)
            else:
                self.bar.done()
                self.done = True

        self.manager.thread_queue.put('.')
        self.manager.sftp_queue.put(self.sftp)

    def exists(self):
        if is_local_file(self.dirpath):
            self.waiting_for_directory = True
            self.bar.set_values('Waiting for directory')
            return True
        elif os.path.exists(self.dst_path):
            self.bar.file_exists_error()
            return True
        else:
            return False

    def do_not_ovewrite(self):
        self.done = True

    def overwrite(self):
        if not self.done:
            self.manager.put_transfer({**self.data, 'overwrite': True}, bar=self.bar)
            self.manager.run()

    def skip(self):
        self.done = True
        self.bar.set_values(f'Downloading {self.filename} - Skipped')
