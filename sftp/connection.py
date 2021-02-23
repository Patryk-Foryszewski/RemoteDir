from common_funcs import get_config, mk_logger
from common_vars import my_knownhosts
from sftp.hostkeymanager import HostKeyManager
from exceptions import InvalidConfig
import pysftp

logger = mk_logger(__name__)


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
        self.port = self.config.get('CREDENTIALS', 'port')
        pkey = self.config.get('CREDENTIALS', 'private_key')
        self.private_key = pkey if pkey else None
        self.private_key_pass = None

    def validate_config(self):
        if not self.password and not self.private_key:
            raise InvalidConfig(errors=['password', 'private_key'])

    def server_auth(self):
        self.hostkeys = HostKeyManager(self.server, self.port)
        self.hostkeys.verify()

    def auth(self, credentials):
        password = credentials.ids.password.text
        private_key = credentials.ids.private_key.text
        self.password = password if password else None
        self.private_key = private_key if private_key else None
        credentials.originator.dismiss()
        self.start()

    def connect(self):
        cnopts = pysftp.CnOpts(my_knownhosts)
        try:
            sftp = pysftp.Connection(
                                    host=self.server,
                                    username=self.user,
                                    password=self.password,
                                    private_key=self.private_key,
                                    private_key_pass=self.private_key_pass,
                                    cnopts=cnopts)
        except Exception as ex:
            logger.exception(f'Failed to connect to server {ex}')
            return False
        else:
            return sftp

    def close(self):
        self.sftp.close()
