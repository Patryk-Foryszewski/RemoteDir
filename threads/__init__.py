"""
This package contains threads for:
- uploading
- downloading
- remote walk
- opening files
- making dirs on remote destination
"""
from threading import Thread
from threads.open import Open
from threads.download import Download
from threads.upload import Upload
from threads.remotewalk import RemoteWalk
from threads.mkremotedirs import MkRemoteDirs
from weakref import WeakValueDictionary
import os
import stat
import queue
from common_funcs import posix_path, pure_windows_path, confirm_popup, is_local_file, get_dir_attrs
from kivy.clock import Clock
from functools import partial
from datetime import datetime


class SingletonMeta(type):
    """
    The Singleton class can be implemented in different ways in Python. Some
    possible methods include: base class, decorator, metaclass. We will use the
    metaclass because it is best suited for this purpose.
    """

    _instances = WeakValueDictionary()

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance

        return cls._instances[cls]

    @classmethod
    def inst_q(cls):
        return len(cls._instances)


class TransferManager(Thread, metaclass=SingletonMeta):

    def __init__(self, tasks_queue, originator, progress_box):
        super().__init__()
        self.tasks_queue = tasks_queue
        self.transfers = queue.LifoQueue()
        self.sftp_queue = queue.Queue()
        self.thread_queue = queue.Queue()
        self.originator = originator
        self.progress_box = progress_box
        self.delay = 0.1
        self.max_connections = 3
        self.threads = []
        self.time = datetime.now()
        self.locked_paths = []
        self.progress_box_shown = False
        self.progress_box.manager = self
        self.transfers_event = None
        for _ in range(self.max_connections):
            self.thread_queue.put('.')

    def run(self):
        self.start_transfers()
        while not self.tasks_queue.empty():
            task = self.tasks_queue.get()
            if task['type'] == 'upload':
                if stat.S_ISDIR(os.lstat(task['src_path']).st_mode):
                    self.local_walk(task)
                else:
                    self.transfers.put({**task, 'dir': False})

            elif task['type'] == 'download':
                if stat.S_ISDIR(task['attrs'].st_mode):
                    self.transfers.put({**task, 'dir': True})
                else:
                    name = os.path.split(task['src_path'])[1]
                    task['dst_path'] = os.path.join(task['dst_path'], name)
                    self.transfers.put({**task, 'dir': False})

            elif task['type'] == 'open':
                self.transfers.put({**task})

    def start_transfers(self):
        if not hasattr(self, 'transfers_event'):
            self.transfers_event = Clock.schedule_interval(self.next_transfer, self.delay)

    def stop_transfers(self, cause=None):
        self.transfers_event.cancel()
        del self.transfers_event
        print('THREAD MANAGER STOP', cause)

    def reconnect(self, _=None):
        sftp = self.connect()
        if sftp:
            self.sftp_queue.put(sftp)
            self.start_transfers()
        else:
            Clock.schedule_once(self.reconnect, 5)

    def connect(self):
        conn = self.originator.connection
        try:
            sftp = conn.connect()
        except Exception as ex:
            print('FAILED TO CONNECT', ex)
            self.stop_transfers(ex)
            self.reconnect()
            return None
        else:
            return sftp

    def get_sftp(self):
        """
        Gets sftp from queue if not empty and checks if the sftp is alive.
        If no it recursively call get sftp to check next sftp from queue
        or creates new sftp connection.
        :return:
        """
        if not self.sftp_queue.empty():
            sftp = self.sftp_queue.get()
            try:
                sftp._transport.send_ignore()
            except EOFError:
                sftp.close()
                self.get_sftp()
            else:
                return sftp
        else:

            sftp = self.connect()
            if not sftp:
                self.reconnect()
                return None
            return sftp

    def locked_path(self, dst_path):
        if dst_path in self.locked_paths:
            return True
        else:
            return False

    def connection_error(self):
        self.stop_transfers()
        self.reconnect()

    def next_transfer(self, _):
        """
        Runs new thread if not too many threads are currently running.
        :param _:
        :return:
        """

        if not self.thread_queue.empty() and not self.transfers.empty():
            # print('NEXT TRANSFER DT', args, '#', datetime.now() - self.time)
            self.time = datetime.now()
            self.thread_queue.get()
            transfer = self.transfers.get()
            sftp = self.get_sftp()
            thread = None
            if not sftp:
                # put back on the stack to no omit this transfer
                self.transfers.put(transfer)
                return

            if transfer['type'] == 'upload':
                if transfer['dir']:
                    thread = MkRemoteDirs(transfer, manager=self, sftp=sftp)

                else:
                    if not transfer.get('bar'):
                        bar = self.progress_box.mk_bar()
                        self.progress_box.add_bar(bar)
                        if not self.progress_box_shown:
                            self.progress_box.show_bars()
                            self.progress_box_shown = True
                    else:
                        bar = transfer['bar']
                    thread = Upload(transfer, manager=self, bar=bar, sftp=sftp)
            elif transfer['type'] == 'download':
                if transfer['dir']:
                    thread = RemoteWalk(data=transfer, manager=self, sftp=sftp)
                else:
                    if not transfer.get('bar'):
                        bar = self.progress_box.mk_bar()
                        self.progress_box.add_bar(bar)
                        if not self.progress_box_shown:
                            self.progress_box.show_bars()
                            self.progress_box_shown = True
                    else:
                        bar = transfer['bar']
                    thread = Download(data=transfer, manager=self, bar=bar, sftp=sftp)
            elif transfer['type'] == 'open':
                thread = Open(data=transfer, manager=self, sftp=sftp)

            if thread:
                self.threads.append(thread)
                thread.start()
            else:
                print('ERROR THREAD NONE')

        elif self.all_threads_finished():
            self.stop_transfers()
            undone = 0
            for thread in self.threads:
                if isinstance(thread, Upload) or isinstance(thread, Download):
                    if not thread.done:
                        undone += 1
                    if undone > 1:
                        self.progress_box.show_actions()
                        break
            self.progress_box.transfer_stop()

    def all_threads_finished(self):
        return self.transfers.empty() and self.thread_queue.qsize() == self.max_connections

    def end(self):

        if self.transfers.empty() and self.thread_queue.empty():
            self.stop_transfers()

    def directory_created(self, destination, instance):
        """
        When during upload program try to make a dir but it already exists and it is a file.
        If user agree to delete the file and create a directory we must renew all file transfers
        to that directory
        """

        for thread in self.threads:
            if isinstance(thread, instance):
                if hasattr(thread, 'waiting_for_directory'):
                    if thread.dst_path == destination:
                        self.transfers.put({**thread.data, 'bar': thread.bar})
                        self.start_transfers()

    def put_transfer(self, data, bar=None):
        self.transfers.put({**data, 'bar': bar})

    def local_walk(self, task):
        src_path = task['src_path']
        dst_path = task['dst_path']
        local_base, dir_to_walk = os.path.split(src_path)

        self.transfers.put({'type': 'upload', 'dir': True, 'dst_path': dst_path, 'name': [dir_to_walk]})
        for root, dirs, files in os.walk(src_path):
            relative_path = root.replace(local_base, '')[1:]
            relative_path = posix_path(dst_path, *relative_path.split('\\'))
            if dirs:
                self.put_transfer({'type': 'upload',
                                   'dir': True,
                                   'dst_path': relative_path,
                                   'name': dirs})

            for file in files:
                self.put_transfer({'type': 'upload',
                                   'dir': False,
                                   'src_path': pure_windows_path(root, file),
                                   'dst_path': relative_path})

    def uploaded(self, path, attrs):
        Clock.schedule_once(partial(self.originator.add_file, path, attrs), 0.01)

    def is_current_path(self, path):
        return self.originator.is_current_path(path)
