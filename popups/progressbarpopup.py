from kivy.uix.boxlayout import BoxLayout
from common import mk_logger

logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


class ThumbnailPopup(BoxLayout):
    def __init__(self):
        super().__init__()

