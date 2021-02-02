import os
from contextlib import contextmanager

@contextmanager
def mkdir(path):
    try:
        cwd = os.getcwd()
        dst, dir = os.path.split(path)
        os.chdir(dst)
        os.mkdir(dir)
        yield
    except Exception as ex:
        print('MKDIR ERROR', ex)
    finally:
        os.chdir(cwd)
