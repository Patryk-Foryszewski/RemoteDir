from kivy.config import Config

Config.set('graphics', 'multisamples', '0')
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '400')

Config.write()

from kivy.app import App
from kivy.lang.builder import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window


kv = '''

MyWindow:

'''

class MyWindow(BoxLayout):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        Window.bind(focus=self.window_focus)

    def window_focus(self, window, focus):
        print('WINDOW FOCUS', focus)
        if focus:
            # is it possible to get touch from window and call on_touch_down?
            pass


    def on_touch_down(self, touch):
        print('TOUCH DOWN')
        return super().on_touch_down(touch)

class MyApp(App):
    def build(self):

        return Builder.load_string(kv)

if __name__ == '__main__':
    MyApp().run()
