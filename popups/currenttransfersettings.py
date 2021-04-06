from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty
from kivy.uix.popup import Popup
from kivy.clock import Clock


class CurrentTransferSettings(BoxLayout):

    #transfer_list = ListProperty([])

    def __init__(self, manager, transfer_list):
        super().__init__()
        self.manager = manager
        self.transfer_list = transfer_list
        self.pop_me()

    def on_transfer_list(self):
        print('NEW TRANSFER', len(self.transfer_list))

    def pop_me(self):
        def pop(_):
            content = self
            self.popup = Popup(
                title=f'Set default action to perform if file already exists',
                auto_dismiss=True,
                content=content,
                size_hint=(0.7, 0.7))

            self.popup.open()

        Clock.schedule_once(pop, .1)