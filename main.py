import threading
import kivy_matplotlib_widget
import matplotlib.pyplot as plt
from datetime import datetime
from kivy.clock import Clock
from kivy.config import ConfigParser
from kivy.properties import ColorProperty
from kivy.core.window import Window
from kivy.uix.vkeyboard import VKeyboard
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFlatButton, MDRectangleFlatIconButton
from kivymd.uix.behaviors.toggle_behavior import MDToggleButton
from kivymd.uix.dialog import MDDialog
from kivy.input.providers.mtdev import MTDMotionEvent
from kivy.input.providers.mouse import MouseMotionEvent

from core import SignalProcessor, Calculator


class PrimaryButton(MDRectangleFlatIconButton): pass


class ChoiceButton(MDRectangleFlatIconButton, MDToggleButton): pass


class PromptContent(BoxLayout): pass


class Prompt(MDDialog):
    ok_action = ObjectProperty()
    pending_value = StringProperty()
    upper_limit = NumericProperty()
    lower_limit = NumericProperty()

    def __init__(self, **kwargs):
        self.screen = MDApp.get_running_app().root.get_screen('modulus')
        self.action = kwargs['ok_action']
        self.type = 'custom'
        self.spacing = 50
        self.pos_hint = {'center_x': .5, 'center_y': 0.8}
        self.content_cls = PromptContent()
        self.content_cls.ids.text_field.text = kwargs['pending_value']
        self.buttons = [
            MDFlatButton(
                text='Cancel',
                theme_text_color='Custom',
                md_bg_color=MDApp.get_running_app().BOLD_RED,
                on_release=lambda _: self.dismiss()
            ),
            MDFlatButton(
                text='OK',
                theme_text_color='Custom',
                md_bg_color=MDApp.get_running_app().SKY_MIST,
                on_release=lambda _: self.validate(
                    self.content_cls.ids.text_field.text.strip(),
                    upper_limit=kwargs['upper_limit'],
                    lower_limit=kwargs['lower_limit']
                )
            )
        ]

        super().__init__(**kwargs)

    def validate(self, value, upper_limit, lower_limit):
        try:
            # Check if value is empty
            if not value.strip():
                self.action('')
            else:
                # Try to convert the value to float
                num_value = float(value)

                # Check if the value is within the specified range
                if num_value < lower_limit:
                    raise ValueError(f"Value must be greater than {lower_limit}.")
                elif num_value > upper_limit:
                    raise ValueError(f"Value must be less than {upper_limit}.")

                # If everything is valid, process the valid number
                self.action(str(num_value))

            # Update the calculation button status
            self.screen.update_calculation_button_status()

        except ValueError as e:
            # Show error message on the text field if there's an exception
            self.content_cls.ids.text_field.focus = True
            self.content_cls.ids.text_field.error = True

            # Display detailed error message based on exception raised
            if str(e).startswith('Value must'):
                self.content_cls.ids.text_field.helper_text = f'* Invalid input! {e}'
            else:
                self.content_cls.ids.text_field.helper_text = '* Invalid input! Please enter a valid number.'


class LabelField(MDTextField):
    dialog_title = StringProperty()
    is_output = BooleanProperty(False)
    upper_limit = NumericProperty()
    lower_limit = NumericProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_touch_down(self, touch):
        # if not self.collide_point(*touch.pos): return
        if isinstance(touch, MouseMotionEvent): return
        if self.is_output: return
        self.prompt = Prompt(
            title=self.dialog_title,
            ok_action=self.ok,
            pending_value=self.text,
            upper_limit=self.upper_limit,
            lower_limit=self.lower_limit
        )
        self.prompt.open()

    def ok(self, value):
        self.text = value
        self.prompt.dismiss()


