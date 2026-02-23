import json
import os
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.tab.tab import MDTabsBase, MDTabs
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.properties import StringProperty, ObjectProperty, NumericProperty
from kivymd.uix.button import MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from scipy.signal import find_peaks


class Tab(MDFloatLayout, MDTabsBase):
    '''Class implementing content for a tab.'''
    pass


class TabContainer(MDTabs):
    def __ini__(self, **kwargs):
        super().__init__(**kwargs)

    def on_tab_switch(self, *args):
        self.screen.update_calculation_button_status()


class ModulusScreen(MDScreen):
    bar_choice = StringProperty('')
    rod_choice = StringProperty('')
    peak_choice = NumericProperty(-1)

    def __ini__(self, **kwargs):
        super().__init__(**kwargs)

    def show_main_peak(self):
        main_peak = self.manager.app.main_peak / 1000
        self.ids.main_peak.text = f'Main Peak: {main_peak:.4f} kHz'

    def on_enter(self):
        self.tab = self.ids.tab_container.get_current_tab().title
        self.show_main_peak()
        self.update_calculation_button_status()
        self.empty_damping_plot()

        try:
            if hasattr(self.ids.df.ids, 'unit_label') and self.ids.df.ids.unit_label.parent:
                self.ids.df.ids.unit_label.parent.remove_widget(self.ids.df.ids.unit_label)
                self.ids.df.ids.label_field.size_hint = (.5, None)
                self.ids.df.ids.title_label.size_hint = (.5, None)

            if hasattr(self.ids.quality_factor.ids, 'unit_label') and self.ids.quality_factor.ids.unit_label.parent:
                self.ids.quality_factor.ids.unit_label.parent.remove_widget(self.ids.quality_factor.ids.unit_label)
                self.ids.quality_factor.ids.label_field.size_hint = (.5, None)
                self.ids.quality_factor.ids.title_label.size_hint = (.5, None)
        except Exception: pass

    def empty_damping_plot(self):
        fig, ax = plt.subplots(layout='constrained')
        ax.grid()
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Amplitude')
        # ax.set_title('Frequency Spectrum with Damping Measurement')
        self.ids.damping_plot.figure = fig

    def change_bar_choice(self):
        bar_choices = {
            'poisson_bar_choice': 'poisson',
            'flexural_bar_choice': 'flexural',
            'torsional_bar_choice': 'torsional'
        }

        self.bar_choice = next(
            (value for key, value in bar_choices.items()
             if getattr(self.ids, key).state == 'down'),
            ''
        )

        self.update_calculation_button_status()

    def change_rod_choice(self):
        rod_choices = {
            'poisson_rod_choice': 'poisson',
            'flexural_rod_choice': 'flexural',
            'torsional_rod_choice': 'torsional'
        }

        self.rod_choice = next(
            (value for key, value in rod_choices.items()
             if getattr(self.ids, key).state == 'down'),
            ''
        )

        self.update_calculation_button_status()

    def change_peak_choice(self):
        peak_choices = {
            'first_peak_choice': 0,
            'second_peak_choice': 1,
            'third_peak_choice': 2
        }

        self.peak_choice = next(
            (value for key, value in peak_choices.items()
             if getattr(self.ids, key).state == 'down'),
             -1
        )

        self.update_calculation_button_status()

    def open_save_dialog(self):
        current_time = datetime.now()

        if self.tab == 'BAR':
            file_name = current_time.strftime(f"SIET1010_%Y-%m-%d_%H-%M-%S_BAR.json")
        elif self.tab == 'ROD':
            file_name = current_time.strftime(f"SIET1010_%Y-%m-%d_%H-%M-%S_ROD.json")
        elif self.tab == 'DISC':
            file_name = current_time.strftime(f"SIET1010_%Y-%m-%d_%H-%M-%S_DISC.json")
        elif self.tab == 'DF':
            file_name = current_time.strftime(f"SIET1010_%Y-%m-%d_%H-%M-%S_DF.json")

        self.save_dialog = MDDialog(
            title='File Name:',
            type='custom',
            pos_hint={'center_x': .5, 'center_y': 0.8},
            content_cls=MDTextField(
                mode='round',
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
        if self.tab == 'BAR':
            inputs = {
                'length': self.ids.bar_length.ids.label_field.text,
                'width': self.ids.bar_width.ids.label_field.text,
                'thickness': self.ids.bar_thickness.ids.label_field.text,
                'mass': self.ids.bar_mass.ids.label_field.text,
                'flexural_frequency': self.ids.bar_flexural_frequency.ids.label_field.text,
                'torsional_frequency': self.ids.bar_torsional_frequency.ids.label_field.text,
                'initial_poisson_ratio': self.ids.bar_initial_poisson_ratio.ids.label_field.text,
                'measurement_type': self.bar_choice
            }
            outputs = {
                'young_modulus': self.ids.bar_young_modulus_output.ids.label_field.text,
                'shear_modulus': self.ids.bar_shear_modulus_output.ids.label_field.text,
                'poisson_ratio': self.ids.bar_poisson_ratio_output.ids.label_field.text
            }

            with open(os.path.join(self.manager.default, name), 'w') as f:
                json.dump({'Inputs': inputs, 'Outputs': outputs}, f, indent=4)

        elif self.tab == 'ROD':
            inputs = {
                'length': self.ids.rod_length.ids.label_field.text,
                'diameter': self.ids.rod_diameter.ids.label_field.text,
                'mass': self.ids.rod_mass.ids.label_field.text,
                'flexural_frequency': self.ids.rod_flexural_frequency.ids.label_field.text,
                'torsional_frequency': self.ids.rod_torsional_frequency.ids.label_field.text,
                'initial_poisson_ratio': self.ids.rod_initial_poisson_ratio.ids.label_field.text,
                'measurement_type': self.rod_choice
            }
            outputs = {
                'young_modulus': self.ids.rod_young_modulus_output.ids.label_field.text,
                'shear_modulus': self.ids.rod_shear_modulus_output.ids.label_field.text,
                'poisson_ratio': self.ids.rod_poisson_ratio_output.ids.label_field.text
            }

            with open(os.path.join(self.manager.default, name), 'w') as f:
                json.dump({'Inputs': inputs, 'Outputs': outputs}, f, indent=4)

        elif self.tab == 'DISC':
            inputs = {
                'diameter': self.ids.disc_diameter.ids.label_field.text,
                'thickness': self.ids.disc_thickness.ids.label_field.text,
                'mass': self.ids.disc_mass.ids.label_field.text,
                'first_frequency': self.ids.disc_first_frequency.ids.label_field.text,
                'second_frequency': self.ids.disc_second_frequency.ids.label_field.text,
            }
            outputs = {
                'young_modulus': self.ids.disc_young_modulus_output.ids.label_field.text,
                'shear_modulus': self.ids.disc_shear_modulus_output.ids.label_field.text,
                'poisson_ratio': self.ids.disc_poisson_ratio_output.ids.label_field.text
            }

            with open(os.path.join(self.manager.default, name), 'w') as f:
                json.dump({'Inputs': inputs, 'Outputs': outputs}, f, indent=4)

        elif self.tab == 'DF':
            inputs = {
                'peak': self.peak_choice
            }

            outputs = {
                'f0': self.ids.f0_output.ids.label_field.text,
                'f1': self.ids.f1_output.ids.label_field.text,
                'f2': self.ids.f2_output.ids.label_field.text,
                'Bandwidth': self.ids.delta_f.ids.label_field.text,
                'Quality Factor': self.ids.quality_factor.ids.label_field.text,
                'Damping Factor': self.ids.df.ids.label_field.text
            }

            with open(os.path.join(self.manager.default, name), 'w') as f:
                json.dump({'Inputs': inputs, 'Outputs': outputs}, f, indent=4)

        self.save_dialog.dismiss()

    def reset(self):
        if self.tab == 'BAR':
            for btn in [
                self.ids.poisson_bar_choice,
                self.ids.flexural_bar_choice,
                self.ids.torsional_bar_choice
            ]:
                btn.state = 'normal'
            self.bar_choice = ''

            for field in [
                self.ids.bar_length.ids.label_field,
                self.ids.bar_width.ids.label_field,
                self.ids.bar_thickness.ids.label_field,
                self.ids.bar_mass.ids.label_field,
                self.ids.bar_initial_poisson_ratio.ids.label_field,
                self.ids.bar_flexural_frequency.ids.label_field,
                self.ids.bar_torsional_frequency.ids.label_field
            ]:
                field.text = ''

            for field in [
                self.ids.bar_young_modulus_output.ids.label_field,
                self.ids.bar_shear_modulus_output.ids.label_field,
                self.ids.bar_poisson_ratio_output.ids.label_field
            ]:
                field.text = ''
        elif self.tab == 'ROD':
            for btn in [
                self.ids.poisson_rod_choice,
                self.ids.flexural_rod_choice,
                self.ids.torsional_rod_choice
            ]:
                btn.state = 'normal'
            self.rod_choice = ''

            for field in [
                self.ids.rod_length.ids.label_field,
                self.ids.rod_diameter.ids.label_field,
                self.ids.rod_mass.ids.label_field,
                self.ids.rod_initial_poisson_ratio.ids.label_field,
                self.ids.rod_flexural_frequency.ids.label_field,
                self.ids.rod_torsional_frequency.ids.label_field
            ]:
                field.text = ''

            for field in [
                self.ids.rod_young_modulus_output.ids.label_field,
                self.ids.rod_shear_modulus_output.ids.label_field,
                self.ids.rod_poisson_ratio_output.ids.label_field
            ]:
                field.text = ''

        elif self.tab == 'DISC':
            for field in [
                self.ids.disc_diameter.ids.label_field,
                self.ids.disc_thickness.ids.label_field,
                self.ids.disc_mass.ids.label_field,
                self.ids.disc_first_frequency.ids.label_field,
                self.ids.disc_second_frequency.ids.label_field
            ]:
                field.text = ''

            for field in [
                self.ids.disc_young_modulus_output.ids.label_field,
                self.ids.disc_shear_modulus_output.ids.label_field,
                self.ids.disc_poisson_ratio_output.ids.label_field
            ]:
                field.text = ''

        elif self.tab == 'DF':
            for btn in [
                self.ids.first_peak_choice,
                self.ids.second_peak_choice,
                self.ids.third_peak_choice
            ]:
                btn.state = 'normal'
            for field in [
                self.ids.f0_output.ids.label_field,
                self.ids.f1_output.ids.label_field,
                self.ids.f2_output.ids.label_field,
                self.ids.delta_f.ids.label_field,
                self.ids.quality_factor.ids.label_field,
                self.ids.df.ids.label_field,
            ]:
                field.text = ''

            self.empty_damping_plot()

        self.update_calculation_button_status()

    def update_calculation_button_status(self):
        self.tab = self.ids.tab_container.get_current_tab().title

        if self.tab == 'BAR':
            calculate_button = self.ids.bar_calculation_btn
            reset_button = self.ids.bar_reset_btn

            fields = [
                bool(self.ids.bar_length.ids.label_field.text),
                bool(self.ids.bar_width.ids.label_field.text),
                bool(self.ids.bar_thickness.ids.label_field.text),
                bool(self.ids.bar_mass.ids.label_field.text),
                bool(self.ids.bar_initial_poisson_ratio.ids.label_field.text),
                bool(self.bar_choice)
            ]

            output_fields = [
                bool(self.ids.bar_young_modulus_output.ids.label_field.text),
                bool(self.ids.bar_shear_modulus_output.ids.label_field.text),
                bool(self.ids.bar_poisson_ratio_output.ids.label_field.text)
            ]

            if self.bar_choice == 'flexural':
                fields.append(bool(self.ids.bar_flexural_frequency.ids.label_field.text))
            elif self.bar_choice == 'torsional':
                fields.append(bool(self.ids.bar_torsional_frequency.ids.label_field.text))
            else:
                fields.extend([
                    bool(self.ids.bar_flexural_frequency.ids.label_field.text),
                    bool(self.ids.bar_torsional_frequency.ids.label_field.text)
                ])

            calculate_button.disabled = not all(fields)
            reset_button.disabled = not any(fields)

            self.ids.modulus_panel.ids.right_button.disabled = not any(
                output_fields)

        elif self.tab == 'ROD':
            calculate_button = self.ids.rod_calculation_btn
            reset_button = self.ids.rod_reset_btn

            fields = [
                bool(self.ids.rod_length.ids.label_field.text),
                bool(self.ids.rod_diameter.ids.label_field.text),
                bool(self.ids.rod_mass.ids.label_field.text),
                bool(self.ids.rod_initial_poisson_ratio.ids.label_field.text),
                bool(self.rod_choice)
            ]

            output_fields = [
                bool(self.ids.rod_young_modulus_output.ids.label_field.text),
                bool(self.ids.rod_shear_modulus_output.ids.label_field.text),
                bool(self.ids.rod_poisson_ratio_output.ids.label_field.text)
            ]

            if self.rod_choice == 'flexural':
                fields.append(bool(self.ids.rod_flexural_frequency.ids.label_field.text))
            elif self.rod_choice == 'torsional':
                fields.append(bool(self.ids.rod_torsional_frequency.ids.label_field.text))
            else:
                fields.extend([
                    bool(self.ids.rod_flexural_frequency.ids.label_field.text),
                    bool(self.ids.rod_torsional_frequency.ids.label_field.text)
                ])

            calculate_button.disabled = not all(fields)
            reset_button.disabled = not any(fields)

            self.ids.modulus_panel.ids.right_button.disabled = not any(
                output_fields)

        elif self.tab == 'DISC':
            calculate_button = self.ids.disc_calculation_btn
            reset_button = self.ids.disc_reset_btn

            fields = [
                bool(self.ids.disc_thickness.ids.label_field.text),
                bool(self.ids.disc_diameter.ids.label_field.text),
                bool(self.ids.disc_mass.ids.label_field.text),
                bool(self.ids.disc_first_frequency.ids.label_field.text),
                bool(self.ids.disc_second_frequency.ids.label_field.text),
            ]

            output_fields = [
                bool(self.ids.disc_young_modulus_output.ids.label_field.text),
                bool(self.ids.disc_shear_modulus_output.ids.label_field.text),
                bool(self.ids.disc_poisson_ratio_output.ids.label_field.text)
            ]

            calculate_button.disabled = not all(fields)
            reset_button.disabled = not any(fields)

            self.ids.modulus_panel.ids.right_button.disabled = not any(output_fields)

        elif self.tab == 'DF':
            calculate_button = self.ids.df_calculation_btn
            reset_button = self.ids.df_reset_btn

            fields = [
                bool(self.peak_choice != -1)
            ]

            output_fields = [
                bool(self.ids.f0_output.ids.label_field.text),
                bool(self.ids.f1_output.ids.label_field.text),
                bool(self.ids.f2_output.ids.label_field.text),
                bool(self.ids.delta_f.ids.label_field.text),
                bool(self.ids.quality_factor.ids.label_field.text),
                bool(self.ids.df.ids.label_field.text)
            ]

            calculate_button.disabled = not all(fields)
            reset_button.disabled = not any(fields)

            self.ids.modulus_panel.ids.right_button.disabled = not any(output_fields)

    def bar_calculation(self):
        inputs = {
            'length': self.ids.bar_length.ids.label_field.text,
            'width': self.ids.bar_width.ids.label_field.text,
            'thickness': self.ids.bar_thickness.ids.label_field.text,
            'mass': self.ids.bar_mass.ids.label_field.text,
            'flexural_frequency': self.ids.bar_flexural_frequency.ids.label_field.text,
            'torsional_frequency': self.ids.bar_torsional_frequency.ids.label_field.text,
            'initial_poisson_ratio': self.ids.bar_initial_poisson_ratio.ids.label_field.text,
            'measurement_type': self.bar_choice
        }

        length = float(inputs['length'])
        width = float(inputs['width'])
        thickness = float(inputs['thickness'])
        mass = float(inputs['mass'])
        initial_poisson_ratio = float(inputs['initial_poisson_ratio'])
        if inputs['flexural_frequency'] != '':
            flexural_frequency = float(inputs['flexural_frequency'])
        if inputs['torsional_frequency'] != '':
            torsional_frequency = float(inputs['torsional_frequency'])

        errors = []

        if not (length >= width >= thickness):
            errors.append('- Length must be ≥ Width ≥ Thickness.')

        if not (0 < length <= 10000):
            errors.append('- Length must be between 0 and 10000.')

        if not (0 < width <= 2000):
            errors.append('- Width must be between 0 and 2000.')

        if not (0 < thickness <= 1000):
            errors.append('- Thickness must be between 0 and 1000.')

        if not (0 < mass <= 20000):
            errors.append('- Mass must be between 0 and 20000.')

        if not (0 < initial_poisson_ratio < 1):
            errors.append('- Poisson ratio must be between 0 and 1.')

        if inputs['flexural_frequency'] != '':
            if not (0.02 < flexural_frequency < 24):
                errors.append('- Flexural frequency must be between 0.02 and 24.')

        if inputs['torsional_frequency'] != '':
            if not (0.02 < torsional_frequency < 24):
                errors.append('- Torsional frequency must be between 0.02 and 24.')

        if errors:
            self.bar_error_dialog = MDDialog(
                title='Invalid Inputs!',
                text='\n'.join(errors),
                buttons=[
                    MDFlatButton(
                        text='OK',
                        on_release=lambda _: self.bar_error_dialog.dismiss()
                    )
                ]
            )
            self.bar_error_dialog.open()
            return

        result = self.manager.calculator.bar(**inputs)
        self.ids.bar_young_modulus_output.ids.label_field.text = result['dynamic_young_modulus_output']
        self.ids.bar_shear_modulus_output.ids.label_field.text = result['dynamic_shear_modulus_output']
        self.ids.bar_poisson_ratio_output.ids.label_field.text = result['poisson_ratio_output']

        self.update_calculation_button_status()

    def rod_calculation(self):
        inputs = {
            'length': self.ids.rod_length.ids.label_field.text,
            'diameter': self.ids.rod_diameter.ids.label_field.text,
            'mass': self.ids.rod_mass.ids.label_field.text,
            'flexural_frequency': self.ids.rod_flexural_frequency.ids.label_field.text,
            'torsional_frequency': self.ids.rod_torsional_frequency.ids.label_field.text,
            'initial_poisson_ratio': self.ids.rod_initial_poisson_ratio.ids.label_field.text,
            'measurement_type': self.rod_choice
        }

        length = float(inputs['length'])
        diameter = float(inputs['diameter'])
        mass = float(inputs['mass'])
        initial_poisson_ratio = float(inputs['initial_poisson_ratio'])

        if inputs['flexural_frequency'] != '':
            flexural_frequency = float(inputs['flexural_frequency'])

        if inputs['torsional_frequency'] != '':
            torsional_frequency = float(inputs['torsional_frequency'])

        errors = []

        if not (length >= diameter):
            errors.append('- Length must be ≥ diameter.')

        if not (0 < length <= 10000):
            errors.append('- Length must be between 0 and 10000.')

        if not (0 < diameter <= 2000):
            errors.append('- Length must be between 0 and 2000.')

        if not (0 < mass <= 20000):
            errors.append('- Length must be between 0 and 20000.')

        if not (0 < initial_poisson_ratio < 1):
            errors.append('- Poisson ratio must be between 0 and 1.')

        if inputs['flexural_frequency'] != '':
            if not (0.02 < flexural_frequency < 24):
                errors.append('- Flexural frequency must be between 0.02 and 24.')

        if inputs['torsional_frequency'] != '':
            if not (0.02 < torsional_frequency < 24):
                errors.append('- Torsional frequency must be between 0.02 and 24.')

        if errors:
            self.rod_error_dialog = MDDialog(
                title='Invalid Inputs!',
                text='\n'.join(errors),
                buttons=[
                    MDFlatButton(
                        text='OK',
                        on_release=lambda _: self.rod_error_dialog.dismiss()
                    )
                ]
            )
            self.rod_error_dialog.open()
            return

        result = self.manager.calculator.rod(**inputs)
        self.ids.rod_young_modulus_output.ids.label_field.text = result['dynamic_young_modulus_output']
        self.ids.rod_shear_modulus_output.ids.label_field.text = result['dynamic_shear_modulus_output']
        self.ids.rod_poisson_ratio_output.ids.label_field.text = result['poisson_ratio_output']

        self.update_calculation_button_status()


    def disc_calculation(self):
        inputs = {
            'diameter': self.ids.disc_diameter.ids.label_field.text,
            'mass': self.ids.disc_mass.ids.label_field.text,
            'thickness': self.ids.disc_thickness.ids.label_field.text,
            'first_frequency': self.ids.disc_first_frequency.ids.label_field.text,
            'second_frequency': self.ids.disc_second_frequency.ids.label_field.text,
        }

        diameter = float(inputs['diameter'])
        thickness = float(inputs['thickness'])
        mass = float(inputs['mass'])
        first_frequency = float(inputs['first_frequency'])
        second_frequency = float(inputs['second_frequency'])

        errors = []

        if not (diameter >= thickness):
            errors.append('- Diameter must be ≥ Thickness.')

        if not (0 < diameter <= 2000):
            errors.append('- Length must be between 0 and 2000.')

        if not (0 < mass <= 20000):
            errors.append('- Length must be between 0 and 20000.')

        if not (0 < thickness <= 1000):
            errors.append('- Thickness must be between 0 and 1000.')

        if not (0.02 < first_frequency < 24):
            errors.append('- First frequency must be between 0.02 and 24.')

        if not (0.02 < second_frequency < 24):
            errors.append('- Second frequency must be between 0.02 and 24.')


        if errors:
            self.disc_error_dialog = MDDialog(
                title='Invalid Inputs!',
                text='\n'.join(errors),
                buttons=[
                    MDFlatButton(
                        text='OK',
                        on_release=lambda _: self.disc_error_dialog.dismiss()
                    )
                ]
            )
            self.disc_error_dialog.open()
            return

        result = self.manager.calculator.disc(**inputs)
        self.ids.disc_young_modulus_output.ids.label_field.text = result['dynamic_young_modulus_output']
        self.ids.disc_shear_modulus_output.ids.label_field.text = result['dynamic_shear_modulus_output']
        self.ids.disc_poisson_ratio_output.ids.label_field.text = result['poisson_ratio_output']

        self.update_calculation_button_status()

    def damping_factor(self):
        self.all_pass_value = self.manager.config_manager.getboolean(
            'SIET1010',
            'all_pass'
        )

        self.low_frequency = float(self.manager.config_manager.get(
            'SIET1010',
            'low_frequency'
        ))

        self.high_frequency = float(self.manager.config_manager.get(
            'SIET1010',
            'high_frequency'
        ))

        self.resolution = self.manager.config_manager.get(
            'SIET1010',
            'resolution'
        )

        self.threshold = float(self.manager.config_manager.get(
            'SIET1010',
            'sensitivity'
        ))

        self.distance = float(self.manager.config_manager.get(
            'SIET1010',
            'distance'
        ))

        data = self.manager.app.signal_processor.normalized_signal

        # f_lower = 20       # Hz
        # f_upper = 24000    # Hz
        if self.all_pass_value:
            f_lower = 20
            f_upper = 24000   # 24 kHz
        else:
            f_lower = self.low_frequency * 1000
            f_upper = self.high_frequency * 1000

        Distance = self.distance

        a = self.peak_choice + 1

        Fs = 196000

        data = data / np.max(np.abs(data))
        N = len(data)
        t = np.arange(N) / Fs

        f = np.fft.fftfreq(N, d=1/Fs)[:N//2]
        fft_data = np.abs(np.fft.fft(data))[:N//2]

        fft_data = fft_data.round(3) # By me!

        mask = (f >= f_lower) & (f <= f_upper)
        f_filtered = f[mask]
        fft_data_filtered = fft_data[mask]

        fft_data_filtered /= np.max(fft_data_filtered)

        Dist = int(Distance / (Fs / N))

        peaks, _ = find_peaks(fft_data_filtered, distance=Dist)

        sorted_indices = np.argsort(fft_data_filtered[peaks])[::-1]
        top_indices = peaks[sorted_indices[:min(3, len(peaks))]]
        top_peaks = fft_data_filtered[top_indices]

        a_index = a - 1
        f0 = f_filtered[top_indices[a_index]]
        peak_amp = top_peaks[a_index]
        half_power = peak_amp / np.sqrt(2)

        left_side = fft_data_filtered[:top_indices[a_index]]
        left_cross = np.where(left_side <= half_power)[0]
        left_cross = left_cross[-1] if left_cross.size > 0 else 0
        f1 = f_filtered[left_cross]

        right_side = fft_data_filtered[top_indices[a_index]:]

        right_cross = np.where(right_side <= half_power)[0]
        right_cross = (right_cross[0] + top_indices[a_index]) if right_cross.size > 0 else len(f_filtered) - 1
        f2 = f_filtered[right_cross]

        delta_f = f2 - f1
        damping_ratio = delta_f / (2 * f0)
        quality_factor = 1 / (2 * damping_ratio)

        fig, ax = plt.subplots(layout='tight')

        ax.plot(f_filtered, fft_data_filtered, 'r', linewidth=1.5)
        ax.axvline(x=f0, color='k', linestyle='--', label='Resonance')
        ax.axvline(x=f1, color='g', linestyle='--', label='Half-power')
        ax.axvline(x=f2, color='g', linestyle='--')
        ax.axhline(y=half_power, xmin=0, xmax=1, color='b', linestyle='--', label='Half-power level')  # xmin/xmax are in 0-1 scale
        # ax.hlines(y=half_power, xmin=f_filtered[0], xmax=f_filtered[-1], color='b', linestyle='--', label='Half-power level')

        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Amplitude')
        # ax.set_title(f'Frequency Spectrum with Damping Measurement (ζ = {damping_ratio:.8f})')
        ax.grid(True)
        ax.legend()
        ax.set_xlim([f1 - 2 * delta_f, f2 + 2 * delta_f])

        self.ids.damping_plot.figure = fig

        # print(f'Resonance Frequency (f0): {f0:.2f} Hz')
        self.ids.f0_output.ids.label_field.text = f'{f0:.2f}'
        # print(f'Half-Power Frequencies: {f1:.2f} Hz and {f2:.2f} Hz')
        self.ids.f1_output.ids.label_field.text = f'{f1:.2f}'
        self.ids.f2_output.ids.label_field.text = f'{f2:.2f}'
        # print(f'Bandwidth (Δf): {delta_f:.2f} Hz')
        self.ids.delta_f.ids.label_field.text = f'{delta_f:.2f}'
        # print(f'Damping Ratio (ζ): {damping_ratio:.8f}')
        self.ids.df.ids.label_field.text = f'{damping_ratio:.8f}'
        # print(f'Quality Factor (Q): {quality_factor:.2f}')
        self.ids.quality_factor.ids.label_field.text = f'{quality_factor:.2f}'

        self.update_calculation_button_status()

