from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.core.window import Window
import queue
from progressrow import ProgressRow


class ProgressBox(BoxLayout):
    autoflush = BooleanProperty(True)
    originator = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.autoflush = True
        self.queue = queue.Queue()

    def set_values(self, desc=''):
        self.ids.desc.text = desc

    def update(self, progress):
        progress = float(progress)
        self.ids.progress.width = progress * (self.size[0] - self.ids.percent.size[0])
        self.ids.percent.text = '{}%'.format(int(progress * 100))
        if progress == 1 and self.autoflush:
            self.flush()

    @staticmethod
    def mk_bar():
        return ProgressRow()

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            self.show_bars(hide=True)
        super().on_touch_down(touch)

    def add_bar(self, bar):
        def add(_):
            self.ids.bars_space.add_widget(bar, index=len(self.ids.bars_space.children))
        Clock.schedule_once(add, 0)

    def show_bars(self, hide=False):
        if hide:
            self.ids.scroll.height = 0
            self.hide_actions()
            self.ids.show_bars.src_path = 'img/arrow_up.png'
            self.originator.on_popup_dismiss()
        else:
            self.ids.scroll.height = .7 * Window.height
            self.ids.show_bars.src_path = 'img/arrow_down.png'
            self.originator.on_popup()

    def transfer_start(self):
        self.ids.short_info.text = 'Transferring files'

    def transfer_stop(self):
        for bar in self.ids.bars_space.children:
            if not bar.my_thread.done:
                break
        else:
            self.ids.short_info.text = 'Files transferred'

    def show_actions(self):
        self.ids.actions.height = 26

    def hide_actions(self):
        self.ids.actions.height = 0

    def overwrite_all(self):
        self.hide_actions()
        for bar in self.ids.bars_space.children:
            bar.hide_actions()
            bar.my_thread.overwrite()

    def skip_all(self):
        self.hide_actions()
        for bar in self.ids.bars_space.children:
            bar.hide_actions()
            bar.my_thread.skip()

    def clear(self):
        self.skip_all()
        self.manager.threads.clear()
        self.show_bars(hide=True)
        self.ids.bars_space.clear_widgets()

    def set_manager(self, manager):
        self.manager = manager

    def stop(self):
        self.manager.stop_transfers()

    def flush(self):
        self.ids.progress.width = 0
        self.ids.percent.text = ''
