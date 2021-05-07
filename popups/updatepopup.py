from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.clock import Clock
import json
from common import mk_logger
from functools import partial

logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


class UpdatePopup(BoxLayout):
    changelog = StringProperty()

    def __init__(self, changelog, **kwargs):
        self.register_event_type('on_answer')
        super().__init__(**kwargs)
        self.load_changelog(changelog)

    def installing(self, i, *_):
        text = f'Installing{i*"."}'
        self.ids.yes.text = text
        if i == 3:
            i = 0
        else:
            i+=1
        Clock.schedule_once(partial(self.installing, i), 0.5)

    def load_changelog(self, changelog):
        try:
            self.changelog = json.loads(changelog)
        except Exception as ex:
            ex_log(f'Failed to load changelog, {ex}')
            self.changelog = 'Failed to read changelog'

    def on_answer(self, *args):
        print('UPDATE POPUP', args)
        if args[0] == 'yes':
            self.ids.yes.halign = 'left'
            self.installing(0)
        return ()
