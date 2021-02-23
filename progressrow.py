from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock


class ProgressRow(BoxLayout):
    def __init__(self, my_thread=None, **kwargs):
        super().__init__(**kwargs)
        self.my_thread = my_thread

    def set_values(self, desc=''):
        self.ids.desc.text = desc

    def file_exists_error(self):
        self.ids.actions.height = 20

    def hide_actions(self):
        self.ids.actions.height = 0

    def overwrite(self):
        self.my_thread.overwrite()

    def update(self, *args):
        progress = float(args[0]/args[1])
        self.ids.progress.width = progress * (self.size[0] - self.ids.percent.size[0])
        self.ids.percent.text = '{}%'.format(int(progress * 100))

    def done(self):
        self.set_values(f'{self.ids.desc.text} - Completed')
        self.hide_actions()

    def skip(self):
        self.my_thread.skip()
        self.hide_actions()

    def clear(self, *args):
        if len(args) == 0:
            Clock.schedule_once(self.clear,  3)
        else:
            self.height = 0

    def flush(self):
        self.ids.progress.width = 0
        self.ids.percent.text = ''
