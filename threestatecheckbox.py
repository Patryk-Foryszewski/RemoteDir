from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty, StringProperty


class ThreeStateCheckbox(BoxLayout):
    image = StringProperty('')
    state = NumericProperty(0)
    value = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_image()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.state == 2:
                self.state = 0
            else:
                self.state += 1

    def on_state(self, *_):
        self.set_image()

    def set_image(self):
        if self.state == 0:
            self.image = 'img/chbx_unchecked.png'
        elif self.state == 1:
            self.image = 'img/chbx_checked.png'
        else:
            self.image = 'img/chbx_black_box.png'
