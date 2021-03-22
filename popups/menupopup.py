from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from common import button_height
from kivy.core.window import Window
from colors import colors
from kivy.properties import NumericProperty


class MenuPopupBtn(Button):

    def __init__(self, menupopup, callback=None, **kwargs):
        super(MenuPopupBtn, self).__init__(**kwargs)
        self.bind(on_touch_down=self.pressed)
        self.callback = callback
        self.menupopup = menupopup
        self.width = self.menupopup.width
        Window.bind(mouse_pos=self.light_up)

    def light_up(self, _, mouse_pos):
        x, y = self.to_widget(*mouse_pos)
        if self.collide_point(x, y):
            self.background_color = colors['context_menu_active_btn']
        else:
            self.background_color = colors['context_menu_normal_btn']

    def pressed(self, *args):
        if self.callback and args[1].button == 'left' and self.collide_point(*args[1].pos):
            self.callback(self.text)
        self.menupopup.dismiss()


class MenuPopup(ModalView):
    spacing = NumericProperty(1)
    # MenuPopup & ButtonSpace

    def __init__(self, buttons, originator, callback=None, widget=None, mouse_pos=None, **kwargs):
        super().__init__(**kwargs)

        self.originator = originator
        self.buttons = buttons
        self.callback = callback
        self.fill()
        self.widget = widget
        self.mouse_pos = mouse_pos
        self.set_width()
        self.set_pos_hint()

    def fill(self):
        for btn in self.buttons:
            button = MenuPopupBtn(self, callback=self.callback)
            button.text = btn
            self.ids.buttons_space.add_widget(button)

    def on_dismiss(self):
        self.originator.on_popup_dismiss()

    def set_width(self):
        widths = []
        for button in self.ids.buttons_space.children:
            button.texture_update()
            widths.append(button.texture_size[0])

        widest = max(widths)
        if widest > self.width:
            self.width = widest + 6
        for button in  self.ids.buttons_space.children:
            button.width = self.width

    def set_pos_hint(self):

        window_width = Window.width
        if self.mouse_pos:
            x, y = self.mouse_pos
            pos_x = x
            if pos_x + self.width > window_width:
                halign = 'right'
            else:
                halign = 'x'
        else:
            print('WIDGET', self.widget.pos)
            x, y = self.widget.to_window(*self.widget.pos)
            pos_x = self.widget.get_right()
            width = self.widget.width
            # if a widget is on the left side of window attach menu to its left else to right
            if x > window_width / 2:
                pos_x = self.widget.get_right()
                halign = 'right'
            else:
                pos_x = x
                halign = 'right'

        window_height = Window.height
        self.height = len(self.buttons) * (button_height + self.spacing)

        # if menu fits under the widget show under else pop where more space
        space_below = y - self.height
        if space_below > 0:
            pos_y = y
            valign = 'top'
        elif window_height - y > self.height:
            pos_y = y
            valign = 'bottom'
        else:
            pos_y = 10
            valign = 'bottom'

        pos_x = pos_x / window_width
        pos_y = pos_y / window_height
        self.pos_hint = {halign: pos_x, valign: pos_y}
