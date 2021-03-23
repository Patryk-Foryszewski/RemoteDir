from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty, ObjectProperty


class ThreeStateCheckbox(BoxLayout):
    image = ObjectProperty('')
    state = NumericProperty(0)
    value = NumericProperty(0)
    callback = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_image()
        self.register_event_type('on_state_change')
        self.max_state = 1

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.state == self.max_state:
                self.state = 0
            else:
                self.state += 1


    def on_state(self, *_):
        self.set_image()
        self.dispatch('on_state_change')

    def set_image(self):
        if self.state == 0:
            self.image = 'img/chbx_unchecked.png'
        elif self.state == 1:
            self.image = 'img/chbx_checked.png'
        else:
            self.image = 'img/chbx_black_box.png'

    def on_state_change(self):
        pass