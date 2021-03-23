from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.properties import StringProperty


class InfoLabel(Label):
    text = StringProperty('')

    def __init__(self, text, popup=None):
        super().__init__()
        self.text = text
        self.popup = popup

    def dismiss_me(self, text):
        self.text = text
        if self.popup:
            def dismiss(_):
                self.popup.dismiss()
            Clock.schedule_once(dismiss, 3)

    def on_text(self, *args):
        self.width = self.text_size[0] + 10

