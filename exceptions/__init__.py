
class InvalidConfig(Exception):
    def __init__(self, errors):
        super().__init__(self)
        self.errors = errors
        self.message = 'Invalid config'

    def __str__(self):
        return f'Invalid config {self.errors}'


class PasswordEncrypted(Exception):
    def __init__(self):
        super().__init__(self)
        self.message = 'Type main password'

    def __str__(self):
        return self.message


class ConfigNotFound(Exception):
    def __init__(self):
        super().__init__(self)
        self.message = 'Fill credentials form'

    def __str__(self):
        return f'Config not found'


class HosKeyNotFound(Exception):
    def __init__(self, fingerprint):
        super().__init__(self)
        self.message = f"""
                      This server host key is not known.
                      To be sure you are logging into 
                      correct server check if recived 
                      fingerprint is correct.
                      
                      Fingerprint: {fingerprint}

                      Press yes if you want to add this host to known host
                    """

    def __str__(self):
        return f'HostKey not found'


class HostkeyMatchError(Exception):
    def __init__(self, fingerprint):
        super().__init__(self)
        self.message = f"""
                Stored host key is different than recived from server.
                Posibbility of "Man in the middle" attack. Be carefull!
                Check if below server fingerprint is the one you want to login to:
                
                Fingerprint: {fingerprint}
                
                Press yes if you want to add this host to known host"""

    def __str__(self):
        return f'HostKey match error'
