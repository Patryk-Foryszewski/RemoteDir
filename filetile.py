from iconcontroller import IconController


class FileTile(IconController):

    def __init__(self, attrs, file_type, space, **kwargs):
        super().__init__(attrs, file_type, space, **kwargs)
        space.add_widget(self)
        self._keyboard.bind(on_enter=self.on_enter)
        self._keyboard.bind(on_key_down=self.key_press)
        self.i = 0

    def new_name(self, _):
        self.filename = str(self.i)
        self.i += 1

    def resize(self, size):
        if size == 'Small':
            width = 100
        elif size == 'Medium':
            width = 160
        else:
            width = 300

        self.ids.pic.size = width, width

    def set_pos(self, dx, dy):
        self.pos = self.pos[0] + dx, self.pos[1] + dy
