from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty


class ConfirmPopup(BoxLayout):
    text = StringProperty()

    def __init__(self, **kwargs):
        self.register_event_type('on_answer')
        super(ConfirmPopup, self).__init__(**kwargs)

    @staticmethod
    def on_answer(_):
        return ()
