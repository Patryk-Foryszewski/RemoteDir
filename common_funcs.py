import logging
import os
import stat
import sys
import binascii
import winreg
import pathlib
from hurry.filesize import size
from datetime import datetime


def mk_logger(name, _format=None):
    from common_vars import log_file
    # Create a custom logger
    if not _format:
        _format = '[%(levelname)-8s] [%(asctime)s] [%(message)s]'
    logger = logging.getLogger(name)

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
    logger.setLevel(logging.DEBUG)

    return logger


def tell_me_about(text, _object):
    object_methods = []
    print("I'M TELLING YOU ABOUT", text)

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


def clipboard_checker(_):
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
    try:
        validated = int(to_validate)
    except Exception as ex:
        return [False, ex]
    else:
        return [True, validated]


def app_name():
    """Returns app name as dir name"""

    return (os.path.split(sys.argv[0])[1]).split('.')[0]


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
    from common_vars import config_file
    from exceptions import ConfigNotFound
    from common_vars import data_path

    config = ConfigParser()

    if not os.path.exists(config_file):
        raise ConfigNotFound
    elif not os.path.exists(data_path):
        os.makedirs(data_path)
        raise ConfigNotFound
    else:
        config.read(config_file)
        return config


def settings_popup(title='Settings'):
    from kivy.uix.popup import Popup
    from popups.settingspopup import SettingsPopup
    from kivy.clock import Clock

    def open_popup(_):
        content = SettingsPopup()
        popup = Popup(title=title,
                      content=content,
                      size_hint=(None, .8),
                      width=600)

        content.originator = popup
        popup.open()

    Clock.schedule_once(open_popup, .1)


def credential_popup(callback=None, title='Credentials', errors=None):
    from kivy.uix.popup import Popup
    from popups.credentialspopup import CredentialsPopup
    from kivy.clock import Clock

    def open_popup(_):
        content = CredentialsPopup(callback, errors)
        popup = Popup(title=title,
                      content=content,
                      size_hint=(None, .8),
                      width=600)

        content.originator = popup
        popup.open()

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


def menu_popup(originator, buttons, callback, widget=None, mouse_pos=None):
    from popups.menupopup import MenuPopup
    from kivy.clock import Clock

    def open_popup(_):
        popup = MenuPopup(
            buttons=buttons,
            originator=originator,
            callback=callback,
            auto_dismiss=True,
            size_hint=(None, None),
            widget=widget,
            mouse_pos=mouse_pos
        )

        popup.open()

    Clock.schedule_once(open_popup, .1)


def get_progid(filename):
    # noinspection PyBroadException
    try:
        ext = os.path.splitext(filename)[1]
        partial_key = r'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\{}\UserChoice'.format(ext)
        with winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER) as reg:
            with winreg.OpenKey(reg, partial_key) as key_object:
                value, type = winreg.QueryValueEx(key_object, 'Progid')
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


def is_local_file(path):
    if os.path.exists(path):
        return stat.S_ISREG(os.stat(path).st_mode)
    else:
        return None


def is_file(attrs):
    return stat.S_ISREG(attrs.st_mode)


def remote_path_exists(path, sftp):
    return sftp.exists(path)


def local_path_exists(path):
    return os.path.exists(path)


def get_dir_attrs(path, sftp):
    attrs = sftp.lstat(path)
    attrs.filename = os.path.split(path)[1]
    attrs.longname = str(attrs)
    return attrs

