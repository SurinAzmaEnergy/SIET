import subprocess
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.screen import MDScreen


class HomeScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.recording = False

    def on_kv_post(self, base):
        self.set_peaks()
        self.calculation_btn = self.ids.calculation_btn
        self.archive_btn = self.ids.archive_btn
        self.show_fft_btn = self.ids.show_fft_btn
        self.show_wave_btn = self.ids.show_wave_btn
        self.settings_btn = self.ids.home_panel.ids.right_button
        self.start_stop_btn = self.ids.start_stop_btn
        self.state_card = self.ids.state_card
        self.state_label = self.ids.state_label

    def set_peaks(self, peaks=[]):
        widgets = [
            self.ids.first_peak,
            self.ids.second_peak,
            self.ids.third_peak
        ]
        labels = [
            'First Peak:',
            'Second Peak:',
            'Third Peak:'
        ]

        if len(peaks) == 0:
            for widget, label in zip(widgets, labels):
                widget.text = f"{label:<15} --- {'':<2}kHz"
        else:
            for widget, label, peak in zip(widgets, labels, peaks):
                if isinstance(peak, float):
                    peak /= 1000
                    widget.text = f"{label:<13} {peak:.4f} {'':<2}kHz"
                else:
                    widget.text = f"{label:<15} --- {'':<2}kHz"

    def start_stop(self, success):
        if self.recording:
            self.update_start_stop_button(
                'Start',
                'microphone-outline',
                self.manager.app.PURE_LIGHT,
            )

            if success:
                self.calculation_btn.disabled = False
                self.show_fft_btn.disabled = False
                self.show_wave_btn.disabled = False
            self.archive_btn.disabled = False
            self.settings_btn.disabled = False

            self.manager.app.stop_recording()

        else:
            self.set_peaks()
            self.update_start_stop_button(
                'Stop',
                'stop-circle-outline',
                self.manager.app.BOLD_RED,
            )

            self.archive_btn.disabled = True
            self.calculation_btn.disabled = True
            self.settings_btn.disabled = True
            self.show_fft_btn.disabled = True
            self.show_wave_btn.disabled = True

            self.manager.app.start_recording()

        self.recording = not self.recording

    def update_start_stop_button(
        self,
        btn_text,
        icon,
        btn_color,
    ):
        self.start_stop_btn.text = btn_text
        self.start_stop_btn.icon = icon
        self.start_stop_btn.md_bg_color = btn_color

    def open_settings(self):
        self.manager.current = 'general_settings'
        self.manager.transition.direction = 'up'

    def reboot(self):
        self.reboot_dialog = MDDialog(
            title='Are you sure you want to reboot?',
            text='Warning: Unsaved work will be lost and cannot be recovered!',
            buttons = [
                MDFlatButton(
                    text='Cancel',
                    theme_text_color='Custom',
                    md_bg_color=MDApp.get_running_app().BOLD_RED,
                    on_release=lambda _: self.reboot_dialog.dismiss()
                ),
                MDFlatButton(
                    text='OK',
                    theme_text_color='Custom',
                    md_bg_color=MDApp.get_running_app().SKY_MIST,
                    on_release=lambda _: self.sudo_reboot()
                )
            ]
        )
        self.reboot_dialog.open()

    def sudo_reboot(self):
        try:
            self.reboot_dialog.dismiss()
            subprocess.run(["sudo", "reboot"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

