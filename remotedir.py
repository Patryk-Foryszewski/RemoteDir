from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty
from kivy.core.window import Window
from kivy.clock import Clock
from colors import colors
from common import credential_popup, menu_popup, settings_popup, confirm_popup, posix_path, find_thumb, thumbnails
from common import remote_path_exists, get_dir_attrs, mk_logger, download_path, default_remote, thumb_dir, thumbnail_ext
from common import thumb_dir_path, pure_windows_path

from sftp.connection import Connection
from exceptions import *
from threads import TransferManager
import queue
import os
from paramiko.ssh_exception import SSHException, AuthenticationException, BadAuthenticationType
import copy
from functools import partial

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
        self.base_path = None
        self.current_path = ''
        self.marked_files = set()
        self.files_queue = queue.LifoQueue()
        self.paths_history = []
        self.tasks_queue = None
        self.connection = None
        self._y = None
        self.childs_to_light = None
        self.files_space = None
        self.progress_box = None
        self.thumbnails = thumbnails()
        self.reconnection_tries = 0
        self.callback = None
        self.current_history_index = 0

    def on_kv_post(self, base_widget):
        self.childs_to_light = [self.ids.current_path, self.ids.search, self.ids.settings,
                                self.ids.sort_menu, self.ids.sort_files_up, self.ids.sort_files_down,
                                self.ids.file_size]

        self.files_space = self.ids.files_space
        self.progress_box = self.ids.progress_box
        self.base_path = ''
        self.current_path = default_remote()
        self.connect()

    def absolute_path(self, relative_path):
        return posix_path(self.base_path, relative_path)

    def relative_path(self, path):
        return path.lstrip(self.base_path)

    def on_current_path(self, *_):
        if self.current_path:
            self.ids.current_path.text = f'/{self.relative_path(self.current_path)}'
        else:
            self.ids.current_path.text = ''



    def chdir_from_input(self, path):
        path = path.lstrip('/')
        path = path.lstrip('\\')
        self.chdir(posix_path(self.base_path, path))

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

    def compare_thumbs(self):
        """
        Checks if thumbnails are up to date with the one on remote disk.
        If thumb is not up to date or does not exist download thumbnail from remote.
        """
        if not self.thumbnails:
            return
        remote_thumbs_path = posix_path(self.get_current_path(), thumb_dir)
        # noinspection PyBroadException
        try:
            remote_attrs = self.sftp.listdir_attr(remote_thumbs_path)
        except Exception:
            return

        downloads = []
        for file in remote_attrs:
            _file_name = '.'.join(file.filename.split('.')[:-1])
            thumb_path = find_thumb(self.get_current_path(), _file_name)
            if thumb_path:
                local_attrs = os.lstat(thumb_path)
                if file.st_mtime != local_attrs.st_mtime:
                    downloads.append(file.filename)

            else:
                downloads.append(file.filename)

        if downloads:
            src_path = posix_path(self.get_current_path(), thumb_dir)
            task = {'type': 'thumbdownload',
                    'src_path': src_path,
                    'dst_path': self.get_current_path(),
                    'thumbnails': downloads,
                    'callback': self.files_space.refresh_thumbnails}
            self.execute_sftp_task(task)

    def list_dir(self, attrs_list=None):
        # print('DIRS', self.sftp.listdir_attr())
        self.compare_thumbs()
        #popup, content = info_popup(f'Listing {file_name(self.get_current_path())} directory')
        if not attrs_list:
            try:
                attrs_list = self.sftp.listdir_attr()
            except OSError as ose:
                if ose == 'Socket is closed':
                    self.callback = self.list_dir
                    self.connect()
            except Exception as ex:
                #content.text = f'List dir exception {ex}'
                ex_log(f'List dir exception {ex}')
                return
            else:
                #popup.dismiss()
                self.add_attrs(attrs_list)
        self.files_space.fill(attrs_list)

    def add_attrs(self, attrs):
        _path = self.get_current_path()
        for attr in attrs:
            attr.path = _path
            attr.thumbnail = self.thumbnails

    def add_file(self, path=None, attrs=None, _=None, from_search=False):
        if path == self.get_current_path():
            self.add_attrs([attrs])
            self.files_space.add_file(attrs)
        elif from_search:
            self.files_space.add_file(attrs)

    def sort_menu(self):
        buttons = ['Name', 'Date added', 'Date modified', 'Size']
        menu_popup(originator=self,
                   buttons=buttons,
                   callback=self.files_space.sort_files,
                   widget=self.ids.sort_menu,
                   on_popup=self.on_popup,
                   on_popup_dismiss=self.on_popup_dismiss)
        self.on_popup()

    def sort_files(self, reverse=False):
        self.files_space.reverse = reverse
        self.files_space.sort_files()

    def clear_file_space(self):
        self.files_space.clear_widgets()

    def search(self, text):
        search_list = []
        self.clear_file_space()
        task = {'type': 'search',
                'text': text,
                'path': self.get_current_path(),
                'thumbnail': self.thumbnails,
                'remote_dir': self,
                'search_list': search_list}

        self.current_path = ''
        self.execute_sftp_task(task)
        self.add_act_to_history({'action': 'search', 'go_to': search_list, 'text': text})

    def view_menu(self):
        buttons = ['Tiles', 'Details']
        menu_popup(originator=self,
                   buttons=buttons,
                   callback=self.files_space.view_menu,
                   widget=self.ids.view_menu,
                   on_popup=self.on_popup,
                   on_popup_dismiss=self.on_popup_dismiss)
        self.on_popup()

    def make_dir(self, name):

        try:
            self.sftp.mkdir(name)
            attrs = get_dir_attrs(_path=posix_path(self.get_current_path(), name), sftp=self.sftp)
        except Exception as ex:
            ex_log(f'Make dir exception {ex}')
            return False
        else:
            attrs.path = self.get_current_path()
            self.files_space.add_icon(attrs, new_dir=True)

    def file_size(self):
        buttons = ['Huge', 'Medium', 'Small']
        menu_popup(originator=self,
                   buttons=buttons,
                   callback=self.files_space.file_size,
                   widget=self.ids.file_size,
                   on_popup=self.on_popup,
                   on_popup_dismiss=self.on_popup_dismiss
                   )

    def connect(self, popup=None, password=None):
        self.files_space.unbind_external_drop()
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

        except BadAuthenticationType as bat:
            ex_log(f'Authentication exception, {str(bat)}')
            credential_popup(callback=self.connect, errors={'errors': '',
                                                            'message': f'{str(bat)}'})

        except AuthenticationException as ae:
            ex_log(f'Authentication exception, {str(ae)}')
            credential_popup(callback=self.connect, errors={'errors': '',
                                                            'message': f'{str(ae)}'})

        except SSHException as she:
            ex_log(f'Connection exception, {she}')
            if 'not a valid' in str(she):
                credential_popup(callback=self.connect, errors={'errors': ['private_key'],
                                                                'message': f'{str(she)[0].upper()}{str(she)[1:]}'})
            else:
                self.reconnect()

        except FileNotFoundError:
            credential_popup(callback=self.connect, errors={'errors': ['private_key'],
                                                            'message': 'Private key file doesn\'t exist'})

        except Exception as ex:
            ex_log(f'Unknown connection exception, {ex}')

        else:
            self.sftp = self.connection.sftp
            if not self.sftp:
                self.reconnect()
                return False
            self.reconnection_tries = 0
            logger.info('Succesfully connected to server')
            self.chdir(self.current_path)
            self.get_base_path()
            self.do_callback()
            self.files_space.bind_external_drop()
            return True

    def do_callback(self):
        if self.callback:
            self.callback()
            self.callback = None

    def remote_path_exists(self, path):
        return remote_path_exists(path, self.sftp)

    def reconnect(self):
        logger.info('Reconnecting to remote server')

        def con(_):
            self.connect(password=self.password)

        dt = 5 + self.reconnection_tries / 10 * 10
        self.reconnection_tries += 1
        Clock.schedule_once(con,  dt)

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

    def chmod(self, file, mode=None, popup=None):

        if not mode:
            from popups.chmodpopup import ChmodPopup
            ChmodPopup(file=file,
                       on_save=self.chmod,
                       on_popup=self.on_popup,
                       on_dismiss=self.on_popup_dismiss)

        else:
            if file.file_type == 'dir':
                path = file.attrs.path
            else:
                path = posix_path(file.attrs.path, file.filename)

            try:
                self.sftp.chmod(path, mode)
                attrs = get_dir_attrs(path, self.sftp)
            except Exception as ex:
                ex_log(f'Failed to change file mode {ex}')
            else:
                self.add_attrs([attrs])
                file.attrs = attrs
                logger.info('File mode changed successfully')
                popup.dismiss()

    def external_dropfile(self, local_path, destination):
        """
        When file is dropped from Windows.
        Creates upload thread if doesn't exists and adds file path to queue
        """
        destination = self.get_current_path() if not destination else posix_path(self.get_current_path(), destination)
        local_path = local_path.decode(encoding='UTF-8', errors='strict')
        task = {'type': 'upload',
                'src_path': local_path,
                'dst_path': destination,
                'thumbnails': self.thumbnails}

        self.execute_sftp_task(task)

    @staticmethod
    def get_history_action(act):
        return act['action']

    def show_history(self, widget):
        print('HISTORY', self.paths_history)
        prepared = []
        go_to = []
        index_map = {}
        index = 1
        for _index, act in enumerate(self.paths_history):
            action = self.get_history_action(act)
            print('GO TO',act['go_to'], act['go_to'] in go_to )
            if act['go_to'] in go_to:
                continue
            go_to.append(act['go_to'])
            if action == 'search':
                prepared.append(f'{index} Searching for: {act["text"]}')
            elif action == 'listed':
                path = self.relative_path(act["go_to"])
                prepared.append(f'{index} {path if path else "Default path"}')
            print('PREPARED', prepared)
            index_map[index] = _index
            index += 1

        self.history_popup = menu_popup(originator=self,
                                        callback=self.show_history_act,
                                        buttons=prepared,
                                        widget=widget,
                                        forced_size=(widget.width, None),
                                        on_popup=self.on_popup,
                                        on_popup_dismiss=self.on_popup_dismiss)
        self.history_popup.index_map = index_map

    def show_history_act(self, choice):
        h_index = int(choice.split(' ')[0])
        p_index = self.history_popup.index_map[h_index]
        self.current_history_index = p_index
        self.list_dir_from_history(self.paths_history[p_index])

    def add_act_to_history(self, act):
        self.paths_history.append(act)

    def go_back(self):
        if self.current_history_index > 0:
            self.current_history_index -= 1
            self.list_dir_from_history(self.paths_history[self.current_history_index])

    def go_forward(self):
        if self.current_history_index < len(self.paths_history)-1:
            self.current_history_index += 1
            self.list_dir_from_history(self.paths_history[self.current_history_index])

    def list_dir_from_history(self, act):
        print('HISTORY ACT', act)
        action = act['action']
        if action == 'listed':
            self.chdir(act['go_to'], add_to_history=False)
        elif action == 'search':
            self.current_path = ''
            self.list_dir(attrs_list=act['go_to'])

    def get_cwd(self):
        cwd = self.sftp.getcwd()
        return cwd if cwd else ""

    def settings(self):
        self.on_popup()
        menu_popup(widget=self.ids.settings,
                   originator=self,
                   buttons=['Credentials', 'Settings'],
                   callback=self.choice,
                   on_popup=self.on_popup,
                   on_popup_dismiss=self.on_popup_dismiss
                   )

    def choice(self, choice):
        self.on_popup_dismiss()
        if choice == 'Credentials':
            credential_popup(auto_dismiss=True)
        if choice == 'Settings':
            settings_popup()

    def on_popup(self, *_):
        print('ON POPUP')
        self.mouse_locked = True

    def remove_from_view(self, file):
        self.files_space.remove_file(file)

    def remove(self, file):
        cwd = self.sftp.getcwd()
        path = posix_path(cwd if cwd else '.', file.filename)
        if file.file_type == 'dir':
            self.rmdir(path, file)
        else:
            # noinspection PyBroadException
            try:
                self.sftp.remove(path)
            except IOError as ie:
                ex_log(f'Failed to remove file {ie}')
                if ie.errno == 2:
                    if not self.sftp.exists(path):
                        self.remove_from_view(file)
            except Exception as ex:
                ex_log(f'Failed to remove file {ex}')
            else:
                self.remove_from_view(file)

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

    def rename_thumbnail(self, old_path, old_name, new_path, new_name):
        # print('RENAME THUMBNAIL', old_path, old_name, new_path, new_name)
        if self.thumbnails:
            from common import find_thumb
            old_local_thumbnail = find_thumb(old_path, old_name)
            if old_local_thumbnail:
                new_name = f'{new_name}.{thumbnail_ext}'
                old_name = f'{old_name}.{thumbnail_ext}'
                new_thumb_dir_path = thumb_dir_path(new_path)
                # print('NEW THUMB DIR PATH', new_thumb_dir_path)
                new_local_thumbnail = pure_windows_path(new_thumb_dir_path, new_name)
                # print('     OLD LOCAL THUMBNAIL', old_local_thumbnail)
                # print('     NEW LOCAL THUMBNAIL', new_local_thumbnail)
                try:
                    if os.path.exists(new_local_thumbnail):
                        os.remove(new_local_thumbnail)

                    if not os.path.exists(new_thumb_dir_path):
                        os.makedirs(new_thumb_dir_path)
                    os.rename(old_local_thumbnail, new_local_thumbnail)
                except Exception as ex:
                    ex_log('Failed to rename local thumbnail', ex)

                old_remote_thumbnail = posix_path(old_path, thumb_dir, old_name)
                path_to_remote_thumb = posix_path(new_path, thumb_dir)
                new_remote_thumbnail = posix_path(path_to_remote_thumb, new_name)
                # print('     OLD REMOTE THUMBNAIL', old_remote_thumbnail)
                # print('     PATH TO REMOTE THUMB', path_to_remote_thumb)
                # print('     NEW REMOTE THUMBNAIL', new_remote_thumbnail)
                try:
                    path_to_remote_thumb = posix_path(new_path, thumb_dir)
                    if not self.sftp.exists(path_to_remote_thumb):
                        self.sftp.makedirs(path_to_remote_thumb)
                    if self.sftp.exists(new_remote_thumbnail):
                        self.sftp.remove(new_remote_thumbnail)
                    self.sftp.rename(old_remote_thumbnail, new_remote_thumbnail)
                except Exception as ex:
                    ex_log('Failed to rename remote thumbnail', ex)

    def rename_file(self, full_old_path, full_new_path, file):

        old_path, old_name = os.path.split(full_old_path)
        new_path, new_name = os.path.split(full_new_path)
        if not self.sftp.exists(full_new_path):
            try:
                self.sftp.rename(full_old_path, full_new_path)
            except IOError as ie:
                ex_log(f'Failed to rename file {ie}')
                file.filename = old_name
            else:
                logger.info(f'File renamed from {file.filename} to {os.path.split(new_name)[1]}')
                self.files_space.remove_file(file)
                # print('     CHECK IF CURRENT PATH', new_path, '|||', self.current_path, new_path == self.current_path )
                if new_path == self.get_current_path():
                    attrs = self.get_file_attrs(full_new_path)
                    if attrs:
                        self.add_attrs([attrs])
                        file.attrs = copy.deepcopy(attrs)
                        file.filename = attrs.filename
                        self.files_space.add_file(attrs)

            finally:
                self.rename_thumbnail(old_path, old_name, new_path, new_name)
                self.files_space.refresh_thumbnail(new_name)

        else:
            confirm_popup(callback=self.remove_and_rename,
                          movable=True,
                          _args=[new_path, old_name, new_name, file],
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
                self.rename_file(content._args[1], content._args[2], content._args[3])

        else:
            popup.dismiss()

    def rmdir(self, remote_path, file):
        task = {'type': 'remove_remote',
                'remote_path': remote_path,
                'on_remove': partial(self.files_space.remove_file, file),
                'progress_box': self.progress_box}
        self.execute_sftp_task(task)

        # try:
        #     for f in self.sftp.listdir_attr(path):
        #         rpath = posix_path(path, f.filename)
        #         if stat.S_ISDIR(f.st_mode):
        #             self.rmdir(rpath)
        #         else:
        #             rpath = posix_path(path, f.filename)
        #             self.sftp.remove(rpath)
        # except OSError as ose:
        #     if ose == 'Socket is closed':
        #         self.callback = partial(self.rmdir, path)
        #         self.connect()
        #
        # except Exception as ex:
        #     ex_log(f'Failed to remove directory {ex}')
        #     return False
        # else:
        #     logger.info(f'Succesfully removed file {os.path.split(path)[1]}')
        #     self.sftp.rmdir(path)
        #     return True

    def transfer_start(self):
        self.progress_box.transfer_start()

    def transfer_stop(self):
        self.progress_box.transfer_stop()

    def on_popup_dismiss(self, *_):
        self.mouse_locked = False

    def chdir(self, path, add_to_history=True):
        print('CHDIR', path)
        # noinspection PyBroadException
        try:
            self.sftp.chdir(path)
        except IOError as ie:
            ex_log(f'Failed to change dir {ie}')
            if ie.errno == 2:
                self.chdir(self.current_path)
            elif str(ie) == 'Socket is closed':
                self.reconnect()
            elif ie.errno == 13:  # Permission denied
                logger.warning('Could not list directory. Permission denied.')
            return False
        except Exception as ex:
            ex_log(f'Failed to change dir {ex}')
            self.reconnect()
            return False
        else:
            self.list_dir()
            self.current_path = path
            if add_to_history:
                self.add_act_to_history({'action': 'listed', 'go_to': self.get_current_path()})

            return True

    def is_current_path(self, path):
        return path == self.get_current_path()

    def get_current_path(self):
        current = self.sftp.getcwd()
        return current if current else posix_path()

    def uploaded(self, path, attrs):
        pass

    def open_file(self, file):
        full_path = posix_path(file.attrs.path, file.filename)
        if file.file_type == 'dir':
            self.chdir(full_path)
            self.current_history_index += 1
        else:
            src_path = posix_path(full_path)
            task = {'type': 'open', 'src_path': src_path}
            self.execute_sftp_task(task)
