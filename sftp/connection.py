from common import get_config, mk_logger, my_knownhosts
from sftp.hostkeymanager import HostKeyManager
from exceptions import InvalidConfig, PasswordEncrypted
import pysftp

logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


class Connection:
    def __init__(self, password=None):
        self.password = password
        self.sftp = None
        self.private_key = None
        self.private_key_pass = None
        self.hostkeys = None
        self.config = None
        self.server = None
        self.user = None
        self.port = None

    def start(self):
        self.read_config()
        self.validate_config()
        self.server_auth()
        self.sftp = self.connect()

    def read_config(self):
        self.config = get_config()
        self.server = self.config.get('CREDENTIALS', 'server')
        self.user = self.config.get('CREDENTIALS', 'user')
        password = self.config.get('CREDENTIALS', 'password')
        self.port = self.config.get('CREDENTIALS', 'port')
        pkey = self.config.get('CREDENTIALS', 'private_key')
        self.private_key = pkey if pkey else None
        self.private_key_pass = None

        if password and not self.password:
            raise PasswordEncrypted

    def validate_config(self):
        if not self.password and not self.private_key:
            raise InvalidConfig(errors={'errors': ['password', 'private_key'],
                                        'message': 'Type password or drop a private key file'})

    def server_auth(self):
        self.hostkeys = HostKeyManager(self.server, self.port)
        self.hostkeys.verify()

    def auth(self, credentials):
        password = credentials.ids.password.text
        private_key = credentials.ids.private_key.text
        self.password = password if password else None
        self.private_key = private_key if private_key else None
        credentials.dismiss()
        self.start()

    def connect(self):
        cnopts = pysftp.CnOpts(my_knownhosts)
        sftp = pysftp.Connection(
                                host=self.server,
                                username=self.user,
                                password=self.password,
                                private_key=self.private_key,
                                private_key_pass=self.private_key_pass,
                                cnopts=cnopts)

        return sftp

    def close(self):
        self.sftp.close()
