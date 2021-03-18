from kivy.uix.popup import Popup

class InfoPopup(Popup):
    def __init__(self, *args, **kwargs):
        super().__init__(title=args[0])

