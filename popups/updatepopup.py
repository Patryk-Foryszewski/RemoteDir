from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
import json
from common import mk_logger

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

    def load_changelog(self, changelog):
        try:
            self.changelog = json.loads(changelog)
        except Exception as ex:
            ex_log(f'Failed to load changelog, {ex}')
            self.changelog = 'Failed to read changelog'

    @staticmethod
    def on_answer(_):
        return ()
