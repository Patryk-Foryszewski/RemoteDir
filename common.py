import logging
import stat
import binascii
import winreg
import pathlib
from hurry.filesize import size
from datetime import datetime
from os import path, environ, makedirs, listdir
from os import stat as os_stat
import sys


def app_name():
    """Returns app name as dir name"""
    import sys
    return path.splitext(path.split(sys.argv[0])[1])[0]


version = '1.0.17'
app_name = app_name()
root_path = path.join(environ['LOCALAPPDATA'], 'RemoteDir')
data_path = path.join(root_path, app_name)
cache_path = path.join(data_path, 'Cache')
config_file = path.join(data_path, 'config.ini')
log_dir = path.join(data_path, 'Log')
my_knownhosts = path.join(data_path, 'known_hosts')
thumb_dir = '.rdthumbnails'
button_height = 20
hidden_files = [thumb_dir]
forbidden_names = [thumb_dir]
img_extensions = ('.jpg', 'jpeg', '.png')
thumbnail_ext = 'jpg'
home_page = 'https://remotedir.eu'
version_file_url = f'{home_page}/version.json'
exe_file_url = f'{home_page}/RemoteDir.exe'
setup_file_url = f'{home_page}/Setup.exe'


def mk_logger(name, level=logging.DEBUG, _format='[%(levelname)-7s] [%(asctime)s] [%(message)s]'):
    """
    Makes logger with given params.

    :param name: (str) Name of class the logger is made for.
    :param level: (int) Level of logging. Defaults to DEBUG
    :param _format: (str)
    :return: logger with two handlers, StreamHanlder and log_file.
    """
    # Create a custom logger

    logger = logging.getLogger(name)
    # prevents log messages from being sent to the root logger
    logger.propagate = 0

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(log_file)
    c_handler.setLevel(logging.DEBUG)
    f_handler.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    c_format = logging.Formatter(_format)
    f_format = logging.Formatter(_format)
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    logger.setLevel(level)

    return logger


def tell_me_about(_object, text=''):
    """
    Prints details like variables and methods of given object. Used only for develop.

    :param text: Text will be printed to allow to distinguish between objects details.
    :param _object: Instance you need to know details
    """

    object_methods = []
    print("HERE IS WHAT I FOUND ABOUT", text)

    try:
        print('* Name', _object.__name__)
    except Exception as ex:
        print('#', ex)

    for method_name in dir(_object):
        try:
            if callable(getattr(_object, method_name)):
                object_methods.append(method_name)
        except Exception as ex:
            print('# Method Error', ex)
    print('* METHODS', object_methods)

    try:
        print('* DICT', _object.__dict__)
    except Exception as ex:
        print('#', ex)

    try:
        print('* VARS   ', vars(_object))
    except Exception as ex:
        print('#', ex)
    print('******')


def clipboard_checker(*_):
    """
    Gives information about current clipboard content.
    :param _: No params needed.
    """

    import win32clipboard as clipboard
    clipboard.OpenClipboard()
    clip_formats = {'CF_TEXT': 1, 'CF_BITMAP': 2, 'CF_METAFILEPICT': 3, 'CF_SYLK': 4, 'CF_DIF': 5, 'CF_TIFF': 6,
                    'CF_OEMTEXT': 7, 'CF_DIB': 8, 'CF_PALETTE': 9, 'CF_PENDATA': 10, 'CF_RIFF': 11, 'CF_WAVE': 12,
                    'CF_UNICODETEXT': 13, 'CF_ENHMETAFILE': 14, 'CF_HDROP': 15, 'CF_LOCALE': 16, 'CF_DIBV5': 17,
                    'CF_MAX': 18, 'CF_OWNERDISPLAY': 128, 'CF_DSPTEXT': 129, 'CF_DSPBITMAP': 130,
                    'CF_DSPMETAFILEPICT': 131, 'CF_DSPENHMETAFILE': 142, }
    print('GET CLIP')
    for _format in clip_formats.items():
        if clipboard.IsClipboardFormatAvailable(_format[1]):
            print(_format[0], clipboard.GetClipboardData(_format[1]))

    # clipboard.EmptyClipboard()
    clipboard.CloseClipboard()


def int_validation(to_validate):
    """
    Checks if given argument is type(int)
    :param to_validate: Argument to check
    :return: List of
    """

    try:
        validated = int(to_validate)
    except Exception as ex:
        return [False, ex]
    else:
        return [True, validated]


def fingerprint(key):
    """Returns fingerprint of a given key

    :param key
    """
    # noinspection PyBroadException
    try:
        converted = binascii.hexlify(key.get_fingerprint())
    except Exception:
        return 'Failed to return fingerprint'
    else:
        return converted


