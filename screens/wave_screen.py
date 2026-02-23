import os
from datetime import datetime
import numpy as np
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFlatButton


class WaveScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self):
        self.ids.wave_widget.figure = self.manager.app.signal_processor.plot_wave()

    def open_save_dialog(self):
        current_time = datetime.now()
        file_name = current_time.strftime(f"SIET1010_%Y-%m-%d_%H-%M-%S_WAVE.csv")
        self.save_dialog = MDDialog(
            title='File Name:',
            type='custom',
            pos_hint={'center_x': .5, 'center_y': 0.8},
            content_cls=MDTextField(
                text=file_name,
                icon_left='rename-box-outline'
            ),
            buttons=[
                MDFlatButton(
                    text='CANCEL',
                    text_color=self.theme_cls.error_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.save_dialog.dismiss()
                ),
                MDFlatButton(
                    text='OK',
                    text_color=self.theme_cls.primary_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.save(
                        self.save_dialog.content_cls.text
                    )
                )
            ]
        )
        self.save_dialog.open()

    def save(self, name):
        np.savetxt(
            os.path.join(self.manager.default, name),
            np.column_stack((
                self.manager.app.signal_processor.time_ms,
                self.manager.app.signal_processor.normalized_signal
            )),
            header='Time,Signal',
            comments='# WAVEFORM\n',
            delimiter=',',
            fmt='%.5f' # It might reduce the accuracy!
        )
        self.save_dialog.dismiss()