class EntryBox(MDBoxLayout):
    label = StringProperty('')
    unit = StringProperty('')
    dialog_title = StringProperty('')
    is_output = BooleanProperty(False)
    upper_limit = NumericProperty()
    lower_limit = NumericProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_touch_down(self, touch):
        # if not self.collide_point(*touch.pos): return
        if self.is_output: return
        screen_name = manager.current
        screen = manager.get_screen(screen_name)

        if screen_name == 'modulus':

            clavius = manager.get_screen('clavius')

            clavius.active_tab = self.label[:-2]

            tab = screen.ids.tab_container.get_current_tab().title

            clavius.fields = []

            if tab == 'BAR':
                clavius.fields = [
                    (screen.ids.bar_length, screen.ids.bar_length.ids.label_field.text),
                    (screen.ids.bar_width, screen.ids.bar_width.ids.label_field.text),
                    (screen.ids.bar_thickness, screen.ids.bar_thickness.ids.label_field.text),
                    (screen.ids.bar_mass, screen.ids.bar_mass.ids.label_field.text),
                    (screen.ids.bar_flexural_frequency, screen.ids.bar_flexural_frequency.ids.label_field.text),
                    (screen.ids.bar_torsional_frequency, screen.ids.bar_torsional_frequency.ids.label_field.text),
                    (screen.ids.bar_initial_poisson_ratio, screen.ids.bar_initial_poisson_ratio.ids.label_field.text),
                ]
            elif tab == 'ROD':
                clavius.fields = [
                    (screen.ids.rod_length, screen.ids.rod_length.ids.label_field.text),
                    (screen.ids.rod_diameter, screen.ids.rod_diameter.ids.label_field.text),
                    (screen.ids.rod_mass, screen.ids.rod_mass.ids.label_field.text),
                    (screen.ids.rod_flexural_frequency, screen.ids.rod_flexural_frequency.ids.label_field.text),
                    (screen.ids.rod_torsional_frequency, screen.ids.rod_torsional_frequency.ids.label_field.text),
                    (screen.ids.rod_initial_poisson_ratio, screen.ids.rod_initial_poisson_ratio.ids.label_field.text),
                ]
            elif tab == 'DISC':
                clavius.fields = [
                    (screen.ids.disc_diameter, screen.ids.disc_diameter.ids.label_field.text),
                    (screen.ids.disc_thickness, screen.ids.disc_thickness.ids.label_field.text),
                    (screen.ids.disc_mass, screen.ids.disc_mass.ids.label_field.text),
                    (screen.ids.disc_first_frequency, screen.ids.disc_first_frequency.ids.label_field.text),
                    (screen.ids.disc_second_frequency, screen.ids.disc_second_frequency.ids.label_field.text),
                ]

            manager.current = 'clavius'
            manager.transition.direction = 'down'


class ConfigManager:
    def __init__(self, filename='settings.ini'):
        self.config = ConfigParser()
        self.filename = filename
        self.config.read(self.filename)

    def get(self, section, key, fallback=None):
        try:
            return self.config.get(section, key)
        except:
            return fallback

    def getint(self, section, key, fallback=0):
        try:
            return self.config.getint(section, key)
        except:
            return fallback

    def getboolean(self, section, key, fallback=False):
        try:
            return self.config.getboolean(section, key)
        except:
            return fallback

    def set(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        self.save()

    def save(self):
        with open(self.filename, 'w') as configfile:
            self.config.write()


class Panel(MDBoxLayout):
    left_icon = StringProperty()
    left_label = StringProperty()
    left_action = ObjectProperty()

    right_icon = StringProperty()
    right_label = StringProperty()
    right_action = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_interval(self.update_datetime, 1)

    def update_datetime(self, dt):
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M:%S')
        self.ids.date_label.text = current_date
        self.ids.time_label.text = current_time


class Navigator(MDScreenManager):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.config_manager = ConfigManager()
        self.calculator = Calculator()

        self.default = self.config_manager.get(
            'SIET1010', 'archive_path', fallback='Archive/SIET1010'
        )

    def on_touch_down_bak(self, touch):
        if self.collide_point(*touch.pos):
            if not isinstance(touch, MouseMotionEvent):
                super().on_touch_down(touch)

    def back(self, direction):
        self.current = 'home'
        self.transition.direction = direction


class Main(MDApp):
    VOID_BLACK = ColorProperty((0, 0, 0, 1))
    PURE_LIGHT = ColorProperty((1, 1, 1, 1))
    STALE_BLUE = ColorProperty((0.23, 0.29, 0.36, 1))
    STALE_GRAY = ColorProperty((0.85, 0.85, 0.90, 1))
    VIBRANT_GREEN = ColorProperty((0.28, 0.73, 0.31, .5))
    BOLD_RED = ColorProperty((0.73, 0.23, 0.23, .5))
    SKY_MIST = ColorProperty((0.55, 0.6, 0.7, 1))


    def on_start(self):
        Window.borderless = True
        Window.size = (1024, 600)

    def stop_recording(self):
        self._stop_recording.set()

    def start_recording(self):
        self._stop_recording.clear()
        self._recording_thread = threading.Thread(
            target=self.signal_processor.run,
            args=(self._stop_recording, self.update_ui),
            daemon=True
        )
        self._recording_thread.start()

    def update_ui(self, success, signal, peaks, importing=False):
        self.main_peak = peaks[0]
        home_screen = self.root.get_screen('home')
        if importing:
            home_screen.calculation_btn.disabled = False
            home_screen.show_fft_btn.disabled = False
            home_screen.show_wave_btn.disabled = False
        if len(signal) > 0 and len(peaks) > 0:
            home_screen.set_peaks(peaks)
        if not importing:
            home_screen.start_stop(success)

    def build(self):
        global manager
        manager = Navigator(self)
        VKeyboard.layout_path = 'keyboards'
        VKeyboard.layout = 'minimal'
        self.signal_processor = SignalProcessor(manager)
        self._stop_recording = threading.Event()
        return manager


if __name__ == '__main__':
    Window.borderless = True
    Window.size = 900, 500
    Main().run()

