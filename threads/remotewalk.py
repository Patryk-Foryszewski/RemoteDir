from threading import Thread
import os
import stat
from common_funcs import confirm_popup, mk_logger
from threads.download import Download

logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


class RemoteWalk(Thread):
    def __init__(self, data, manager,  sftp):
        super().__init__()
        self.transfer = data
        self.src_path = data['src_path']
        self.dst_path = data['dst_path']
        self.dir_name = os.path.split(data['src_path'])[1]
        self.manager = manager
        self.sftp = sftp

    def run(self):
        try:
            self.sftp.walktree(remotepath=self.src_path,
                               fcallback=self.fcallback,
                               dcallback=self.dcallback,
                               ucallback=self.fcallback)
        finally:
            self.manager.thread_queue.put('.')
            self.manager.sftp_queue.put(self.sftp)

    def fcallback(self, file_path):
        dst = file_path[len(self.src_path):].split('/')
        path = os.path.join(self.dst_path, self.dir_name, *dst)
        relative_path = os.path.normpath(path)

        task = {'type': 'download',
                'dir': False,
                'src_path': file_path,
                'dst_path': relative_path}
        self.manager.put_transfer(task)

    def dcallback(self, dir_path):
        relative_path = os.path.normpath(os.path.join(self.dst_path,
                                                      self.dir_name,
                                                      *dir_path[len(self.src_path):].split('/')))
        if not os.path.exists(relative_path):
            os.makedirs(relative_path, exist_ok=True)
        elif stat.S_ISREG(os.stat(relative_path).st_mode):
            confirm_popup(callback=self.delete_file,
                          movable=True,
                          _args=relative_path,
                          text=f'Path {relative_path} already exists on remote server but it is a file\n'
                               f'To be able to upload data to that destination it must be removed\n\n'

                               f'Do you agree to delete the file and create directory?')

    def delete_file(self, popup, content, answer):
        if answer == 'yes':
            try:
                os.remove(content._args)
            except Exception as ex:
                content.text = f'Could not remove file.\n{ex}'
                popup.auto_dimiss = True
                ex_log(f'Failed to remove file')

            else:
                popup.dismiss()
                os.makedirs(content._args, exist_ok=True)
                self.manager.directory_created(content._args, Download)
        else:
            popup.dismiss()
