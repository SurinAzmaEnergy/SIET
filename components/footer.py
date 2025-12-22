# from datetime import datetime
# from kivy.clock import Clock
from kivy.properties import StringProperty, ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout


class Footer(MDBoxLayout):
    left_icon = StringProperty()
    left_label = StringProperty()
    left_action = ObjectProperty()
    right_icon = StringProperty()
    right_label = StringProperty()
    right_action = ObjectProperty()
