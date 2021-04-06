from kivy.uix.boxlayout import BoxLayout
from common import int_validation, data_path, config_file, get_config, encrypt, decrypt
from kivy.core.window import Window
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import shutil
from cryptography.fernet import InvalidToken
from configparser import ConfigParser
import os
from kivy.app import App
import re
from kivy.properties import StringProperty
from common import mk_logger

logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


class CredentialsPopup(BoxLayout):
    auto_dismiss = False
    message = StringProperty('')

    def __init__(self, callback=None, errors=None, auto_dismiss=False):
        super().__init__()
        self.bind_external_drop()
        self.callback = callback
        self.show_errors(errors)
        self.auto_dismiss = auto_dismiss
        self.dismissed = False
        self.password = ''
        self.encrypted_password = ''
        self.fill()
        self.path = None
        self.inputs = None
        self.popup = None

    def show_errors(self, errors_dict):
        if errors_dict:
            errors = errors_dict.get('errors')
            self.message = errors_dict['message']
            if 'server' in errors:
                self.ids.server_err.text = 'Type correct server name or IP'
            if 'user' in errors:
                self.ids.user_err.text = 'Type correct username'
            if 'password' in errors:
                self.ids.password_err.text = 'Type correct password'
            if 'private_key' in errors:
                self.ids.private_key_err.text = 'Drop correct key file or type password'
            if 'main_password' in errors:
                self.ids.main_password.text = 'Main password is incorrect'

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
            self.encrypted_password = config.get('CREDENTIALS', 'password')
            if self.encrypted_password:
                self.ids.password.text = ''
                self.ids.password.hint_text = '*' * 10





    def decrypt_password(self, encrypted):
        try:
            decrypted = decrypt(encrypted, self.ids.main_password.text)
        except Exception as ex:
            ex_log('Could not decrypt password', type(ex))
            return None
        else:
            return decrypted

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

        if self.dismissed:
            return
        self.path = path.decode(encoding='UTF-8', errors='strict')
        try:
            with open(path) as f:
                text = f.readlines()

        except Exception as ex:
            self.ids.private_key_err.text = 'Failed to read private key file'
        else:
            if text[0].split()[1] == 'ssh-rsa':
                pass

            self.ids.private_key.text = self.path

    def bind_external_drop(self):
        Window.bind(on_dropfile=self.on_dropfile)

    def unbind_external_drop(self):
        Window.unbind(on_dropfile=self.on_dropfile)

    def connect(self):
        self.unbind_external_drop()
        if self.encrypted_password and not self.password:
            try:
                decrypted_password = decrypt(self.encrypted_password, self.ids.main_password.text)
            except Exception as ex:
                self.message = f'Failed to decrypt password {type(ex)}'
                ex_log(self.message)
                 
            else:
                if decrypted_password:
                    self.password = decrypted_password.decode()
                else:
                    return

        if not self.validate():
            return
        self.save_config()
        self.dismissed = True
        App.get_running_app().root.connect(self.popup, self.password)

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
        config.set('CREDENTIALS', 'password', self.encrypted_password)
        with open(config_file, 'w+') as f:
            config.write(f)


    def encrypt(self, text):
        main_password = self.ids.main_password.text

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=32,
            iterations=666,
            backend=default_backend(),
            salt=b''
        )
        key = base64.urlsafe_b64encode(kdf.derive(main_password))
        f = Fernet(key)

        decrypted = f.encrypt(text)
        return decrypted


    def validate_password(self, password, focus=False):

        if focus and len(password) <= 0:
            return

        self.ids.main_password_inp_err.text = 'Password to weak'
        if len(password) < 8:
            return False
        elif not re.search("[a-z]", password):
            return False
        elif not re.search("[A-Z]", password):
            return False
        elif not re.search("[0-9]", password):
            return False
        elif not re.search("[_@$]", password):
            return False
        elif re.search("\s", password):
            return False
        self.ids.main_password_inp_err.text = ''
        return True

    def clear_errors(self):
        self.ids.main_password_inp_err.text = ''
        self.ids.main_password_cmp_err.text = ''

    def confirm_main_password(self, password, confirm):
        if len(password) <= 0:
            return
        elif not self.validate_password(password):
            self.ids.main_password_cmp_err.text = 'Type correct password'
            self.ids.main_password_cmp.text = ''
        elif len(confirm) >= len(password) and password != '':
            if password != confirm:
                self.ids.main_password_cmp_err.text = 'Password doesn\'t match'
            else:
                self.clear_errors()

        else:
            self.ids.main_password_cmp_err.text = ''

    def password_requirements(self):
        requirements = f'{"  1. Minimum 8 characters."}\n' \
                       f'{"  2. The alphabets must be between [a-z]"}\n' \
                       f'{"  3. At least one alphabet should be of Upper Case [A-Z]."}\n' \
                       f'{"  4. At least 1 number or digit between [0-9]."}\n' \
                       f'{"  5. At least 1 character from [ _ or @ or $ ]."}\n'

        return requirements

    def set_password(self, password):
        self.password = password

    def set_main_password(self):
        main_password = self.ids.main_password_inp.text
        if not self.validate_password(main_password):
            self.message = 'Password too weak'
        elif not self.password:
            self.message = 'Type password to server first'
        else:
            self.message = ''
            self.encrypted_password = encrypt(self.password, main_password).decode()
            print('ENCRYPTED PASSWORD', self.encrypted_password)
            config = get_config()
            config.set('CREDENTIALS', 'password', self.encrypted_password)
            with open(config_file, 'w+') as f:
                config.write(f)

    def dismiss(self):
        self.popup.dismiss()

    def on_connect(self):
        return
