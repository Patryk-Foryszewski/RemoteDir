from kivy.uix.boxlayout import BoxLayout
from common import get_config, mk_logger, config_file
from associationrow import AssociationRow

logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


class Associations(BoxLayout):
    name = 'Associations'
    tags = ['associations']

    def __init__(self):
        super().__init__()
        self.section = 'ASSOCIATIONS'
        self.associations = None
        self.fill()

    def fill(self):
        self.clear_associations()
        try:
            config = get_config()
        except Exception as ex:
            ex_log(f'Could not read config {ex}')
        else:
            if config.has_section(self.section):
                self.associations = dict(config.items(self.section))
                for asociation in self.associations.items():
                    extension = asociation[0]
                    path, params = asociation[1].split('#')
                    self.show_association(extension, path, params)

    def add_association(self, row=None):
        config = get_config()
        association = row.get_association()
        if association:
            extension, path, params = row.get_association()
        else:
            return

        if not config.has_section(self.section):
            config.add_section(self.section)

        self.associations = dict(config.items(self.section))
        value = f'{path}#{params}'
        config.set(self.section, extension, value)

        with open(config_file, 'w+') as f:
            config.write(f)

    def clear_associations(self):
        self.ids.associations_space.clear_widgets()

    def show_association(self, extension='', path='', params='', row=None):
        if row:
            extension, path, params = row.get_association()
        ast = AssociationRow(extension, path, params)
        self.ids.associations_space.add_widget(ast)

    def save(self):
        print('SAVE ASSOTIATIONS CONFIG')
        config = get_config()
        if config:
            config.remove_section(self.section)
            with open(config_file, 'w+') as f:
                config.write(f)               
            print('     ROWS', len(self.ids.associations_space.children))
            for association_row in self.ids.associations_space.children:
                association = association_row.get_association()
                print('     ASSOCIATION', association)
                if association:
                    self.add_association(association_row)

    def on_dismiss(self):
        self.save()
