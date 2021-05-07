from iconcontroller import IconController


class FileDetails(IconController):

    def __init__(self, attrs, file_type, space, **kwargs):
        super().__init__(attrs, file_type, space, **kwargs)
        space.add_widget(self)

    def resize(self, size):
        if size == 'Small':
            self.height = 34
        elif size == 'Medium':
            self.height = 45
        else:
            self.height = 55

    def set_pos(self, _, dy):
        self.y += dy
