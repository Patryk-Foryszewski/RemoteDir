from kivy.uix.popup import Popup
from kivy.app import App

class MyPopup(Popup):
    """My Popup class thad adds popup moving possiblity"""


    def __init__(self, **kwargs):
        super().__init__(title=kwargs['title'],
                         content=kwargs['content'],
                         size_hint=kwargs['size_hint'])
        self.movable = kwargs['movable']

    def on_touch_move(self, touch):
        if self.movable and self.collide_point(*touch.pos):
            width, height = App.get_running_app().root.size
            self.pos_hint={'x':(self.pos[0] + touch.dx)/width,
                           'y':(self.pos[1] + touch.dy)/height}

