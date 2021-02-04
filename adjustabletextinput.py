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
        self.multiline = False
        self.text = self.my_text
        self.adjust_text()

    def on_focus(self, *args):
        if not self.focus:
            text = self.clear_text()
            if text != self.my_text:
                self.text_change(text)

            self.text = ''
            self.on_my_text()

    def set_text(self, rows):
        self.text = '\n'.join(rows)
        self.multiline = True

    def full_text(self):
        self.set_font_size()
        self.text = ''
        self.text = self.my_text

    def adjust_text(self):
        rows, step = self.split_text()
        if len(rows) > self.max_lines:
            _rows = [rows[0]]
            for row in range(1, self.max_lines-1):
                _rows.append('...')
            _rows.append(self.text[-step:])
            rows = _rows
        self.set_text(rows)

    def clear_text(self):
        return self.text.replace('\n', '')

    def on_width(self, *args):
        if self.focus:
            self.full_text()
        else:
            self.on_my_text()

    def set_height(self):
        line_height = self._lines_labels[0].height + 2 * self.line_spacing
        self.height = max(len(self._lines_labels), self.max_lines) * line_height

    def set_font_size(self):
        self.font_size = math.floor(.14 * self.width)

    def split_text(self):
        self.set_font_size()
        self.row_height = self.font_size + 2 * self.line_spacing
        lines = self._lines_labels[0].width / (.8 * self.width)
        step = math.ceil(len(self.text) / math.ceil(lines))
        start = 0
        end = step
        rows = []
        for _ in range(math.ceil(lines)):
            line = self.text[start:end]
            rows.append(line)
            start = end
            end = min(end + step, len(self.text))
        return rows, step

    def on_disabled(self, *args):
        if not self.disabled:
            self.full_text()

    def on_text(self, *args):
        self.set_height()
