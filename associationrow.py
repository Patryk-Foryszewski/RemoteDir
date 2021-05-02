from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty


class AssociationRow(BoxLayout):
    extension = StringProperty('.')
    path = StringProperty()
    params = StringProperty()

    def __init__(self,  extension='.', path='', params='', **kwargs):
        super().__init__(**kwargs)
        self.section = 'ASSOCIATIONS'
        self.extension = extension
        self.path = path
        self.params = params
        self.fill(extension, path, params)

    def fill(self, extension, path, params):
        self.extension = extension
        self.path = path
        self.params = params

    def get_association(self):
        if self.extension and (self.path or self.params):
            return self.extension, self.path, self.params
        else:
            return None
