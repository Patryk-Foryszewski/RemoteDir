from kivy.uix.boxlayout import BoxLayout
from kivy.properties import BooleanProperty, StringProperty


class ShortenTextInput(BoxLayout):
    """
    Class that wraps text in oneline textinput when text is longer than widget.
    (Not ready yet)
    """

    text = StringProperty()
    focus = BooleanProperty()
    text_validate = BooleanProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_text')

