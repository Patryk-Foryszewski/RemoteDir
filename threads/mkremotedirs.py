from threading import Thread
from common_funcs import posix_path, confirm_popup, get_dir_attrs
from threads.upload import Upload


class MkRemoteDirs(Thread):
    def __init__(self, data, manager, sftp):
        super().__init__()
        self.data = data
        self.dst_path = data['dst_path']
        # self.full_path = posix_path(self.dst_path, data['name'])
        self.manager = manager
        self.sftp = sftp
        self.done = None

    def run(self):
        self.makedirs()

    def delete_file(self, popup, content, answer):
        print('DELETE FILE', answer)
        if answer == 'yes':
            self.sftp = self.manager.get_sftp()

            if self.sftp:
                path = content._args
                print('     PATH', path)
                # noinspection PyBroadException
                try:
                    self.sftp.remove(path)
                    self.sftp.makedirs(path)
                    attrs = get_dir_attrs(path, self.sftp)
                except Exception:
                    print('COULD NOT MAKE SFTP DIRECTORY')
                else:
                    self.manager.sftp_queue.put(self.sftp)
                    self.manager.uploaded(self.dst_path, attrs)
                    self.manager.directory_created(path, Upload)

        popup.dismiss()

    def makedirs(self):
        for _dir in self.data['name']:
            full_path = posix_path(self.dst_path, _dir)
            try:
                self.sftp.makedirs(full_path)
                attrs = get_dir_attrs(full_path, self.sftp)
            except OSError:
                print(f'PATH {full_path} IS A REGULAR FILE')
                self.manager.locked_paths.append(full_path)
                confirm_popup(callback=self.delete_file,
                              movable=True,
                              _args=full_path,
                              text=f'Path {full_path} already exists on remote server but it is a file\n'
                                   f'To be able to upload data to that destination it must be removed\n\n'

                                   f'Do you agree to delete the file and create directory?')

            else:
                self.done = True
                if self.manager.is_current_path(self.dst_path):
                    self.manager.uploaded(self.dst_path, attrs)

        else:
            self.manager.sftp_queue.put(self.sftp)
            self.manager.thread_queue.put('.')
            self.manager.next_transfer()
