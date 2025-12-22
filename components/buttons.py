from kivy.properties import StringProperty
from kivymd.uix.button import MDButton


class TextIconButton(MDButton):
    text = StringProperty()
    icon = StringProperty()
