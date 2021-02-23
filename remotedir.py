from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty
from kivy.core.window import Window
from kivy.clock import Clock
from colors import colors
from common_funcs import credential_popup, menu_popup, settings_popup, confirm_popup, posix_path
from common_funcs import remote_path_exists, get_dir_attrs, mk_logger
from common_vars import download_path, default_remote
from configparser import ConfigParser
from filesspace import FilesSpace
from progressbox import ProgressBox
from sftp.connection import Connection
from exceptions import *
from threads import TransferManager
import stat
import queue
import os
from paramiko.ssh_exception import SSHException
import copy

logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


class RemoteDir(BoxLayout):
    bcolor = ListProperty()
    current_path = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_move)
        Window.bind(focus=self.window_focus)
        self.mouse_locked = False
        self.password = None
        self.sftp = None
        self.connect()
        self.current_path = default_remote()
        self.marked_files = set()
        self.files_queue = queue.LifoQueue()
        self.paths_history = []
        self.tasks_queue = None
        self.base_path = None
        self.connect_event = None
        self.connection = None
        self._y = None
        self.childs_to_light = None
        self.files_space = None
        self.progress_box = None

    def on_kv_post(self, base_widget):
        self.childs_to_light = [self.ids.current_path, self.ids.search, self.ids.settings,
                                self.ids.sort_menu, self.ids.sort_files_up, self.ids.sort_files_down,
                                self.ids.file_size]

        self.files_space = self.ids.files_space
        self.progress_box = self.ids.progress_box

    def on_mouse_move(self, _, mouse_pos):
        if not self.mouse_locked:

            for child in self.childs_to_light:
                if child.focus:
                    child.background_color = child.focused_color

                elif child.collide_point(*child.to_widget(*mouse_pos)):
                    child.background_color = child.active_color

                else:
                    child.background_color = child.unactive_color

    def on_touch_down(self, touch):
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        return super().on_touch_up(touch)

    def on_touch_move(self, touch):
        # moves file_space up or down depends to touch_move position
        self._y = self.ids.space_scroller.vbar[0] * self.ids.files_space.height + touch.y
        if touch.y / self.ids.space_scroller.height > 0.9 and self.ids.space_scroller.scroll_y < 1:
            self.ids.space_scroller.scroll_y += 0.1

        elif touch.y / self.ids.space_scroller.height < 0.1 and self.ids.space_scroller.scroll_y > 0:
            self.ids.space_scroller.scroll_y -= 0.1

        return super().on_touch_move(touch)

    def list_dir(self):
        # print('DIRS', self.sftp.listdir_attr())
        try:
            attrs_list = self.sftp.listdir_attr()
        except Exception as ex:
            ex_log(f'List dir exception {ex}')
        else:
            self.files_space.fill(attrs_list)

    def add_file(self, path, attrs, _):
        if path == self.get_current_path():
            self.files_space.add_file(attrs)

    def sort_menu(self):
        buttons = ['Name', 'Date added', 'Date modified', 'Size']
        menu_popup(originator=self,
                   buttons=buttons,
                   callback=self.files_space.sort_files,
                   widget=self.ids.sort_menu)
        self.on_popup()

    def sort_files(self, reverse=False):
        self.files_space.reverse = reverse
        self.files_space.sort_files()

    def view_menu(self):
        buttons = ['Tiles', 'Details']
        menu_popup(originator=self,
                   buttons=buttons,
                   callback=self.files_space.view_menu,
                   widget=self.ids.view_menu)
        self.on_popup()

    def make_dir(self, name):

        try:
            self.sftp.mkdir(name)
            attrs = get_dir_attrs(path=posix_path(self.get_current_path(), name), sftp=self.sftp)
        except Exception as ex:
            ex_log(f'Make dir exception {ex}')
            return False
        else:
            self.files_space.add_icon(attrs, new_dir=True)

    def file_size(self):
        buttons = ['Huge', 'Medium', 'Small']
        menu_popup(originator=self,
                   buttons=buttons,
                   callback=self.files_space.file_size,
                   widget=self.ids.file_size)

    def connect(self, popup=None, password=None):
        if popup:
            popup.dismiss()

        if password:
            self.password = password

        self.connection = Connection(self.password)
        try:
            self.connection.start()
        except ConfigNotFound:
            ex_log('Config not found')
            credential_popup(callback=self.connect)
            return False
        except InvalidConfig as ic:
            credential_popup(callback=self.connect, errors=ic.errors)
            return False
        except HosKeyNotFound as nf:
            logger.info('Host key not found')
            self.connection.hostkeys.connect = self.connect
            self.connection.hostkeys.hostkey_popup(nf.message)
            return False
        except HostkeyMatchError as me:
            ex_log(f'Hostkey\'s match error {me.message}')
            self.connection.hostkeys.connect = self.connect
            self.connection.hostkeys.hostkey_popup(me.message)
            return False
        except SSHException as she:
            ex_log(f'Connection exception, {she}')
            self.reconnect()
        except Exception as ex:
            ex_log(f'Unknown connection exception, {ex}')
        else:
            logger.info('Succesfully connected to server')
            self.sftp = self.connection.sftp
            self.chdir(self.current_path)
            self.get_base_path()
            if self.connect_event is not None:
                self.connect_event.cancel()
                self.connect_event = None
            return True

    def remote_path_exists(self, path):
        return remote_path_exists(path, self.sftp)

    def reconnect(self):
        def con(_):
            self.connect(password=self.password)

        self.connect_event = Clock.schedule_once(con,  5)

    def get_base_path(self):
        """Creates string holding the path user login to."""

        if not self.base_path:
            self.base_path = self.get_current_path()

    def window_focus(self, *args):
        if not args[1]:
            self.bcolor = colors['unactive_window_color']
        else:
            self.bcolor = colors['active_window_color']

    def execute_sftp_task(self, task):
        if not hasattr(self, 'transfer_manager'):
            self.tasks_queue = queue.Queue()
            self.transfer_manager = TransferManager(tasks_queue=self.tasks_queue,
                                                    originator=self,
                                                    progress_box=self.progress_box)
            self.tasks_queue.put(task)
            self.transfer_manager.start()
        else:
            self.transfer_manager.tasks_queue.put(task)
            self.transfer_manager.run()

    def download(self, file):
        src_path = posix_path(self.get_current_path(), file.filename)
        task = {'type': 'download', 'src_path': src_path, 'dst_path': download_path(), 'attrs': file.attrs}
        self.execute_sftp_task(task)

    def external_dropfile(self, local_path, destination):
        """
        When file is dropped from Windows.
        Creates upload thread if doesn't exists and adds file path to queue
        """
        destination = self.get_current_path() if not destination else posix_path(self.get_current_path(), destination)
        local_path = local_path.decode(encoding='UTF-8', errors='strict')
        task = {'type': 'upload', 'src_path': local_path, 'dst_path': destination}

        self.execute_sftp_task(task)

    def go_back(self):
        index = self.paths_history.index(self.get_current_path())
        if index > 0:
            self.chdir(self.paths_history[index-1])

    def go_forward(self):
        index = self.paths_history.index(self.get_current_path())
        if index < len(self.paths_history)-1:
            self.chdir(self.paths_history[index+1])

    def get_cwd(self):
        cwd = self.sftp.getcwd()
        return cwd if cwd else ""

    def settings(self):
        self.on_popup()
        menu_popup(widget=self.ids.settings,
                   originator=self,
                   buttons=['Credentials', 'Settings'],
                   callback=self.choice)

    def choice(self, choice):
        self.on_popup_dismiss()
        if choice == 'Credentials':
            credential_popup()
        if choice == 'Settings':
            settings_popup()

    def on_popup(self):
        self.mouse_locked = True

    def remove_from_view(self, file):
        self.files_space.remove_file(file)

    def remove(self, file):
        cwd = self.sftp.getcwd()
        path = posix_path(cwd if cwd else '.', file.filename)
        if file.file_type == 'dir':
            if self.rmdir(path):
                return True
        else:
            # noinspection PyBroadException
            try:
                self.sftp.remove(path)
            except IOError as ie:
                ex_log(f'Failed to remove file {ie}')
                if ie.errno == 2:
                    if not self.sftp.exists(path):
                        self.files_space.remove_file(file)

                return False
            except Exception as ex:
                ex_log(f'Failed to remove file {ex}')
                return False
            else:
                self.remove_from_view(file)
                return True

    def get_file_attrs(self, path):
        # noinspection PyBroadException
        try:
            attrs = self.sftp.lstat(path)
            attrs.filename = os.path.split(path)[1]
            attrs.longname = str(attrs)
        except Exception as ex:
            ex_log(f'Failed to get file attrs {ex}')
            return None
        else:
            return attrs

    def rename_file(self, old, new, file, drop=False):

        old_path = posix_path(self.get_current_path(), old)
        new_path = posix_path(self.get_current_path(), new)
        if not self.sftp.exists(new_path):
            try:
                self.sftp.rename(old_path, new_path)
            except IOError as ie:
                ex_log(f'Failed to rename file {ie}')
                file.filename = old
            else:
                logger.info(f'File renamed from {file.filename} to {os.path.split(new)[1]}')
                if drop:
                    self.files_space.remove_file(file)
                else:
                    attrs = self.get_file_attrs(new_path)
                    if attrs:
                        file.attrs = copy.deepcopy(attrs)
                        file.filename = attrs.filename
        else:
            confirm_popup(callback=self.remove_and_rename,
                          movable=True,
                          _args=[new_path, old, new, file, drop],
                          text='File already exists in destination directory.\n\n'
                               'Click "Yes" if you wish to remove existing file and move'
                          )

    def remove_and_rename(self, popup, content, answer):
        """
        If user tries to rename file to name that already exists in current directory
        this method gives ability to remove existing file and rename file.

        :param popup:
        :param content:
        :param answer:
        :return:
        """
        if answer == 'yes':
            try:
                self.sftp.remove(content._args[0])
            except Exception as ex:
                content.text = 'Could not remove file. Try again later'
                ex_log(f'Failed to remove and rename file {ex}')
            else:
                popup.dismiss()
                self.rename_file(content._args[1], content._args[2], content._args[3], content._args[4])
        else:
            popup.dismiss()

    def rmdir(self, path):
        # noinspection PyBroadException
        try:
            for f in self.sftp.listdir_attr(path):
                rpath = posix_path(path, f.filename)
                if stat.S_ISDIR(f.st_mode):
                    self.rmdir(rpath)
                else:
                    rpath = posix_path(path, f.filename)
                    self.sftp.remove(rpath)
        except Exception as ex:
            ex_log(f'Failed to remove directory {ex}')
            return False
        else:
            logger.info(f'Succesfully removed file {os.path.split(path)[1]}')
            self.sftp.rmdir(path)
            return True

    def transfer_start(self):
        self.progress_box.transfer_start()

    def transfer_stop(self):
        self.progress_box.transfer_stop()

    def on_popup_dismiss(self):
        self.mouse_locked = False

    def chdir(self, path):
        # noinspection PyBroadException
        try:
            self.sftp.chdir(path)
        except IOError as ie:
            ex_log(f'Failed to change dir {ie}')
            if ie.errno == 2:
                self.chdir(self.current_path)
        except Exception as ex:
            ex_log(f'Failed to change dir {ex}')
            self.reconnect()
            return False
        else:
            self.list_dir()
            self.current_path = path
            self.paths_history.append(self.get_current_path())
            return True

    def is_current_path(self, path):
        return path == self.get_current_path()

    def get_current_path(self):
        current = self.sftp.getcwd()
        return current if current else posix_path()

    def uploaded(self, path, attrs):
        pass

    def open_file(self, file):
        if file.file_type == 'dir':
            path = posix_path(self.get_current_path(), file.filename)
            self.chdir(path)
        else:
            src_path = posix_path(self.get_current_path(), file.filename)
            task = {'type': 'open', 'src_path': src_path}
            self.execute_sftp_task(task)
