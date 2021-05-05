from settings.associations import Associations
from settings.credentials import Credentials
from settings.paths import Paths
from settings.thumbnails import Thumbnails
from settings.transfersettings import TransferSettings

"""

    Classes for settings options. 
    Each class must have below class variables:
        name: (str) String that will appear on button in Settings Popup
        tags: (list) of tags that allows to search through settings. 
    Instances of settings are content of Setting Popup. (path: popups/settings.py)

"""

settings = (Associations, Credentials, Paths, Thumbnails, TransferSettings)
__all__ = settings

