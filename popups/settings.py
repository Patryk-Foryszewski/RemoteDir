from kivy.uix.popup import Popup
from settings.credentials import Credentials
from settings.paths import Paths
from settings.thumbnails import Thumbnails
from settings.transfersettings import TransferSettings
from kivy.uix.button import Button
from functools import partial


class Settings(Popup):
    def __init__(self, on_open, on_dismiss, auto_dismiss=True):
        super().__init__()
        self.options = [Credentials, Paths, Thumbnails, TransferSettings]
        self.settings_dict = {}
        self.open()
        on_open()
        self.bind(on_dismiss=on_dismiss)
        self.auto_dismiss = auto_dismiss

    def fill(self):
        for option in self.options:
            name = option.name
            self.settings_dict.update({name: {'tags': option.tags, 'class':option}})
            self.add_button(name)

    def search(self, text):
        print('SEARCH', text)
        self.clear_buttons()
        if text:
            for option in self.options:
                if text in option.tags:
                    self.add_button(option.name)
        else:
            self.fill()

    def clear_buttons(self):
        self.ids.options.clear_widgets()

    def add_button(self, text):
        bt = Button(text=text)
        bt.bind(on_press=partial(self.add_content, text))
        self.ids.options.add_widget(bt)

    def add_content(self, *args):
        self.ids.content.clear_widgets()
        op = self.settings_dict[args[0]]['class']()
        self.ids.content.add_widget(op)
