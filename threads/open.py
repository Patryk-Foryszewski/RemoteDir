from threading import Thread
import os
from threads.download import Download
from kivy.clock import Clock
from common import mk_logger, thumbnails, progress_popup

logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


class Open(Thread):
    def __init__(self, data, manager, sftp):
        super().__init__()
        from common_vars import cache_path
        self.cache_path = cache_path
        self.data = data
        self.src_path = data['src_path']
        self.file_name = os.path.split(self.src_path)[1]
        self.dst_path = os.path.join(cache_path, self.file_name)
        self.data['dst_path'] = os.path.join(cache_path, self.file_name)
        self.manager = manager
        self.sftp = sftp
        self.m_time = None
        self.check_event = None
        self.file = None
        self.bar = None
        self.upload_progress = None
        self.thumbnails = thumbnails()

    def run(self):
        logger.info(f'Opening file {self.file_name}')
        if os.path.exists(self.dst_path):
            local_attrs = os.stat(self.dst_path)
            remote_attrs = self.sftp.stat(self.src_path)
            if local_attrs.st_size != remote_attrs.st_size:
                self.download()
            elif local_attrs.st_mtime != remote_attrs.st_mtime:
                self.download()
            else:
                self.open()

        else:
            self.download()

    def download(self):
        self.bar = self.manager.progress_box.mk_bar()
        self.manager.progress_box.add_bar(self.bar)
        os.makedirs(self.cache_path, exist_ok=True)
        self.data.update({'overwrite': True})
        thread = Download(data=self.data,
                          manager=self.manager,
                          bar=self.bar,
                          sftp=self.sftp,
                          preserve_mtime=True)
        self.bar.set_values(f'Opening {self.file_name}')
        thread.start()
        thread.join()
        self.open()

    def open(self):
        self.manager.sftp_queue.put(self.sftp)
        self.manager.thread_queue.put('.')
        self.get_mtime()
        self.check_event = Clock.schedule_interval(self.is_modified, 1)
        self.file = os.system('"{}"'.format(self.dst_path))

    def get_mtime(self):
        self.m_time = os.stat(self.dst_path).st_mtime

    def is_modified(self, _):
        if self.m_time != os.stat(self.dst_path).st_mtime:
            self.get_mtime()
            self.upload()

    def file_closed(self):
        """Function to check if file is closed. If so stop self.check_event"""
        print('FILE CLOSED?', self.file)
        # noinspection PyBroadException
        try:
            os.rename(self.dst_path, self.dst_path)
        except Exception:
            print('     COULD NOT RENAME FILE')
        else:
            print('     FILE RENAMED')

    def upload(self):
        transfer = {'src_path': self.dst_path,
                    'dst_path': os.path.split(self.src_path)[0],
                    'type': 'upload',
                    'dir': False,
                    'overwrite': True,
                    'thumbnails': self.thumbnails,
                    'preserve_mtime': True}

        self.upload_progress = self.bar.progress
        self.bar.progress_callback = self.on_upload_progress
        self.popup, self.bar_popup = progress_popup()
        self.bar_popup.set_values(f'Uploading {self.file_name} to {os.path.split(self.dst_path)[1]}')
        self.manager.put_transfer(transfer, bar=self.bar)
        self.manager.run()

    def on_upload_progress(self, progress):
        self.bar_popup.update(*progress)
        if progress[0]/progress[1] == 1:
            def dismiss_progress_popup(_):
                self.popup.dismiss()
            Clock.schedule_once(dismiss_progress_popup, 1)
