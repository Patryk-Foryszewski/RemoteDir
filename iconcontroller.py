from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from pathvalidate import ValidationError, validate_filename
from common import get_progid, convert_file_size, unix_time, forbidden_names, find_thumb, posix_path
from kivy.clock import Clock


class IconController(BoxLayout):

    filename = StringProperty()
    date_added = StringProperty()
    date_modified = StringProperty()
    focus = BooleanProperty()
    image = StringProperty()
    description = StringProperty()
    filesize = StringProperty()

    def __init__(self, attrs, file_type, space, **kwargs):
        super().__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self.key_press, self)
        self._keyboard.bind(on_key_down=self.key_press)
        self._keyboard.bind(on_key_up=self.key_up)
        self.attrs = attrs
        self.filename = self.attrs.filename
        self.path = attrs.path
        self.date_added = unix_time(attrs.st_atime)
        self.date_modified = unix_time(attrs.st_mtime)
        self.space = space
        self.filesize = convert_file_size(attrs.st_size)
        self.focus = False
        self.file_type = file_type
        self.description = self.get_description()
        self.previous_touch = None
        self.collided = False
        self.pressed_key = ''
        self.counter = 0
        self.set_thumbnail()

    @classmethod
    def from_attrs(cls, attrs, space):
        if attrs.longname[0] == 'd':
            file_type = 'dir'
        else:
            file_type = 'file'
        return cls(attrs=attrs, file_type=file_type, space=space)

    @classmethod
    def unfocus(cls):
        cls.focus = False

    def set_thumbnail(self):
        image = None
        if self.attrs.thumbnail:
            image = find_thumb(self.path, self.filename)

        if image:
            self.image = image
        elif self.file_type == 'dir':
            self.image = 'img/dir.png'
        else:
            self.image = 'img/unknown.png'
        self.ids.image.reload()

    def get_description(self):
        if self.file_type == 'dir':
            return 'Directory'
        else:
            return get_progid(self.filename)

    def key_up(self, *args):
        self.pressed_key = None

    def key_press(self, *args):
        if len(args) == 4:
            self.pressed_key = args[1][1]
            if self.focus:
                if self.pressed_key == 'enter':
                    self.on_enter()

    def on_enter(self):
        """
        Mehtod that allows to have multiline textinput and validate on enter
        """
        if self.ids.filename.focus:
            self.rename_file(self.ids.filename.text.replace('\n', ''))
        elif self.focus:
            self.space.open_file(self)

    def filename_valid(self, text):

        error = ''
        # noinspection PyBroadException
        try:
            if text in forbidden_names:
                return ValidationError(description=f'Forbidden name {text}')

            validate_filename(text)

        except ValidationError as ve:
            if ve.description is not None:
                error = 'Could not change filename.\n\nReason: {}'.format(ve.description)
            elif len(ve.args):
                error = 'Could not change filename.\n\nReason: {}'.format(ve.args[0])
            else:
                error = 'Could not change filename.\n\nReason: {}'.format(ve.reason)
        except Exception as ex:
            error = f'Unknown exception: {ex}'

        finally:
            if error:
                return False
            else:
                return True

    def rename_file(self, text):
        print('RENAME FILE')
        self.ids.filename.disabled = True
        self.ids.filename.focus = False
        self.space.on_popup_dismiss()
        if not self.filename_valid(text):
            return
        if text != self.filename:
            full_old_path = posix_path(self.path, self.filename)
            full_new_path = posix_path(self.path, text)

            self.space.rename_file(full_old_path, full_new_path, file=self)
            self.ids.filename.disabled = True
            self.focus = False

    def enable_rename(self):
        self.space.on_popup()
        def delay(_):
            self.ids.filename.disabled = False
            self.ids.filename.focus = True
        Clock.schedule_once(delay, 0.3)

    def on_touch_down(self, touch):

        if self.collide_point(*touch.pos) and not self.pressed_key:
            self.counter += 1
            if not self.focus:
                self.enabled_rename = False
                self.focus = True
        else:
            self.counter = 0

        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        # print('TOUCH UP FBX', touch.button)
        # Because on_touch_up is fired few times on each FileBox. This is issue to be solved
        if self.ids.filename.collide_point(*touch.pos) and not self.pressed_key:

            if self.focus \
                    and touch.button == 'left'\
                    and not touch.is_double_tap\
                    and not self.space.moving\
                    and len(self.space.marked_files) == 1\
                    and self.counter == 2:
                self.enable_rename()
        else:
            self.ids.filename.disabled = True

        if self.previous_touch == touch:
            return
        self.previous_touch = touch
        if self.collide_point(*touch.pos) and self.focus:
            # print('  FOCUSED FILEBOX', self.filename)
            for file in self.space.children:
                if file is not self and file.collide_point(*touch.pos):
                    # print('COLLIDED', file.filename, file.file_type, self.filename, self.file_type)
                    if file.file_type == 'dir':
                        self.space.internal_file_drop(file)
                        break
            else:
                # do layout if moved file is not dropped on directory
                self.space.do_layout()

        # Dispatch touch event to the rest of the widget tree
        return super().on_touch_up(touch)

    def collide_rectangle(self, x, y, right, top):
        # _x = x if x < right else right
        # _y = y if y < top else top
        # _right = right if right > x else x
        # _top = top if top > y else y
        _x = min(x, right)
        _y = min(y, top)
        _right = max(x, right)
        _top = max(y, top)

        if self.right < _x:
            return False
        if self.x > _right:
            return False
        if self.top < _y:
            return False
        if self.y > _top:
            return False
        return True
