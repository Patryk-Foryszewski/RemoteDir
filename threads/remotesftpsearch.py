from threading import Thread
from common import get_dir_attrs, mk_logger, thumb_dir, is_file, info_popup
from os.path import split
from queue import Queue
from kivy.clock import Clock
import re

logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


class RemoteSftpSearch(Thread):
    def __init__(self, manager, sftp, data):
        super().__init__()
        self.manager = manager
        self.sftp = sftp
        self.text = data['text'].lower()
        self.src_path = data['path']
        self.search_list = data['search_list']
        self.thumbnail = data['thumbnail']
        self.remote_dir = data['remote_dir']
        self.files_queue = Queue()
        self.finished = False
        self.add_file_event = None
        self.info_popup, self.info_text = info_popup(f'Sarching for {self.text}')

    def run(self):
        self.add_file_event = Clock.schedule_interval(self.add_file, 0.1)

        try:
            self.sftp.walktree(remotepath=self.src_path,
                               fcallback=self.callback,
                               dcallback=self.callback,
                               ucallback=self.callback)
        finally:
            self.finished = True
            self.manager.thread_queue.put('.')
            self.manager.sftp_queue.put(self.sftp)
            if not self.search_list:
                self.add_file_event.cancel()

    def callback(self, path):
        _path, filename = split(path)
        # print('REMOTE SEARCH', self.text, path,  thumb_dir not in path and self.text in filename.lower())
        if thumb_dir not in path and self.text in filename.lower():
            try:
                attrs = get_dir_attrs(path, self.sftp)
            except Exception as ex:
                ex_log(f'Failed to get attrs {ex}')
            else:
                attrs.thumbnail = self.thumbnail
                if is_file(attrs):
                    attrs.path = path
                else:
                    attrs.path = _path
                self.search_list.append(attrs)
                self.files_queue.put(attrs)

    def add_file(self, _):
        if self.search_list and not self.files_queue.empty():
            attrs = self.files_queue.get()
            self.remote_dir.add_file(attrs=attrs, from_search=True)
        elif self.finished and self.files_queue.empty():
            self.add_file_event.cancel()
            self.info_text.dismiss_me('Search finished')
