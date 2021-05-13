import os
import sys
import stat
from configparser import ConfigParser
import shutil
import json
import time

version = '1.0.00'
my_path = os.path.split(sys.argv[0])[0]
rd_version = sys.argv[1]
to_run = sys.argv[2]
to_kill = os.path.split(to_run)[1]
run = f'{to_run} kill Setup.exe'
cwd = os.getcwd()
print('###################################')
print('#######  REMOTEDIR UPDATER  #######')
print('###################################')
print('SETUP V -', version)
print(f'KILLING {to_kill}')
command = r'{}\windows\system32\taskkill.exe /f /im {}'.format(os.environ['HOMEDRIVE'], to_kill)
os.system(command)
time.sleep(3)
print('LOOKING FOR REMOTEDIR INSTANCES')
os.chdir(my_path)
_list = os.listdir()
instances = []
for file in _list:
    if stat.S_ISDIR(os.stat(file).st_mode):
        instances.append(file)
print('INSTANCES TO UPDATE - ', instances)
for _instance in instances:
    print(f'UPDATING {_instance}')
    config_path = os.path.join(_instance, 'config.ini')
    try:
        config = ConfigParser()
        config.read(config_path)
        current = config.get('PROPERTIES', 'version')
        if current != rd_version:
            paths = current = config.get('PROPERTIES', 'paths')
            paths = json.loads(paths)
            for path in paths:
                print(' -CHECK IF INSTANCE EXISTS', path)
                if os.path.exists(path):
                    print(' *INSTANCE EXISTS')
                    print('     REMOVING INSTANCE')
                    os.remove(path)
                    print('     COPING INSTANCE')
                    shutil.copy('RemoteDir.exe', path)
                else:
                    print(f' *INSTANCE DOESN\'T EXISTS')
                    print('Instance doesnt exists')
        else:
            print(f' *INSTANCE {_instance} UP TO DATE')
            continue
    except Exception as ex:
        print(' #FAILED TO UPDATE INSTANCE', ex)
    else:
        print(f' *INSTANCE {_instance} UPDATED TO {rd_version}')

os.chdir(cwd)
os.system(run)
print('###################################')
print('#####  REMOTEDIR UPDATER END ######')
print('###################################')