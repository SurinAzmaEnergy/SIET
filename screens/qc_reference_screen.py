import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField


class ReferenceSetScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self):
        self.display_slot_id()
        self.display_slot_name()
        imported = self.import_reference()
        print(f'Imported: {imported}')
        self.update_buttons_state(imported=imported, started=False)

    def update_buttons_state(self, imported, started):
        if imported:
            print('It is imported, but Not started')
            self.ids.set_ref.disabled = True
            self.ids.ref_export.disabled = True
            self.ids.reset_slot.disabled = False
        elif started:
            print('Not imported, but it is started')
            self.ids.set_ref.disabled = False
            self.ids.ref_export.disabled = False
        else:
            print('Not imported, Not started')
            self.ids.set_ref.disabled = True
            self.ids.ref_export.disabled = True
            self.ids.reset_slot.disabled = True

    def display_slot_id(self):
        self.slot_id = self.manager.metadata_manager.current
        self.ids.slot_id.text = f'Reference #{self.slot_id}'

    def display_slot_name(self):
        self.slot_id = self.manager.metadata_manager.current
        self.slot_name = self.manager.metadata_manager.get(
            self.slot_id - 1,
            'name'
        )
        self.ids.slot_name.text = self.slot_name

    def start(self):
        self.start_btn = self.ids.ref_start
        home_screen = self.manager.get_screen('home')
        home_screen.start_stop(False)

        self.start_btn.disabled = True
        self.start_btn.text = 'Recording...'

        Clock.schedule_interval(
            self.check_recording_finished,
            0.1
        )

        self.update_buttons_state(imported=False, started=True)

    def check_recording_finished(self, dt):
        thread = self.manager.app._recording_thread

        if not thread.is_alive():
            self.start_btn.disabled = False
            self.start_btn.text = 'Start'

            self.ids.ref_plot.figure = (
                self.manager.app.signal_processor.plot_fft()
            )

            return False  # stop checking

    def open_general_settings(self):
        self.manager.settings_caller = 'reference_set'
        self.manager.current = 'general_settings'
        self.manager.transition.direction = 'up'

    def rename_slot(self, name):
        self.manager.metadata_manager.put(self.slot_id - 1, 'name', name)
        self.rename_dialog.dismiss()
        self.display_slot_name()

    def show_rename_dialog(self):
        self.rename_dialog = MDDialog(
            title='Rename',
            type='custom',
            pos_hint={'center_x': .5, 'center_y': 0.8},
            content_cls=MDTextField(
                mode='round',
                text=self.slot_name
            ),
            buttons=[
                MDFlatButton(
                    text='CANCEL',
                    text_color=self.theme_cls.primary_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.rename_dialog.dismiss()
                ),
                MDFlatButton(
                    text='OK',
                    text_color=self.theme_cls.primary_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.rename_slot(
                        self.rename_dialog.content_cls.text
                    )
                )
            ]
        )
        self.rename_dialog.open()

    def show_save_dialog(self):
        current_time = datetime.now()
        file_name = current_time.strftime(f"SIET1010_%Y-%m-%d_%H-%M-%S_REF.csv")
        self.save_dialog = MDDialog(
            title="File Name:",
            type="custom",
            pos_hint={"center_x": 0.5, "center_y": 0.8},
            content_cls=MDTextField(text=file_name, icon_left="rename-box-outline"),
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    text_color=self.theme_cls.error_color,
                    theme_text_color="Custom",
                    on_release=lambda _: self.save_dialog.dismiss(),
                ),
                MDFlatButton(
                    text="OK",
                    text_color=self.theme_cls.primary_color,
                    theme_text_color="Custom",
                    on_release=lambda _: self.save(self.save_dialog.content_cls.text),
                ),
            ],
        )
        self.save_dialog.open()

    def save(self, name, path=None):
        if path is None:
            path = self.manager.default
        sp = self.manager.app.signal_processor

        # Use only positive frequencies
        freq = sp.fft_freqs[:len(sp.fft_data)]
        mag = np.abs(sp.fft_data[:len(sp.fft_data)])

        # Normalize magnitude (optional, like in your plots)
        mag = mag / np.max(mag)

        # Stack and save
        np.savetxt(
            os.path.join(path, name),
            np.column_stack((freq, mag)),
            header='Frequency,Amplitude',
            comments='# Frequency Spectrum\n',
            delimiter=',',
            fmt='%.5f'
        )
        if getattr(self, "save_dialog", None):
            self.save_dialog.dismiss()

    def set_reference(self):

        sp = self.manager.app.signal_processor

        resolution = self.manager.config_manager.get(
            'SIET1010',
            'resolution'
        )

        all_pass = self.manager.config_manager.get(
            'SIET1010',
            'all_pass'
        )

        low_frequency = self.manager.config_manager.get(
            'SIET1010',
            'low_frequency'
        )
        high_frequency = self.manager.config_manager.get(
            'SIET1010',
            'high_frequency'
        )

        slot_path = Path(f'Archive/QCT/SLOT{self.slot_id}/')

        # Existing reference files
        old_refs = list(slot_path.glob("*_REF.csv"))

        current_time = datetime.now()
        file_name = current_time.strftime(
            f"SIET1010_%Y-%m-%d_%H-%M-%S_S{self.slot_id}_REF.csv"
        )

        # Compose the path
        full_path = os.path.join(slot_path, file_name)

        # Write the file in the slot
        self.save(file_name, slot_path)

        # Put the path, range, and resolution in the metadata
        self.manager.metadata_manager.put(
            self.slot_id-1,
            'reference',
            full_path,
        )

        self.manager.metadata_manager.put(
            self.slot_id-1,
            'resolution',
            resolution,
        )

        all_pass = all_pass == 'True'

        if all_pass:
            print('All Pass is True!')
            self.manager.metadata_manager.put(
                self.slot_id-1,
                'low_frequency',
                0.02,
            )
            self.manager.metadata_manager.put(
                self.slot_id-1,
                'high_frequency',
                24.0,
            )
        else:
            print('All Pass is NOT True!')
            print(low_frequency)
            print(high_frequency)
            self.manager.metadata_manager.put(
                self.slot_id-1,
                'low_frequency',
                low_frequency,
            )
            self.manager.metadata_manager.put(
                self.slot_id-1,
                'high_frequency',
                high_frequency,
            )

        self.manager.metadata_manager.put(
            self.slot_id-1,
            'peaks',
            sp.peaks_for_qct.tolist(), # it happen here...
        )

        # Removes the previous reference files
        for ref_file in old_refs:
            ref_file.unlink()

        # Show the success message
        success_dialog = MDDialog(
            title='Reference Set',
            text=full_path,
            buttons=[MDFlatButton(
                text='OK',
                # Only available KivyMD 1.2.0!
                text_color=self.theme_cls.primary_color,
                theme_text_color='Custom',
                on_release=lambda _: success_dialog.dismiss()
            )]
        )

        success_dialog.open()

        self.ids.reset_slot.disabled = False

    def import_reference(self):

        resolution = self.manager.metadata_manager.get(
            self.slot_id-1,
            'resolution'
        )

        low_frequency = self.manager.metadata_manager.get(
            self.slot_id-1,
            'low_frequency'
        )

        high_frequency = self.manager.metadata_manager.get(
            self.slot_id-1,
            'high_frequency'
        )

        print(f'Resolution: {resolution}')
        print(f'Low Frequency: {low_frequency}')
        print(f'High Frequency: {high_frequency}')

        info = (
            f"Resolution: {resolution} Hz\n"
            f"Range: {low_frequency} - {high_frequency} Hz"
        )

        ref_path = self.manager.metadata_manager.get(
            self.slot_id-1,
            'reference'
        )
        peaks_idx = self.manager.metadata_manager.get(
            self.slot_id-1,
            'peaks'
        )

        if ref_path == '': # Or the file did not exist!
            self.ids.ref_plot.figure = self.manager.app.qct.plot()
            return False

        if not os.path.exists(ref_path):
            self.ids.ref_plot.figure = self.manager.app.qct.plot()
            return False

        if len(peaks_idx) == 0 or peaks_idx is None:
            self.ids.ref_plot.figure = self.manager.app.qct.plot()
            return False

        data = pd.read_csv(ref_path, skiprows=1)

        frequency = data['Frequency']
        amplitude = data['Amplitude']

        fig, ax = plt.subplots(layout="constrained")
        ax.plot(frequency, amplitude)
        ax.scatter(
            frequency[peaks_idx],
            amplitude[peaks_idx],
            facecolors="none",
            edgecolors="red",
            marker="s",
            s=100,
        )

        ax.text(
            # RIGHT, TOP
            1-0.02, 1-0.04,
            info,
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=10,
            multialignment="left",
            bbox=dict(
                boxstyle="round,pad=0.5",
                facecolor="white",
                edgecolor="gray",
                alpha=0.60,
            ),
        )

        ax.grid()
        ax.set_xlabel("Frequency (Hz)", fontsize=13)
        ax.set_ylabel("Amplitude", fontsize=13)

        self.ids.ref_plot.figure = fig

        return True

    def reset_slot(self):
        self.slot_id = self.manager.metadata_manager.current

        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'reference',
            ''
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'peaks',
            ''
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'sample',
            ''
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'sample_peaks',
            ''
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'sample_table',
            ''
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'name',
            ''
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'status',
            ''
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'status',
            'IDLE'
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'frequency_shift',
            True
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'damping',
            True
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'peak_splitting',
            True
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'peak_intensity',
            True
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'missing_mode',
            True
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'added_mode',
            False
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'frequency_shift_limit',
            0.2
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'damping_limit',
            2.0
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'split_frequency_gap',
            250
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'peak_intensity_limit',
            2.5
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'peak_matching_tolerance',
            50
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'min_peak_distance',
            100
        )
        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'min_peak_prominence',
            10.0
        )

        slot_path = Path(f'Archive/QCT/SLOT{self.slot_id}/')

        if slot_path.exists():
            for item in slot_path.iterdir():
                if item.is_file() or item.is_symlink():
                    item.unlink()

        self.ids.ref_plot.figure = self.manager.app.qct.plot()

        self.reset_slot_dialog.dismiss()

    def open_reset_slot_dialog(self):
        self.reset_slot_dialog = MDDialog(
            title='Warning!',
            type='custom',
            text=(
                "This will permanently delete both the reference and test data "
                "for this slot. This action cannot be undone."
            ),
            buttons=[
                MDFlatButton(
                    text='Cancel',
                    # Only available KivyMD 1.2.0!
                    text_color=self.theme_cls.primary_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.reset_slot_dialog.dismiss()
                ),
                MDFlatButton(
                    text='Reset',
                    # Only available KivyMD 1.2.0!
                    text_color=self.theme_cls.error_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.reset_slot()
                ),
            ]
        )
        self.reset_slot_dialog.open()
