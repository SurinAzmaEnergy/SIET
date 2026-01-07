from kivy.properties import StringProperty, NumericProperty
from kivymd.uix.button import MDButton, MDIconButton


class TextIconButton(MDButton):
    text = StringProperty()
    icon = StringProperty()
    text_font_size = NumericProperty(25)
    icon_font_size = NumericProperty(25)


class IconButton(MDIconButton):
    icon = StringProperty()
