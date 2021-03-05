from kivy.uix.relativelayout import RelativeLayout
from common_funcs import int_validation
from kivy.core.window import Window
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import shutil
from common_vars import data_path, config_file
from common_funcs import get_config
from cryptography.fernet import InvalidToken
from configparser import ConfigParser
import os
from kivy.app import App


class CredentialsPopup(RelativeLayout):
    auto_dismiss = False

    def __init__(self, callback=None, errors=None):
        super().__init__()
        self.bind_external_drop()
        self.callback = callback
        self.show_errors(errors)
        self.dismissed = False
        self.fill()
        self.path = None
        self.inputs = None

    def show_errors(self, errors):
        if errors:
            if 'server' in errors:
                self.ids.server_err.text = 'Type correct server name or IP'
            if 'user' in errors:
                self.ids.user_err.text = 'Type correct username'
            if 'password' in errors:
                self.ids.password_err.text = 'Type correct password'

        else:
            self.ids.password_err.text = ''
            self.ids.user_err.text = ''
            self.ids.server_err.text = ''

    def fill(self):
        # noinspection PyBroadException
        try:
            config = get_config()
        except Exception:
            pass
        else:
            self.ids.server.text = config.get('CREDENTIALS', 'server')
            self.ids.user.text = config.get('CREDENTIALS', 'user')
            self.ids.port.text = config.get('CREDENTIALS', 'port')
            self.ids.private_key.text = config.get('CREDENTIALS', 'private_key')

    def get_inputs(self):

        server = '' if not self.ids.server.text else self.ids.server.text
        user = '' if not self.ids.user.text else self.ids.user.text
        port = '' if not self.ids.port.text else self.ids.port.text
        password = '' if not self.ids.password.text else self.ids.password.text
        private_key = '' if not self.ids.private_key.text else self.ids.private_key.text

        return {
                'server': server,
                'user': user,
                'password': password,
                'port': port,
                'private_key': private_key
                }

    def validate(self):
        self.inputs = self.get_inputs()

        valid = True
        if not self.inputs['server']:
            self.ids.server_err.text = 'Server name can not be empty'
            valid = False
        else:
            self.ids.server_err.text = ''

        if not self.inputs['user']:
            self.ids.user_err.text = 'User name can not be empty'
            valid = False
        else:
            self.ids.user_err.text = ''

        if not self.inputs['password'] and not self.inputs['private_key']:
            self.ids.password_err.text = 'Put a password'
            valid = False
        else:
            self.ids.password_err.text = ''

        port = int_validation(self.inputs['port'])
        if not port[0]:
            self.ids.port_err.text = 'Wrong port nr'
        else:
            self.ids.port_err.text = ''

        if valid:
            # Possibility of coping pkey file to program directory. Rethink if that can be useful. 
            # if self.ids.copy_pkey.state == 'down':
            #    shutil.copy(self.path, config_file)

            return True
        else:
            return False

    def on_dropfile(self, _, path):
        print('DROPPED FILE', path)
        if self.dismissed:
            return
        self.path = path.decode(encoding='UTF-8', errors='strict')
        try:
            with open(path) as f:
                text = f.readlines()

        except Exception as ex:
            print('READ ERROR', ex)
            self.ids.private_key_err.text = 'Failed to read private key file'
        else:
            print('Credentials', text)
            if text[0].split()[1] == 'ssh-rsa':
                print('ELO')

            self.ids.private_key.text = self.path

    def bind_external_drop(self):
        Window.bind(on_dropfile=self.on_dropfile)

    def unbind_external_drop(self):
        Window.unbind(on_dropfile=self.on_dropfile)

    def connect(self):
        self.unbind_external_drop()
        if not self.validate():
            return
        self.save_config()
        self.dismissed = True
        App.get_running_app().root.connect(self.originator, self.inputs['password'])

    def save_config(self):
        if not self.validate():
            return
        if not os.path.exists(data_path):
            os.makedirs(data_path)

        config = ConfigParser()
        config.read(config_file)

        # noinspection PyBroadException
        try:
            config.add_section('CREDENTIALS')
        except Exception:
            pass
        config.set('CREDENTIALS', 'server', self.inputs['server'])
        config.set('CREDENTIALS', 'user', self.inputs['user'])
        config.set('CREDENTIALS', 'port', self.inputs['port'])
        config.set('CREDENTIALS', 'private_key', self.inputs['private_key'])

        with open(config_file, 'w+') as f:
            config.write(f)
        #password = self.inputs['program_password'].encode() or self.inputs['password'].encode()
        #print('PASSWORD', password)
        #config = json.dumps(self.inputs).encode()
        #kdf = PBKDF2HMAC(
        #    algorithm=hashes.SHA512(),
        #    length=32,
        #    iterations=100000,
        #    backend=default_backend(),
        #    salt=b''
        #)
        #key = base64.urlsafe_b64encode(kdf.derive(password))
        #f = Fernet(key)
        #
        #decrypted = f.encrypt(config)
        #with open('config.ini', 'wb') as config:
        #    config.write(decrypted)

    def on_connect(self):
        return
