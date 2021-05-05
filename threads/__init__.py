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
from threads.removeremote import RemoveRemoteDirectory
from threads.thumbdownload import ThumbDownload
from threads.remotesftpsearch import RemoteSftpSearch
from popups.currenttransfersettings import CurrentTransferSettings

from weakref import WeakValueDictionary
import os
import stat
import queue
from common import posix_path, pure_windows_path, mk_logger, get_config, confirm_popup
from kivy.clock import Clock
from functools import partial
from datetime import datetime

logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


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
        self.delay = 0.01
        self.max_connections = 3
        self.threads = []
        self.time = datetime.now()
        self.locked_paths = set()
        self.progress_box_shown = False
        self.progress_box.manager = self
        self.transfers_event = None
        self.progress_box.set_manager(self)
        self.upload_settings = ''
        self.download_settings = ''
        self.timeshift = 0
        self.upload_settings_popup = None
        self.download_settings_popup = None
        self.transfers_stopped = False
        #for _ in range(self.max_connections):
        #    self.thread_queue.put('.')

    def run(self):

        self.get_transfer_settings()
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

            elif task['type'] == 'remove_remote':
                self.transfers.put({**task})

            elif task['type'] == 'thumbdownload':
                self.transfers.put({**task})

            elif task['type'] == 'search':
                self.transfers.put({**task})
        self.start_transfers()
    
    def existing_files_popup(self, data, bar, thread):
        print('EXISTING FILES POPUP', self.upload_settings_popup, self.download_settings_popup)
        if data['type'] == 'upload':
            if not self.upload_settings_popup:
                self.upload_settings_popup = CurrentTransferSettings(manager=self)
            self.upload_settings_popup.append_transfers_list([data, bar, thread])

        elif data['type'] == 'download':
            if not self.download_settings_popup:
                self.download_settings_popup = CurrentTransferSettings(manager=self)
            self.download_settings_popup.append_transfers_list([data, bar, thread])

    def set_transfer_settings(self, uploads=None, downloads=None):
        if uploads:
            self.upload_settings = uploads
        if downloads:
            self.download_settings = downloads

    def get_transfer_settings(self):
        config = get_config()
        try:
            self.upload_settings = config.get('DEFAULTS', 'upload')
        except Exception:
            self.upload_settings = 'opt1'
        try:
            self.download_settings = config.get('DEFAULTS', 'download')
        except Exception:
            self.download_settings = 'opt1'
        try:
            self.timeshift = int(config.get('DEFAULTS', 'timeshift'))
        except Exception:
            self.timeshift = 0

    def start_transfers(self):
        self.transfers_stopped = False
        for _ in range(self.max_connections):
            self.thread_queue.put('.')
            self.next_transfer()
        #if not self.transfers_event:
        #    self.transfers_event = Clock.schedule_interval(self.next_transfer, self.delay)

    def stop_transfers(self, cause=None):
        cause = cause if cause else ''
        logger.info(f'Thread manager stop. {cause}')
        self.transfers_stopped = True
        while not self.thread_queue.empty():
            self.thread_queue.get()

        #if self.transfers_event:
        #    self.transfers_event.cancel()
        #    self.transfers_event = None

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
            ex_log(f'Connection exception {ex}')
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

    def connection_error(self):
        self.stop_transfers()
        self.reconnect()

    def next_transfer(self, _=None):
        """
        Runs new thread if not too many threads are currently running.
        :param _:
        :return:
        """
        if self.transfers_stopped:
            return
        if not self.transfers.empty():
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
                settings = self.upload_settings if not transfer.get('settings') else transfer.get('settings')
                transfer['settings'] = settings

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
                settings = self.download_settings if not transfer.get('settings') else transfer.get('settings')
                transfer['settings'] = settings
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

            elif transfer['type'] == 'remove_remote':
                thread = RemoveRemoteDirectory(manager=self, sftp=sftp, data=transfer)

            elif transfer['type'] == 'thumbdownload':
                thread = ThumbDownload(manager=self, sftp=sftp, data=transfer)

            elif transfer['type'] == 'search':
                thread = RemoteSftpSearch(manager=self, sftp=sftp, data=transfer)

            if thread:
                self.threads.append(thread)
                thread.start()
            else:
                ex_log(f'Thread None. Transfer type {transfer["type"]}')

        elif self.all_threads_finished():
            self.stop_transfers('All threads finished')
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

    def locked_path(self, dst_path):
        if dst_path in self.locked_paths:
            return True
        else:
            return False

    #def lock_destination(self, destination, instance):
    #    if destination not in self.locked_destinations:
    #
    #        confirm_popup(callback=self.directory_created,
    #                      text=f'You are going to transfer file to destination directory that already exists'
    #                           f'and it is a file.'
    #                           f''
    #                           f'Do you agree to remove file in order to create a directory and transfer '
    #                           f'all files?',
    #                      title='I\'no idea how to explain you that case.',
    #                      _args=[destination, instance]
    #                      )
    #
    #    self.locked_destinations.add(destination)

    def directory_created(self, destination, instance):

        """
        When during upload program try to make a dir but it already exists and it is a file.
        If user agree to delete the file and create a directory restart all file transfers
        to that directory
        """

        for thread in self.threads:
            if isinstance(thread, instance):
                if hasattr(thread, 'waiting_for_directory'):
                    if thread.dst_path == destination:
                        self.put_transfer({**thread.data, 'bar': thread.bar})
                        self.start_transfers()

    def put_transfer(self, data, bar=None):
        self.transfers.put({**data, 'bar': bar})

    def local_walk(self, task):
        src_path = task['src_path']
        dst_path = task['dst_path']
        local_base, dir_to_walk = os.path.split(src_path)

        for root, dirs, files in os.walk(src_path):
            relative_path = root.replace(local_base, '')[1:]
            relative_path = posix_path(dst_path, *relative_path.split('\\'))

            for file in files:
                self.put_transfer({'type': 'upload',
                                   'dir': False,
                                   'src_path': pure_windows_path(root, file),
                                   'dst_path': relative_path,
                                   'thumbnails': task['thumbnails'],
                                   'settings': self.upload_settings})
            if dirs:
                empty_dirs = []
                for _dir in dirs:
                    if not len(os.listdir(pure_windows_path(root, _dir))):
                        empty_dirs.append(_dir)
                if empty_dirs:
                    self.put_transfer({'type': 'upload',
                                       'dir': True,
                                       'dst_path': relative_path,
                                       'name': empty_dirs,
                                       'thumbnails': task['thumbnails'],
                                       'settings': self.upload_settings})

        self.put_transfer({'type': 'upload',
                           'dir': True,
                           'dst_path': dst_path,
                           'name': [dir_to_walk],
                           'thumbnails': task['thumbnails'],
                           'settings': self.upload_settings})

    def uploaded(self, path, attrs):
        Clock.schedule_once(partial(self.originator.add_file, path, attrs), 0.01)

    def is_current_path(self, path):
        return self.originator.is_current_path(path)
