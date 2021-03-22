from kivy.uix.boxlayout import BoxLayout
from popups.mypopup import MyPopup
from kivy.clock import Clock
from pysftp.helpers import st_mode_to_int
from kivy.properties import StringProperty, NumericProperty


class ChmodPopup(BoxLayout):
    value_error = StringProperty('')
    mode = StringProperty('')
    owner_read = NumericProperty()
    owner_write = NumericProperty()
    owner_execute = NumericProperty()
    group_read = NumericProperty()
    group_write = NumericProperty()
    group_execute = NumericProperty()
    other_read = NumericProperty()
    other_write = NumericProperty()
    other_execute = NumericProperty()

    def __init__(self, file, on_save, on_popup, on_dismiss):
        super().__init__()
        self.file = file
        self.attrs = file.attrs
        self.on_save = on_save
        self.first_run = True
        self.on_popup = on_popup
        self.on_dismiss = on_dismiss
        self.popup = None
        self.pop_me_up()
        self.fill(st_mode_to_int(self.attrs.st_mode))

    def pop_me_up(self):
        self.popup = MyPopup(title=f'Attributes of {self.attrs.filename}',
                        content=self,
                        size_hint=(None, None),
                        size=(300, 340),
                        auto_dismiss=True,
                        movable=True)
        self.popup.bind(on_dismiss=self.on_dismiss)

        def _open(_):
            self.popup.open()
            self.on_popup()
        Clock.schedule_once(_open, 0.1)

    def fill(self, mode=None):
        self.mode = str(mode)
        mode = self.mode.zfill(3)
        bin_owner_perm = bin(int(mode[0]))[2:].zfill(3) if len(mode) >= 1 else '000'
        bin_group_perm = bin(int(mode[1]))[2:].zfill(3) if len(mode) >= 2 else '000'
        bin_other_perm = bin(int(mode[2]))[2:].zfill(3) if len(mode) == 3 else '000'
        self.owner_read = int(str(bin_owner_perm)[0])
        self.owner_write = int(str(bin_owner_perm)[1])
        self.owner_execute = int(str(bin_owner_perm)[2])
        self.group_read = int(str(bin_group_perm)[0])
        self.group_write = int(str(bin_group_perm)[1])
        self.group_execute = int(str(bin_group_perm)[2])
        self.other_read = int(str(bin_other_perm)[0])
        self.other_write = int(str(bin_other_perm)[1])
        self.other_execute = int(str(bin_other_perm)[2])
        self.first_run = False

    def change_mode(self, value):
        try:
            value = int(value)
        except Exception:
            self.value_error = 'Wrong value'
            self.ids.save_btn.disabled = True

        else:
            self.ids.save_btn.disabled = False
            self.value_error = ''
            self.first_run = True
            self.fill(value)
            self.first_run = False

    def on_owner_read(self, *_):
        self.recount_attribute()

    def on_owner_write(self, *_):
        self.recount_attribute()

    def on_owner_execute(self, *_):
        self.recount_attribute()

    def on_group_read(self, *_):
        self.recount_attribute()

    def on_group_write(self, *_):
        self.recount_attribute()

    def on_group_execute(self, *_):
        self.recount_attribute()

    def on_other_read(self, *_):
        self.recount_attribute()

    def on_other_write(self, *_):
        self.recount_attribute()

    def on_other_execute(self, *_):
        self.recount_attribute()

    def recount_attribute(self):
        if self.first_run:
            return

        owner = f'{self.owner_read}{self.owner_write}{self.owner_execute}'
        group = f'{self.group_read}{self.group_write}{self.group_execute}'
        other = f'{self.other_read}{self.other_write}{self.other_execute}'

        value = f'{int(owner, 2)}{int(group, 2)}{int(other, 2)}'
        self.fill(int(value))

    def save(self):
        self.on_save(self.file, self.mode.zfill(3), self.popup)
