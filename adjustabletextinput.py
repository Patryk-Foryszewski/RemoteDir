from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty, StringProperty
import math


class AdjustableTextInput(TextInput):
    max_lines = ObjectProperty()
    my_text = StringProperty()
    text_change = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.row_height = None

    def on_my_text(self, *args):
        print('ON MY TEXT', args)
        self.multiline = False
        self.text = self.my_text
        self.adjust_text(args[1])

    def on_focus(self, *args):
        print('ON FOCUS', args, self.focus)
        if self.focus:
            self.full_text(self.my_text)
        else:
            text = self.clear_text()
            print('     NEW TEXT', self.text, '#', text, '#', self.my_text, '#', text != self.my_text)
            if text != self.my_text:
                self.text_change(text)
            else:
                self.multiline = False
                self.text = self.my_text
                self.adjust_text(self.my_text)

    def set_text(self, rows):
        print('     SET TEXT', rows)

        self.text = ''.join(rows)
        print('     MYTEXT', self.my_text)
        print('     TEXT', self.text)
        print('     LINES', len(self._lines_labels), self._lines_labels)
        self.set_height(len(self._lines_labels))
        self.multiline = True

    def full_text(self, text):
        self.multiline = False
        rows = self.split_text(text)[0]
        self.set_text(rows)

    def adjust_text(self, text):
        rows, step = self.split_text(text)
        if len(rows) > self.max_lines:
            _rows = []
            _rows.append(rows[0])
            for row in range(1, self.max_lines-1):
                _rows.append('...')
            _rows.append(text[-step:])
            rows = _rows
        self.set_text(rows)

    def clear_text(self):
        return self.text.replace('\n', '')

    def set_height(self, rows):
        self.height = self.row_height * math.ceil(rows) + 6
        print('SET HEIGHT', rows, self.height)

    def on_text(self, *args):
        print('ON TEXT', self.text, *args)
        self.full_text(self.text)

    def split_text(self, text):

        self.font_size = math.floor(.16*self.width)
        print('ADJUST', self.line_height)
        print('     INPUT SIZE', self.size)
        print('     TEXT WIDTH', self._lines_labels[0].width)
        self.row_height = self._lines_labels[0].height
        lines = self._lines_labels[0].width / self.width

        print('     LINES     ', lines, math.ceil(lines))

        step = math.ceil(len(text) / math.ceil(lines))
        start = 0
        end = step
        rows = []
        for _ in range(math.ceil(lines)):
            line = text[start:end]
            rows.append(line)
            start = end
            end = min(end + step, len(text))
        print('     ROWS      ', rows, step)
        return rows, step
