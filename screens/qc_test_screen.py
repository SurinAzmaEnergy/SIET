import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

from kivy.core.window import Window
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.clock import Clock
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField

from kivymd.uix.datatables import MDDataTable

from kivymd.uix.datatables.datatables import (
    TableData,
    TableRecycleGridLayout
)

class QCTable(MDDataTable):
    def __init__(self, screen, **kwargs):
        super().__init__(**kwargs)
        self.screen = screen

    def on_row_press(self, cell):
        Window.release_all_keyboards()


class QCTestScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Store reference data and plot elements
        self.fig = None
        self.ax = None
        self.reference_frequency = None
        self.reference_amplitude = None
        self.reference_peaks_idx = None

        self.current_widget = 'plot'

    def on_enter(self):
        self.display_slot_id()
        self.display_slot_name()
        self.setup_table()
        self.import_reference()
        imported = self.import_test()
        self.update_buttons_state(imported=imported, started=False)

    def update_buttons_state(self, imported, started):
        if imported:
            self.ids.set_test.disabled = True
            self.ids.qc_export.disabled = True
        elif started:
            self.ids.set_test.disabled = False
            self.ids.qc_export.disabled = False
        else:
            self.ids.set_test.disabled = True
            self.ids.qc_export.disabled = True

    def setup_table(self):
        self.table = QCTable(
            self,
            size_hint=(1, 1),
            elevation=0,
            use_pagination=True,
            background_color_header=(.23, .29, .36, .5),
            column_data=[
                ("mode", dp(30)),
                ("ref_freq", dp(40)),
                ("test_freq", dp(40)),
                ("freq_shift_fail", dp(30)),
                ("damping_fail", dp(30)),
                ("intensity_fail", dp(30)),
                ("split_fail", dp(30)),
                ("missing_fail", dp(30)),
                ("status", dp(30)),
            ],
        )

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
        self.start_btn = self.ids.qc_start
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

            # Get the test plot and combine it with the reference plot
            test_fig = self.manager.app.signal_processor.plot_fft()
            self.combine_plots(test_fig)

            self.calculate()

            return False  # stop checking

    def combine_plots(self, test_figure):
        """Combine reference plot with test plot"""
        # Check if reference plot exists
        if self.fig is None or self.ax is None:
            # If no reference plot, just show the test plot
            self.ids.qc_plot.figure = test_figure
            return

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

        info = (
            f"Resolution: {resolution} Hz\n"
            f"Range: {low_frequency} - {high_frequency} Hz"
        )

        # Extract test data from the test figure
        test_ax = test_figure.axes[0]
        test_line = test_ax.lines[0]
        test_scatter = test_ax.collections[0]

        test_freqs = test_line.get_xdata()
        test_amps = test_line.get_ydata()

        self.test_f = test_freqs
        self.test_spec = test_amps

        # Get peak data
        if len(test_scatter.get_offsets()) > 0:
            test_peaks_freqs = test_scatter.get_offsets()[:, 0]
            test_peaks_amps = test_scatter.get_offsets()[:, 1]
        else:
            test_peaks_freqs = []
            test_peaks_amps = []

        # Clear and recreate the plot with combined data
        self.ax.clear()

        # Plot reference data
        self.ax.plot(
            self.reference_frequency,
            self.reference_amplitude,
            label='Reference',
            color='blue',
            linewidth=1
        )

        self.ax.scatter(
            self.reference_frequency[self.reference_peaks_idx],
            self.reference_amplitude[self.reference_peaks_idx],
            facecolors="none",
            edgecolors="red",
            marker="s",
            s=100,
            label='Reference Peaks',
            linewidth=1
        )

        # Plot test data
        self.ax.plot(
            test_freqs,
            test_amps,
            label='Test',
            color='green',
            alpha=0.7,
            linewidth=1
        )
        if len(test_peaks_freqs) > 0:
            self.ax.scatter(
                test_peaks_freqs,
                test_peaks_amps,
                facecolors="none",
                edgecolors="orange",
                marker="o",
                s=80,
                label='Test Peaks',
                linewidth=1
            )

        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlabel("Frequency (Hz)", fontsize=13)
        self.ax.set_ylabel("Amplitude", fontsize=13)

        self.ax.text(
            # RIGHT, TOP
            1-0.02, 1-0.045,
            info,
            transform=self.ax.transAxes,
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

        # Remove tight_layout() to maintain original layout
        # Just refresh the canvas
        self.fig.canvas.draw()

        # Close the temporary test figure to free memory
        plt.close(test_figure)

        # Ensure the combined plot is displayed
        self.ids.qc_plot.figure = self.fig

    def open_qc_settings(self):
        self.manager.current = 'qc_settings'
        self.manager.transition.direction = 'up'

    def import_reference(self):
        ref_path = self.manager.metadata_manager.get(
            self.slot_id-1,
            'reference'
        )
        peaks_idx = self.manager.metadata_manager.get(
            self.slot_id-1,
            'peaks'
        )
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

        self.reference_peaks_idx = peaks_idx

        self.manager.config_manager.set(
            'SIET1010',
            'all_pass',
            False
        )

        self.manager.config_manager.set(
            'SIET1010',
            'resolution',
            resolution
        )
        self.manager.config_manager.set(
            'SIET1010',
            'low_frequency',
            low_frequency
        )
        self.manager.config_manager.set(
            'SIET1010',
            'high_frequency',
            high_frequency
        )

        if ref_path == '':
            default_fig = self.manager.app.qct.plot()
            self.ids.qc_plot.figure = default_fig
            self.fig = default_fig
            self.ax = default_fig.axes[0] if default_fig.axes else None
            return False

        self.data = pd.read_csv(ref_path, skiprows=1)
        self.frequency = self.data['Frequency']
        self.amplitude = self.data['Amplitude']

        self.reference_frequency = self.frequency
        self.reference_amplitude = self.amplitude

        self.fig, self.ax = plt.subplots(layout="constrained")

        self.ax.plot(
            self.frequency,
            self.amplitude,
            label='Reference',
            linewidth=1
        )

        self.ax.scatter(
            self.frequency[peaks_idx],
            self.amplitude[peaks_idx],
            facecolors="none",
            edgecolors="red",
            marker="s",
            s=100,
            label='Reference Peaks',
            linewidth=1
        )

        info = (
            f"Resolution: {resolution} Hz\n"
            f"Range: {low_frequency} - {high_frequency} Hz"
        )

        self.ax.text(
            # RIGHT, TOP
            1-0.02, 1-0.045,
            info,
            transform=self.ax.transAxes,
            ha="right",
            va="top",
            fontsize=15,
            multialignment="left",
            bbox=dict(
                boxstyle="round,pad=0.5",
                facecolor="white",
                edgecolor="gray",
                alpha=0.60,
            ),
        )

        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlabel("Frequency (Hz)", fontsize=15)
        self.ax.set_ylabel("Amplitude", fontsize=15)

        self.ids.qc_plot.figure = self.fig

        return True

    def calculate(self):
        f = self.reference_frequency
        ref_spec = self.amplitude
        test_f = self.test_f
        test_spec = self.test_spec

        # Resolution / step check
        ref_step = np.diff(f)
        test_step = np.diff(test_f)

        use_freq_shift = self.manager.metadata_manager.get(
            self.slot_id - 1,
            'frequency_shift'
        )
        use_damping = self.manager.metadata_manager.get(
            self.slot_id - 1,
            'damping'
        )
        use_intensity = self.manager.metadata_manager.get(
            self.slot_id - 1,
            'peak_intensity'
        )
        use_split = self.manager.metadata_manager.get(
            self.slot_id - 1,
            'peak_splitting'
        )
        use_missing = self.manager.metadata_manager.get(
            self.slot_id - 1,
            'missing_mode'
        )
        use_added = self.manager.metadata_manager.get(
            self.slot_id - 1,
            'added_mode'
        )

        freq_shift_limit = float(
            self.manager.metadata_manager.get(
                self.slot_id - 1,
                "frequency_shift_limit"
            )
        ) / 100
        damping_limit = float(
            self.manager.metadata_manager.get(
                self.slot_id - 1,
                "damping_limit"
            )
        ) / 100
        intensity_limit = float(
            self.manager.metadata_manager.get(
                self.slot_id - 1,
                "peak_intensity_limit"
            )
        ) / 100
        split_gap = float(
            self.manager.metadata_manager.get(
                self.slot_id - 1,
                "split_frequency_gap"
            )
        )
        tol_hz = float(
            self.manager.metadata_manager.get(
                self.slot_id - 1,
                "peak_matching_tolerance"
            )
        )
        min_dist = float(
            self.manager.metadata_manager.get(
                self.slot_id - 1,
                "min_peak_distance"
            )
        )
        min_prom = float(
            self.manager.metadata_manager.get(
                self.slot_id - 1,
                "min_peak_prominence"
            )
        ) / 100


        ref_idx, _ = find_peaks(
            ref_spec,
            prominence=min_prom,
            distance=min_dist
        )

        test_idx, _ = find_peaks(
            test_spec,
            prominence=min_prom,
            distance=min_dist
        )

        ref_locs = f[ref_idx]
        ref_peak_vals = ref_spec[ref_idx]

        test_locs = f[test_idx]
        test_peak_vals = test_spec[test_idx]


        num_ref_modes = len(ref_locs)
        num_test_modes = len(test_locs)

        matched_ref_f  = np.full(num_ref_modes, np.nan)
        matched_ref_p  = np.full(num_ref_modes, np.nan)
        matched_test_f = np.full(num_ref_modes, np.nan)
        matched_test_p = np.full(num_ref_modes, np.nan)

        used_test_idx = np.zeros(num_test_modes, dtype=bool)

        ref_locs = pd.Series(f[ref_idx])
        test_locs = pd.Series(f[test_idx])
        ref_peak_vals = pd.Series(ref_spec[ref_idx])
        test_peak_vals = pd.Series(test_spec[test_idx])

        for i in range(num_ref_modes):
            ref_f = ref_locs.iloc[i]
            diffs = np.abs(test_locs - ref_f)
            idx = np.argmin(diffs)
            min_diff = diffs.iloc[idx]

            matched_ref_f[i] = ref_f
            matched_ref_p[i] = ref_peak_vals.iloc[i]

            if min_diff <= tol_hz:
                matched_test_f[i] = test_locs.iloc[idx]
                matched_test_p[i] = test_peak_vals.iloc[idx]
                used_test_idx[idx] = True

        added_modes = []
        for i in range(num_test_modes):
            if not used_test_idx[i]:
                is_split = False
                for j in range(num_ref_modes):
                    if not np.isnan(matched_test_f[j]) and abs(test_locs.iloc[i] - matched_test_f[j]) < split_gap:
                        is_split = True
                        break
                if not is_split:
                    added_modes.append(test_locs.iloc[i])

        added_modes = np.array(added_modes)


        missing_mode = ref_locs[np.isnan(matched_test_f)] # This changed, be fucking careful!

        freq_shift = (matched_test_f - matched_ref_f) / matched_ref_f
        intensity_change = (matched_test_p - matched_ref_p) / matched_ref_p

        damping_ref = np.full(num_ref_modes, np.nan)
        damping_test = np.full(num_ref_modes, np.nan)

        for i in range(num_ref_modes):

            # ---------------- REFERENCE DAMPING ----------------

            if not np.isnan(matched_ref_f[i]):

                pk = matched_ref_p[i]
                f0 = matched_ref_f[i]

                idx = np.where(ref_spec >= pk / np.sqrt(2))[0]

                if len(idx) > 0:
                    damping_ref[i] = (
                        f.iloc[idx[-1]] - f.iloc[idx[0]]
                    ) / f0

            # ---------------- TEST DAMPING ----------------

            if not np.isnan(matched_test_f[i]):

                pk = matched_test_p[i]
                f0 = matched_test_f[i]

                idx = np.where(test_spec >= pk / np.sqrt(2))[0]

                if len(idx) > 0:
                    damping_test[i] = (
                        f.iloc[idx[-1]] - f.iloc[idx[0]]
                    ) / f0

        damping_change = (damping_test - damping_ref) / damping_ref

        split_flag = np.zeros(num_ref_modes, dtype=bool)
        for i in range(num_ref_modes):
            if not np.isnan(matched_test_f[i]):
                nearby = test_locs[np.abs(test_locs - matched_test_f[i]) < split_gap]
                if len(nearby) > 1:
                    split_flag[i] = True

        fail_freq_shift = np.zeros(num_ref_modes, dtype=bool)
        fail_damping    = np.zeros(num_ref_modes, dtype=bool)
        fail_intensity  = np.zeros(num_ref_modes, dtype=bool)
        fail_split      = np.zeros(num_ref_modes, dtype=bool)
        fail_missing    = np.zeros(num_ref_modes, dtype=bool)

        qc_fail = np.zeros(num_ref_modes, dtype=bool)
        qc_status = []

        for i in range(num_ref_modes):

            if np.isnan(matched_test_f[i]) and use_missing:
                fail_missing[i] = True

            else:
                if (
                    use_freq_shift
                    and not np.isnan(freq_shift[i])
                    and abs(freq_shift[i]) > freq_shift_limit
                ):
                    fail_freq_shift[i] = True

                if (
                    use_damping
                    and not np.isnan(damping_change[i])
                    and damping_change[i] > damping_limit
                ):
                    fail_damping[i] = True

                if (
                    use_intensity
                    and not np.isnan(intensity_change[i])
                    and abs(intensity_change[i]) > intensity_limit
                ):
                    fail_intensity[i] = True

                if use_split and split_flag[i]:
                    fail_split[i] = True

            qc_fail[i] = (
                fail_freq_shift[i]
                or fail_damping[i]
                or fail_intensity[i]
                or fail_split[i]
                or fail_missing[i]
            )

            qc_status.append("FAIL" if qc_fail[i] else "PASS")

        overall_status = False if "FAIL" in qc_status else True

        if overall_status:
            self.ids.indicator_text.text = 'PASS'
            self.ids.indicator.md_bg_color = (0.28, 0.73, 0.31, .5)
            self.status_to_save = 'PASS'
        else:
            self.ids.indicator_text.text = 'FAIL'
            self.ids.indicator.md_bg_color = (0.73, 0.23, 0.23, .5)
            self.status_to_save = 'FAIL'

        table_data = []

        for i in range(num_ref_modes):
            table_data.append({
                "index": i,
                "mode": i + 1,
                "ref_freq": None if np.isnan(matched_ref_f[i]) else float(matched_ref_f[i]),
                "test_freq": None if np.isnan(matched_test_f[i]) else float(matched_test_f[i]),

                "freq_shift_fail": bool(fail_freq_shift[i]),
                "damping_fail": bool(fail_damping[i]),
                "intensity_fail": bool(fail_intensity[i]),
                "split_fail": bool(fail_split[i]),
                "missing_fail": bool(fail_missing[i]),

                # "added_fail": "---",

                "status": qc_status[i],
            })

        df = pd.DataFrame(table_data)
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.where(pd.notnull(df), None)

        self.table_to_save = df

        self.table.row_data = [
            (
                str(row["mode"]),
                "" if row["ref_freq"] is None else f"{row['ref_freq']:.2f}",
                "" if row["test_freq"] is None else f"{row['test_freq']:.2f}",
                str(row["freq_shift_fail"]),
                str(row["damping_fail"]),
                str(row["intensity_fail"]),
                str(row["split_fail"]),
                str(row["missing_fail"]),
                row["status"],
            )
            for _, row in df.iterrows()
        ]

    def toggle(self):
        self.ids.container.clear_widgets()
        button = self.ids.qct_toggle_btn

        if self.current_widget == 'plot':
            self.ids.container.add_widget(self.table)
            self.ids.container.padding = (0, 0, 10, 0)
            button.text = 'Show Plot'
            self.current_widget = 'table'
        else:
            self.ids.container.add_widget(self.ids.qc_plot)
            self.ids.container.padding = (10, 10)
            button.text = 'Show Table'
            self.current_widget = 'plot'

    def open_qc_settings(self):
        self.manager.settings_caller = 'qc_test'
        self.manager.current = 'qc_settings'
        self.manager.transition.direction = 'up'

    def save(self, name, path=None):
        if path is None:
            path = self.manager.default
        sp = self.manager.app.signal_processor

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

    def set_test(self):
        sp = self.manager.app.signal_processor

        slot_path = Path(f'Archive/QCT/SLOT{self.slot_id}/')

        current_time = datetime.now()
        file_name = current_time.strftime(
            f"SIET1010_%Y-%m-%d_%H-%M-%S_S{self.slot_id}_TEST.csv"
        )
        table_file_name = current_time.strftime(
            f"SIET1010_%Y-%m-%d_%H-%M-%S_S{self.slot_id}_T_TEST.csv"
        )

        # Compose the path
        full_path = os.path.join(slot_path, file_name)
        table_full_path = os.path.join(slot_path, table_file_name)


        self.save(file_name, slot_path)
        self.table_to_save.to_csv(table_full_path, index=False)

        success_dialog = MDDialog(
            title='Reference Set',
            text=full_path,
            buttons=[MDFlatButton(
                text='OK',
                # Only available KivyMD 1.2.0!
                text_color=self.theme_cls.primary_color,
                font_size="20sp",
                theme_text_color='Custom',
                on_release=lambda _: success_dialog.dismiss()
            )]
        )

        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'sample',
            full_path,
        )

        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'sample_table',
            table_full_path,
        )

        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'sample_peaks',
            sp.peaks_for_qct.tolist(),
        )

        self.manager.metadata_manager.put(
            self.slot_id - 1,
            'status',
            self.status_to_save,
        )

        success_dialog.open()

    def import_test(self):
        test_path = self.manager.metadata_manager.get(
            self.slot_id-1,
            'sample'
        )
        peaks_idx = self.manager.metadata_manager.get(
            self.slot_id-1,
            'sample_peaks'
        )
        sample_table = self.manager.metadata_manager.get(
            self.slot_id-1,
            'sample_table'
        )
        status = self.manager.metadata_manager.get(
            self.slot_id-1,
            'status'
        )

        if test_path == '': # Or the file did not exist!
            return False

        if status == 'PASS':
            self.ids.indicator_text.text = 'PASS'
            self.ids.indicator.md_bg_color = (0.28, 0.73, 0.31, .5)
        elif status == 'FAIL':
            self.ids.indicator_text.text = 'FAIL'
            self.ids.indicator.md_bg_color = (0.73, 0.23, 0.23, .5)
        elif status == 'IDLE':
            self.ids.indicator_text.text = 'IDLE'
            self.ids.indicator.md_bg_color = (1, 1, 1, 1)

        data = pd.read_csv(test_path, skiprows=1)
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

        table_loaded = pd.read_csv(sample_table)

        self.table.row_data = [
            (
                str(row["mode"]),
                "--" if row["ref_freq"] is None else f"{row['ref_freq']:.2f}",
                "--" if row["test_freq"] is None else f"{row['test_freq']:.2f}",
                str(row["freq_shift_fail"]),
                str(row["damping_fail"]),
                str(row["intensity_fail"]),
                str(row["split_fail"]),
                str(row["missing_fail"]),
                # str(row["added_fail"]),
                row["status"],
            )
            for _, row in table_loaded.iterrows()
        ]

        ax.grid()
        ax.set_xlabel("Frequency (Hz)", fontsize=15)
        ax.set_ylabel("Amplitude", fontsize=15)

        self.combine_plots(fig)

        return True

    def show_save_dialog(self):
        current_time = datetime.now()
        file_name = current_time.strftime(f"SIET1010_%Y-%m-%d_%H-%M-%S_TEST.csv")
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
                    font_size="20sp",
                    on_release=lambda _: self.save_dialog.dismiss(),
                ),
                MDFlatButton(
                    text="OK",
                    text_color=self.theme_cls.primary_color,
                    theme_text_color="Custom",
                    font_size="20sp",
                    on_release=lambda _: self.save(self.save_dialog.content_cls.text),
                ),
            ],
        )
        self.save_dialog.open()
