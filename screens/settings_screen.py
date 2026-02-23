import os
import shutil
import subprocess
import threading
import socket
from datetime import datetime
from kivy.clock import mainthread
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.label import MDLabel
from kivy.input.providers.mouse import MouseMotionEvent


class SecondaryButton(MDFlatButton):

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if not isinstance(touch, MouseMotionEvent):
                super().on_touch_down(touch)


class Updater:
    def __init__(self, clone_dir):
        self.clone_dir = clone_dir

        self.update_dialog = MDDialog(
            title='Update',
            text='The app is updating itself. Do not close the app!',
            buttons=[
                MDFlatButton(
                    text='OK',
                    on_release=lambda _: self.update_dialog.dismiss()
                )
            ]
        )

    def update(self):
        if not self._check_internet_connection():
            self.update_dialog.text = 'No internet connection. Please check your network.'
            self.update_dialog.open()
            return
        threading.Thread(target=self._perform_update, daemon=True).start()
        self.update_dialog.open()

    def _perform_update(self):
        try:
            self._clone_or_pull_repo()
            self._install_dependencies()
        except Exception as e:
            print(f"Update failed: {e}")

    def _clone_or_pull_repo(self):
        self.update_dialog.text = 'Pulling from GitHub!'
        os.system('git stash')
        os.system('git pull')

    def _install_dependencies(self):
        requirements_path = os.path.join(self.clone_dir, "requirements.txt")
        if os.path.exists(requirements_path):
            print("Installing dependencies...")
            self.update_dialog.text = 'Installing the Dependencies!'
            subprocess.run(["pip", "install", "-r", requirements_path], check=True)
        else:
            print("No requirements.txt found, skipping dependency installation.")

        self.update_dialog.text = 'Done!'

    def _check_internet_connection(self):
        try:
            # Try to connect to a reliable server (Google DNS).
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except socket.error as e:
            self.update_dialog.text = f'Network error: {e}. Please check your network.'
            self.update_dialog.open()
            return False


class SetTimeContent(BoxLayout): pass


class SetDateContent(BoxLayout): pass


class GeneralSettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self):
        self.low_frequency = float(self.manager.config_manager.get(
            'SIET1010',
            'low_frequency'
        ))
        self.high_frequency = float(self.manager.config_manager.get(
            'SIET1010',
            'high_frequency'
        ))
        self.update_label('low_freq_label', self.low_frequency)
        self.ids.low_freq.value = self.low_frequency
        self.update_label('high_freq_label', self.high_frequency)
        self.ids.high_freq.value = self.high_frequency
        self.all_pass_value = self.manager.config_manager.getboolean(
            'SIET1010',
            'all_pass'
        )
        self.ids.all_pass_btn.icon = 'check' if self.all_pass_value else 'close'
        self.all_pass()

    def open_save_dialog(self):
        self.save_dialog = MDDialog(
            title='Done!',
            buttons=[
                SecondaryButton(
                    text='OK',
                    text_color=self.theme_cls.primary_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.save_dialog.dismiss()
                )
            ]
        )
        self.save_dialog.open()

    def save(self):
        self.manager.config_manager.set(
            'SIET1010', 'all_pass', self.is_checked
        )
        self.manager.config_manager.set(
            'SIET1010', 'low_frequency', round(self.ids.low_freq.value, 2)
        )
        self.manager.config_manager.set(
            'SIET1010', 'high_frequency', round(self.ids.high_freq.value, 2)
        )
        self.manager.config_manager.save()
        self.open_save_dialog()

    def update_label(self, label, value):
        if label == 'low_freq_label':
            self.ids.low_freq_label.text = f'Low Frequency: {value:.2f} kHz'
            self.ids.high_freq.min = value + 1
            self.ids.high_freq_min.text = f'Min: {int(value) + 1} kHz'
        else:
            self.ids.high_freq_label.text = f'High Frequency: {value:.2f} kHz'
            self.ids.low_freq.max = value - 1
            self.ids.low_freq_max.text = f'Max: {int(value) - 1} kHz'

    def all_pass(self):
        is_checked = self.ids.all_pass_btn.icon == 'check'
        self.is_checked = is_checked
        self.ids.all_pass_btn.icon = 'close' if is_checked else 'check'
        bg_color = self.manager.app.STALE_BLUE if is_checked else self.manager.app.PURE_LIGHT
        text_color = self.manager.app.PURE_LIGHT if is_checked else self.manager.app.VOID_BLACK
        opacity = .6 if is_checked else 1
        disabled = is_checked
        self.ids.all_pass_btn.md_bg_color = bg_color
        self.ids.all_pass_btn.text_color = text_color
        self.ids.all_pass_btn.icon_color = text_color
        self.ids.frequencies_label.opacity = opacity
        self.ids.low_freq.disabled = disabled
        self.ids.high_freq.disabled = disabled

    def open_set_time_dialog(self):
        self.set_time_dialog = MDDialog(
            title='Set Time',
            type='custom',
            pos_hint={'center_x': .5, 'center_y': .8},
            content_cls=SetTimeContent(),
            buttons=[
                SecondaryButton(
                    text='CANCEL',
                    text_color=self.theme_cls.error_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.set_time_dialog.dismiss()
                ),
                SecondaryButton(
                    text='OK',
                    text_color=self.theme_cls.primary_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.apply_time()
                )
            ]
        )
        self.set_time_dialog.open()

    def apply_time(self):
        current_date = datetime.now().date()

        content = self.set_time_dialog.content_cls
        if hasattr(self, 'error_label'):
            content.remove_widget(self.error_label)
        self.error_label = MDLabel(id='error_msg', theme_text_color='Custom', text_color=(1, 0, 0, 1))
        hour_str = self.set_time_dialog.content_cls.ids.hour_field.text.strip()
        minute_str = self.set_time_dialog.content_cls.ids.minute_field.text.strip()
        second_str = self.set_time_dialog.content_cls.ids.second_field.text.strip()


        # Step 2: Validate numeric input
        if not (hour_str.isdigit() and minute_str.isdigit() and second_str.isdigit()):
            self.error_label.text = 'Invalid input: All time fields must be numbers.'
            content.add_widget(self.error_label)
            return

        hour = int(hour_str)
        minute = int(minute_str)
        second = int(second_str)

        # Step 3: Validate time ranges
        if not (0 <= hour < 24):
            self.error_label.text = 'Invalid hour: must be 0–23.'
            content.add_widget(self.error_label)
            return
        if not (0 <= minute < 60):
            self.error_label.text = 'Invalid minute: must be 0–59.'
            content.add_widget(self.error_label)
            return
        if not (0 <= second < 60):
            self.error_label.text = 'Invalid minute: must be 0–59.'
            content.add_widget(self.error_label)
            return

        # Step 3: Combine date + new time
        time_str = f"{hour}:{minute}:{second}"
        new_datetime = datetime.strptime(f"{current_date} {time_str}", "%Y-%m-%d %H:%M:%S")

        # Step 4: Format for Linux date command
        formatted_time = new_datetime.strftime("%Y-%m-%d %H:%M:%S")

        print(os.system(f"sudo date -s '{formatted_time}'"))
        # Step 5: Set system time using os.system
        os.system(f"sudo date -s '{formatted_time}'")

        # Optional: sync to RTC using os.system
        os.system("sudo hwclock -w")

        self.set_time_dialog.dismiss()

    def open_set_date_dialog(self):
        self.set_date_dialog = MDDialog(
            title='Set Date',
            type='custom',
            pos_hint={'center_x': .5, 'center_y': .8},
            content_cls=SetDateContent(),
            buttons=[
                SecondaryButton(
                    text='CANCEL',
                    text_color=self.theme_cls.error_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.set_date_dialog.dismiss()
                ),
                SecondaryButton(
                    text='OK',
                    text_color=self.theme_cls.primary_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.apply_date()
                )
            ]
        )
        self.set_date_dialog.open()

    def apply_date(self):

        content = self.set_date_dialog.content_cls

        if hasattr(self, 'date_error_label'):
            content.remove_widget(self.date_error_label)

        self.date_error_label = MDLabel(id='error_msg', theme_text_color='Custom', text_color=(1, 0, 0, 1))

        # Step 1: Get input from text fields
        day_str = self.set_date_dialog.content_cls.ids.day_field.text.strip()
        month_str = self.set_date_dialog.content_cls.ids.month_field.text.strip()
        year_str = self.set_date_dialog.content_cls.ids.year_field.text.strip()

        # Step 2: Validate numeric input
        if not (day_str.isdigit() and month_str.isdigit() and year_str.isdigit()):
            self.date_error_label.text = 'Invalid input: All date fields must be numbers.'
            content.add_widget(self.date_error_label)
            return

        day = int(day_str)
        month = int(month_str)
        year = int(year_str)

        # Step 3: Validate ranges (basic)
        if not (1 <= month <= 12):
            self.date_error_label.text = 'Invalid month: must be 1–12.'
            content.add_widget(self.date_error_label)
            return
        if not (1 <= day <= 31):
            self.date_error_label.text = 'Invalid day: must be 1–31.'
            content.add_widget(self.date_error_label)
            return
        if not (2025 <= year <= 2100):  # Unix time safe range
            self.date_error_label.text = 'Invalid year: must be 2025–2100.'
            content.add_widget(self.date_error_label)
            return

        try:
            # Step 4: Validate full date (e.g., Feb 30 → error)
            new_date = datetime(year, month, day)
        except ValueError as e:
            self.date_error_label.text = 'Invalid Date!'
            content.add_widget(self.date_error_label)
            return

        # Step 5: Get current time
        current_time = datetime.now().time()
        # Step 6: Combine new date with current time
        new_datetime = datetime.combine(new_date, current_time)

        # Step 7: Format for date command
        formatted_datetime = new_datetime.strftime("%Y-%m-%d %H:%M:%S")

        # Step 8: Set system date using os.system
        os.system(f"sudo date -s '{formatted_datetime}'")

        # Optional: sync system date to RTC
        os.system("sudo hwclock -w")

        # Step 9: Dismiss dialog
        self.set_date_dialog.dismiss()

class AdvancedSettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._is_off = True

    def on_enter(self):
        self.resolution = float(self.manager.config_manager.get(
            'SIET1010',
            'resolution'
        ))
        self.update_label('resolution', self.resolution)
        self.ids.resolution_slider.value = self.resolution

        self.sensitivity = float(self.manager.config_manager.get(
            'SIET1010',
            'sensitivity'
        ))
        self.update_label('sensitivity', self.sensitivity)
        self.ids.sensitivity_slider.value = self.sensitivity

        self.distance = float(self.manager.config_manager.get(
            'SIET1010',
            'distance'
        ))
        self.update_label('distance', self.distance)
        self.ids.distance_slider.value = self.distance

    def back_to_general(self):
        self.manager.current = 'general_settings'
        self.manager.transition.direction = 'down'

    def open_save_dialog(self):
        self.save_dialog = MDDialog(
            title='Done!',
            buttons=[
                SecondaryButton(
                    text='OK',
                    text_color=self.theme_cls.primary_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.save_dialog.dismiss()
                )
            ]
        )
        self.save_dialog.open()

    def save(self):
        self.manager.config_manager.set(
            'SIET1010', 'resolution', round(self.ids.resolution_slider.value, 2)
        )
        self.manager.config_manager.set(
            'SIET1010', 'sensitivity', round(self.ids.sensitivity_slider.value, 2)
        )
        self.manager.config_manager.set(
            'SIET1010', 'distance', int(self.ids.distance_slider.value)
        )
        self.manager.config_manager.save()
        self.open_save_dialog()

    def update_label(self, label, value):
        if label == 'resolution':
            self.ids.resolution_label.text = f'Resolution: {value:.1f} Hz'
        elif label == 'sensitivity':
            self.ids.sensitivity_label.text = f'Sensitivity: ± {value:.1f}'
        elif label == 'distance':
            self.ids.distance_label.text = f'Distance: {int(value)} Hz'

    def update(self):
        # Define your repository details
        CLONE_DIR = "/home/pi/SIET1010/"

        updater = Updater(CLONE_DIR)

        updater.update()

    def default(self):
        self.manager.config_manager.set(
            'SIET1010', 'resolution', 1
        )
        self.manager.config_manager.set(
            'SIET1010', 'sensitivity', 2
        )
        self.manager.config_manager.set(
            'SIET1010', 'distance', 100
        )
        self.manager.config_manager.set(
            'SIET1010', 'all_pass', True
        )
        self.manager.config_manager.set(
            'SIET1010', 'low_frequency', 2.0
        )
        self.manager.config_manager.set(
            'SIET1010', 'high_frequency', 10.0
        )
        self.manager.config_manager.save()
        self.on_enter()
