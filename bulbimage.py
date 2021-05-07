from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.properties import BooleanProperty


class BulbImage(Image):
    focus = BooleanProperty(False)
    mouse_locked = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_move)

    def on_mouse_move(self, *args):
        mouse_pos = args[1]
        if self.mouse_locked:
            return

        if self.focus:
            self.background_color = self.focused_color

        elif self.collide_point(*self.to_widget(*mouse_pos)):
            self.background_color = self.active_color

        else:
            self.background_color = self.unactive_color

