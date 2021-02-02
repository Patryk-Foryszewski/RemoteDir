from os import path, environ
from common_funcs import app_name, get_config

data_path = path.join(environ['LOCALAPPDATA'], 'RemoteDir', app_name())
cache_path = path.join(data_path, 'Cache')
config_file = path.join(data_path, 'config.ini')
my_knownhosts = path.join(data_path, 'known_hosts')
button_height = 20


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
    import os
    # noinspection PyBroadException
    try:
        config = get_config()
        _download_path = config.get('SETTINGS', 'download_path')
        if not os.path.exists(data_path):
            raise FileNotFoundError
    except FileNotFoundError:
        # put input popup here
        return os.path.join(os.environ['HOMEDRIVE'], os.environ['HOMEPATH'], 'Downloads')
    except Exception:
        return os.path.join(os.environ['HOMEDRIVE'], os.environ['HOMEPATH'], 'Downloads')
    else:
        return _download_path
