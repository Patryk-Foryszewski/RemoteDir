import os
import paramiko
from common import my_knownhosts, fingerprint, confirm_popup
from exceptions import HosKeyNotFound, HostkeyMatchError


class HostKeyManager:
    """
    Checks if stored server key matches recived server key.
    If no it asks for adding to my_knownhosts
    """
    def __init__(self, server, port):
        self.server = server
        self.port = port
        self.matches = False
        self.server_key = None
        self.connect = None

    def get_server_key(self):
        t = paramiko.transport.Transport(f'{self.server}:{self.port}')  # Expected type 'socked' but can be str/tuple
        t.start_client()
        return t.get_remote_server_key()

    def get_known_key(self):
        if os.path.exists(my_knownhosts):
            h = paramiko.hostkeys.HostKeys(my_knownhosts)
            known_key = h.lookup(self.server)

        else:
            known_key = None

        return known_key

    def line(self):
        return f"{self.server} {self.server_key.get_name()} {self.server_key.get_base64()}\n"

    def verify(self):
        # getting server key
        self.server_key = self.get_server_key()

        # getting local key
        known_key = self.get_known_key()
        # loading known_hosts if exists.
        if not known_key:
            raise HosKeyNotFound(fingerprint(self.server_key))

        else:
            local_key = known_key._entries[0]
            if local_key.key.asbytes() != self.server_key.asbytes():
                raise HostkeyMatchError(fingerprint(self.server_key))

    def hostkey_popup(self, text):
        confirm_popup(self.add_hostkey, text)

    def add_hostkey(self, popup, _, answer):
        popup.dismiss()
        if answer == 'yes':
            with open(my_knownhosts, 'w+') as f:
                f.write(self.line())
            self.connect()
