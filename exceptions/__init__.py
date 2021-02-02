
class InvalidConfig(Exception):
    def __init__(self, errors):
        super().__init__(self)
        self.errors = errors
        self.message = 'Invalid config'

class ConfigNotFound(Exception):
    def __init__(self):
        super().__init__(self)
        self.message = 'Fill credentials form'

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

class HostkeyMatchError(Exception):
    def __init__(self, fingerprint):
        super().__init__(self)
        self.message = f"""
                Stored host key is different than recived from server.
                Posibbility of "Man in the middle" attack. Be carefull!
                Check if below server fingerprint is the one you want to login to:
                
                Fingerprint: {fingerprint}
                
                Press yes if you want to add this host to known host"""