def get_config():
    from configparser import ConfigParser
    from exceptions import ConfigNotFound

    config = ConfigParser()

    if not path.exists(config_file):
        raise ConfigNotFound
    elif not path.exists(data_path):
        makedirs(data_path)
        raise ConfigNotFound
    else:
        config.read(config_file)
        return config


def credential_popup(title='Credentials',
                     errors=None,
                     auto_dismiss=False,
                     on_popup=None,
                     on_popup_dismiss=None):
    from kivy.uix.popup import Popup
    from settings.credentials import Credentials
    from kivy.clock import Clock
    content = Credentials(errors=errors, auto_dismiss=auto_dismiss)

    def open_popup(_):

        popup = Popup(title=title,
                      content=content,
                      size_hint=(None, .8),
                      width=600,
                      auto_dismiss=auto_dismiss)
        popup.bind(on_dismiss=on_popup_dismiss)
        content.popup = popup
        popup.open()
        on_popup()

    Clock.schedule_once(open_popup, .1)


def confirm_popup(callback, text, title='Answer', movable=False, _args=None):
    from popups.mypopup import MyPopup
    from popups.confirmpopup import ConfirmPopup
    from kivy.clock import Clock
    from functools import partial

    def open_popup(_):
        content = ConfirmPopup(text=text)
        content._args = _args
        popup = MyPopup(title=title,
                        content=content,
                        size_hint=(0.7, 0.7),
                        movable=movable)

        content.bind(on_answer=partial(callback, popup))
        popup.open()
    Clock.schedule_once(open_popup, .1)


def menu_popup(originator,
               buttons,
               callback,
               widget=None,
               mouse_pos=None,
               forced_size=None,
               on_popup=None,
               on_popup_dismiss=None):
    from popups.menupopup import MenuPopup
    from kivy.clock import Clock

    popup = MenuPopup(
        buttons=buttons,
        originator=originator,
        callback=callback,
        auto_dismiss=True,
        size_hint=(None, None),
        widget=widget,
        mouse_pos=mouse_pos,
        forced_size=forced_size
    )
    popup.bind(on_dismiss=on_popup_dismiss)

    def open_popup(_):
        popup.open()
        on_popup()

    Clock.schedule_once(open_popup, .1)
    return popup


def thumbnail_popup(originator, destination, _filename, sftp, on_popup, on_popup_dismiss):
    from kivy.uix.popup import Popup
    from popups.thumbnailpopup import ThumbnailPopup
    from kivy.clock import Clock

    def open_popup(_):
        content = ThumbnailPopup(originator, destination, _filename, sftp)
        popup = Popup(
            title=f'Drop thumbnail for {_filename}',
            auto_dismiss=True,
            content=content,
            size_hint=(0.7, 0.7))
        content.popup = popup
        popup.bind(on_dismiss=on_popup_dismiss)
        on_popup()
        popup.open()

    Clock.schedule_once(open_popup, .1)


def progress_popup():
    from kivy.clock import Clock
    from kivy.uix.modalview import ModalView
    from progressrow import ProgressRow
    content = ProgressRow()
    popup = ModalView(
        size_hint=(.5, None),
        height=36,
        pos_hint={'y': .02, 'x': .5}
    )
    popup.add_widget(content)

    def open_popup(_):
        popup.open()

    Clock.schedule_once(open_popup, 0.1)
    return popup, content


def info_popup(text=''):
    from kivy.clock import Clock
    from infolabel import InfoLabel
    from kivy.uix.modalview import ModalView

    content = InfoLabel(text)
    popup = ModalView(
        size_hint=(None, None),
        background_color=(0, 0, 0, 0),
        pos_hint={'y': .02, 'right': .98},
        auto_dismiss=False
    )
    content.popup = popup

    def open_popup(_):
        popup.open()
        popup.size = content.size
        popup.add_widget(content)
    Clock.schedule_once(open_popup, 0)
    return popup, content


def get_progid(_filename):
    # noinspection PyBroadException
    try:
        ext = path.splitext(_filename)[1]
        partial_key = r'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\{}\UserChoice'.format(ext)
        with winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER) as reg:
            with winreg.OpenKey(reg, partial_key) as key_object:
                value, _type = winreg.QueryValueEx(key_object, 'Progid')
    except Exception:
        return 'unknown'
    else:
        return value


def convert_file_size(_size):
    return size(_size)


def posix_path(*args):
    return rf'{(pathlib.PurePosixPath(*args))}'


