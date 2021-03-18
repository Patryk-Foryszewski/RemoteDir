from kivy.uix.boxlayout import BoxLayout
from popups.mypopup import MyPopup
from kivy.clock import Clock
from pysftp.helpers import st_mode_to_int
from kivy.properties import StringProperty


class ChmodPopup(BoxLayout):
    value_error = StringProperty('')
    mode = StringProperty('')

    def __init__(self, attrs, on_popup, on_dismiss):
        super().__init__()
        self.attrs = attrs
        self.on_popup = on_popup
        self.on_dismiss = on_dismiss
        self.pop_me_up()
        self.fill()

    def pop_me_up(self):
        print('FILL CHMOD', st_mode_to_int(self.attrs.st_mode), self.attrs)
        popup = MyPopup(title=f'Attributes of {self.attrs.filename}',
                        content=self,
                        size_hint=(None, None),
                        size=(300, 340),
                        auto_dismiss=True,
                        movable=True)
        popup.bind(on_dismiss=self.on_dismiss)

        def _open(_):
            popup.open()
            self.on_popup()
        Clock.schedule_once(_open, 0.1)

    def fill(self):
        self.mode = str(st_mode_to_int(self.attrs.st_mode))
        print('FILL CHMOD', self.attrs.st_mode)

    def on_dismiss(self, _):
        self.on_dismiss()

    def change_mode(self, value):
        print('CHANGE MODE', self.ids.numeric_value_lbl.size, '#', self.ids.numeric_value_lbl.texture_size)
        try:
            if value == '':
                pass
            if not (value == 'x' or value == 'xx' or value == 'xxx'):
                int(value)
            if int(value) > 777:
                raise Exception

        except Exception:
            #self.ids.numeric_value_lbl.text = 'Wrong value'
            self.value_error = 'Wrong value'
        else:
            self.value_error = ''
            #self.ids.numeric_value_lbl.text = self.ids.numeric_value_lbl.def_text

