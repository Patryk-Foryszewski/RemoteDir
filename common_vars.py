from os import path, environ, makedirs
from common_funcs import app_name, get_config

data_path = path.join(environ['LOCALAPPDATA'], 'RemoteDir', app_name())
cache_path = path.join(data_path, 'Cache')
config_file = path.join(data_path, 'config.ini')
log_dir = path.join(data_path, 'Log')
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
    log_file = path.join(log_dir, name)
    if not path.exists(log_dir):
        makedirs(log_dir)
    return log_file

log_file = _log_file()