def pure_windows_path(*args):
    return rf'{str(pathlib.PureWindowsPath(*args))}'


def unix_time(timestamp):

    # if you encounter a "year is out of range" error the timestamp
    # may be in milliseconds, try `ts /= 1000` in that case
    return str(datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'))


def is_local_file(_path):
    if path.exists(_path):
        return stat.S_ISREG(os_stat(_path).st_mode)
    else:
        return None


def is_file(attrs):
    return stat.S_ISREG(attrs.st_mode)


def remote_path_exists(_path, sftp):
    return sftp.exists(_path)


def local_path_exists(_path):
    return path.exists(_path)


def get_dir_attrs(_path, sftp):
    attrs = sftp.lstat(_path)
    attrs.filename = path.split(_path)[1]
    attrs.longname = str(attrs)
    return attrs


def file_ext(name):
    return path.splitext(name)[1]


def filename(_path):
    return path.split(_path)[1]


def dst_path(_path):
    return path.split(_path)[0]


def thumb_name(src_path):
    name = path.split(src_path)[1]
    return f'{name}.{thumbnail_ext}'


def thumb_dir_path(remote_path):
    return pure_windows_path(cache_path, remote_path.strip('/'), thumb_dir)


def default_remote():
    # noinspection PyBroadException
    try:
        config = get_config()
        _default_remote = config.get('SETTINGS', 'default_remote')
    except Exception:
        return '.'
    else:
        return _default_remote


def download_path():
    # noinspection PyBroadException
    try:
        config = get_config()
        _download_path = config.get('SETTINGS', 'download_path')
        if not path.exists(data_path):
            raise FileNotFoundError
    except FileNotFoundError:
        # put input popup here
        return path.join(environ['HOMEDRIVE'], environ['HOMEPATH'], 'Downloads')
    except Exception:
        return path.join(environ['HOMEDRIVE'], environ['HOMEPATH'], 'Downloads')
    else:
        return _download_path


def _log_file():
    import datetime
    name = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.log"
    current_log_file = path.join(log_dir, name)
    if not path.exists(log_dir):
        makedirs(log_dir)
    return current_log_file


log_file = _log_file()


def find_thumb(_dst_path, _filename):
    path_to_thumbnails = pure_windows_path(cache_path, _dst_path.strip('/'), thumb_dir)

    if not path.exists(path_to_thumbnails):
        return None
    _thumbnails = listdir(path_to_thumbnails)
    for thumbnail in _thumbnails:
        _thumbnail = '.'.join(thumbnail.split('.')[0: -1])
        if _thumbnail == _filename:
            return pure_windows_path(path_to_thumbnails, thumbnail)
    else:
        return None


def thumbnails():
    # noinspection PyBroadException
    try:
        config = get_config()
        enable_thumbnails = config.getboolean('SETTINGS', 'enable_thumbnails')
    except Exception:
        return False
    else:
        return enable_thumbnails


def file_name(_path):
    return path.split(_path)[1]


def crypto(text, password, _encrypt=False, _decrypt=False):
    from cryptography.fernet import Fernet
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    password = password.encode()
    text = text.encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=32,
        iterations=666,
        backend=default_backend(),
        salt=b''
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    f = Fernet(key)
    if _encrypt:
        return f.encrypt(text)
    elif _decrypt:
        return f.decrypt(text)


def encrypt(text, password):
    return crypto(text, password, _encrypt=True)


def decrypt(text, _password):
    return crypto(text, _password, _decrypt=True)


def resource_path(*args):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', path.dirname(path.abspath(__file__)))
    return path.join(base_path, *args)


def img_path(img):
    """ Get absolute path to img resource, works for dev and for PyInstaller """
    return path.join(resource_path('img'), img)


class TransferSettingsMapper:
    def __init__(self):

        self.options_dict = {
            'opt1': 'Ask everytime',
            'opt2': 'Skip',
            'opt3': 'Overwrite',
            'opt4': 'Overwrite if source is newer',
            'opt5': 'Overwrite if size is different'
            }

        self.range_dict = {
            'rng1': 'Ask everytime',
            'rng2': 'Apply only for this session',
            'rng3': 'Set as default'
            }

    def _option(self, txt):

        if txt.startswith('opt'):
            return self.options_dict[txt]
        else:
            for item in self.options_dict.items():
                key, value = item[0], item[1]
                if value == txt:
                    return key

    def _range(self, txt):

        if txt.startswith('rng'):
            return self.range_dict[txt]
        else:
            for item in self.range_dict.items():
                key, value = item[0], item[1]
                if value == txt:
                    return key

