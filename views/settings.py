from kivymd.uix.screen import MDScreen


class GeneralSettings(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self):
        self.display_frequency('low_freq_label', 2)
        self.display_frequency('high_freq_label', 10)
        self.toggle_all_pass(False)

    def display_frequency(self, label_id, value):
        if label_id == 'low_freq_label':
            self.ids.low_freq_slider.value = value
            self.ids.low_freq_label.text = f'Low Frequency: {value:.2f} kHz'
            self.ids.high_min_label.text = f'Min: {int(value) + 1} kHz'
            self.ids.high_freq_slider.min = value + 1
        else:
            self.ids.high_freq_slider.value = value
            self.ids.high_freq_label.text = f'High Frequency: {value:.2f} kHz'
            self.ids.low_max_label.text = f'Max: {int(value) - 1} kHz'
            self.ids.low_freq_slider.max = value - 1

    def toggle_all_pass(self, active):
        self.ids.all_pass_switch.active = active
        if active == True:
            self.ids.high_freq_slider.disabled = True
            self.ids.low_freq_slider.disabled = True
        else:
            self.ids.high_freq_slider.disabled = False
            self.ids.low_freq_slider.disabled = False


class AdvancedSettings(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self):
        self.display_advanced_label('distance_label', 100)
        self.display_advanced_label('sensitivity_label', 2)
        self.display_advanced_label('resolution_label', 0.5)

    def display_advanced_label(self, label_id, value):
        if label_id == 'resolution_label':
            self.ids.resolution_label.text = f'Resolution: {value:.1f} Hz'
            self.ids.resolution_slider.value = value
        elif label_id == 'sensitivity_label':
            self.ids.sensitivity_label.text = f'Sensitivity: ± {value:.1f}'
            self.ids.sensitivity_slider.value = value
        elif label_id == 'distance_label':
            self.ids.distance_label.text = f'Distance: {int(value)} Hz'
            self.ids.distance_slider.value = value
