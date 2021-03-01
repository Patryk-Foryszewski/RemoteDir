from os import path, environ, makedirs




def app_name():
    """Returns app name as dir name"""
    import sys
    return (path.split(sys.argv[0])[1]).split('.')[0]


app_name = app_name()
data_path = path.join(environ['LOCALAPPDATA'], 'RemoteDir', app_name)
cache_path = path.join(data_path, 'Cache')
config_file = path.join(data_path, 'config.ini')
log_dir = path.join(data_path, 'Log')
my_knownhosts = path.join(data_path, 'known_hosts')
thumb_dir = '.rdthumbnails'
button_height = 20
hidden_files = [thumb_dir]
forbidden_names = [thumb_dir]
img_extensions = ('.jpg', 'jpeg', '.png')


def get_config():

    from configparser import ConfigParser
    from common_vars import config_file
    from exceptions import ConfigNotFound
    from common_vars import data_path

    config = ConfigParser()

    if not path.exists(config_file):
        raise ConfigNotFound
    elif not path.exists(data_path):
        makedirs(data_path)
        raise ConfigNotFound
    else:
        config.read(config_file)
        return config

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


def thumb_name(dst_path, img_name):
    from common_funcs import pure_windows_path
    img_name = img_name.split('.')
    img_name = '.'.join([img_name[0], 'jpg'])
    return pure_windows_path(cache_path, dst_path.strip('/'), thumb_dir, img_name)