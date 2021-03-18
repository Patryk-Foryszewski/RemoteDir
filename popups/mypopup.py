from kivy.uix.popup import Popup
from kivy.app import App
from kivy.core.window import Window


class MyPopup(Popup):
    """My Popup class thad adds popup moving possiblity"""

    def __init__(self, **kwargs):
        super().__init__(title=kwargs['title'],
                         content=kwargs['content'],
                         size_hint=kwargs['size_hint'],
                         auto_dismiss=kwargs.get('auto_dismiss'),
                         size=kwargs.get('size'))
        self.movable = kwargs['movable']

    def on_touch_move(self, touch):
        if self.movable and self.collide_point(*touch.pos):
            width, height = App.get_running_app().root.size
            print('DX', touch.dx, 'DY', touch.dy)
            dx = touch.dx if ((touch.dx < 0 and self.x >= 0) or (touch.dx > 0 and self.right < Window.width)) else 0
            dy = touch.dy if ((touch.dy < 0 and self.y >= 0) or (touch.dy > 0 and self.top < Window.height)) else 0

            self.pos_hint = {'x': (self.pos[0] + dx)/width,
                             'y': (self.pos[1] + dy)/height}
