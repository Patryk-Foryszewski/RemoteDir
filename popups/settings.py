from kivy.uix.popup import Popup
from kivy.uix.button import Button
from functools import partial
from settings import settings


class Settings(Popup):
    title = 'Settings'

    def __init__(self, on_open, on_dismiss, auto_dismiss=True):
        super().__init__()
        self.options = settings
        self.settings_dict = {}
        self.open()
        on_open()
        self.bind(on_dismiss=on_dismiss)
        self.auto_dismiss = auto_dismiss
        self.current_content = None

    def fill(self):
        for option in self.options:
            name = option.name
            self.settings_dict.update({name: {'tags': option.tags, 'class': option}})
            self.add_button(name)

    def search(self, text):
        self.clear_buttons()
        if text:
            text = text.lower()
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
        self.current_content = self.settings_dict[args[0]]['class']()
        self.current_content.originator = self
        self.ids.content.add_widget(self.current_content)

    def on_touch_down(self, touch):
        print('SETTINGS ON TOUCH ')
        if not self.collide_point(*touch.pos):
            if self.current_content:
                dismissed = self.current_content.on_dismiss()
                if dismissed:
                    self.dismiss()
                else:
                    self.title = 'Fill the form correctly'
        return super().on_touch_down(touch)