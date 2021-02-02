import pysftp
import binascii
from ftplib import FTP_TLS
import paramiko
import os
from pysftp.helpers import (st_mode_to_int, WTCallbacks, path_advance,
                            path_retreat, reparent, walktree, cd, known_hosts)
from paramiko import SSHException, AuthenticationException
from common_vars import data_path
from common_funcs import fingerprint

my_knownhosts = os.path.join(data_path, 'Dir', 'known_hosts')
print('MY KEYS', my_knownhosts)
server = '94.152.130.129'
user = 'patrick'
password = '2ng2Qk8xjL'
port = 22


def verify_hostkeys():
    # getting server key
    t = paramiko.transport.Transport(f'{server}:{port}')
    t.start_client()
    server_key = t.get_remote_server_key()
    print('SERVER KEY', server_key.get_name(), server_key.get_base64())
    print('SERVER KEY BYTES', server_key.asbytes())
    # getting local key

    known_key = None
    # loading known_hosts if exists.
    if os.path.exists(my_knownhosts):

        h = paramiko.hostkeys.HostKeys(my_knownhosts)
        # lookup if key is stored
        known_key = h.lookup(server)
    else:
        print('FILE NOT FOUND', my_knownhosts)

    if not known_key:
        # put confrim popup here
        print('KEY NOT KNOWN')
        text = f"""This server host key is not known.
                  To be sure you are logging into 
                  correct server check if recived 
                  fingerprint is correct.
                  Fingerprint: {fingerprint(server_key)}

                  Press yes if you want to add this host to known host
                """
    else:
        # checking if stored key match server key
        print('KNOWN KEY', known_key, known_key._hostkeys, dir(known_key._hostkeys))
        key = known_key._entries[0].key.asbytes()
        print('SRV BYTES', server_key.asbytes())
        print('KEY BYTES', known_key._entries[0].key.asbytes())
        print('MATCHES?', known_key._entries[0].key.asbytes() == server_key.asbytes())
        if  known_key._entries[0].key.asbytes() == server_key.asbytes():
            return True
        else:
            return False

    def add_hostkey(answer):
        if answer == 'yes':
            from sftp.add_hostkey import add_hostkey
            add_hostkey(data_path)


verify_hostkeys()


def verify_and_connect():
    t = paramiko.transport.Transport(f'{server}:{port}')
    t.start_client()
    server_key = t.get_remote_server_key()
    print('SERVER KEY', server_key.asbytes())  # server_key.get_name(), server_key.get_base64())
    try:
        print('CONNECTING TO SFTP2')

        cnopts = pysftp.CnOpts()
        if os.path.exists(my_knownhosts):
            cnopts.hostkeys.load(os.path.join(data_path, 'Dir', 'known_hosts'))
        connection = pysftp.Connection(host=server,
                                       password=password,
                                       username=user,
                                       cnopts=cnopts,
                                       )
    except SSHException as ex:
        print('EX', str(ex), dir(ex))
        if 'No hostkey for' in str(ex):
            print(
                f'No host key for server. Add server with fingerprint {binascii.hexlify(server_key.get_fingerprint())} to known_hostkeys?')

        elif 'Bad host key from server' in str(ex):
            print(
                f'HOSKEYS DOESNt MATCH Your server fingerprint is {binascii.hexlify(server_key.get_fingerprint())} Is it correct?')

# verify_and_connect()