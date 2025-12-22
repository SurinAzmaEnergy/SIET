from kivymd.uix.screen import MDScreen


class Home(MDScreen):
    LABELS = ("First Peak:", "Second Peak:", "Third Peak:")

    def on_kv_post(self, base):
        self._widgets = (
            self.ids.first_peak,
            self.ids.second_peak,
            self.ids.third_peak,
        )
        self.set_peaks()

    def set_peaks(self, peaks=None):
        peaks = peaks or ()

        for widget, label, peak in zip(
            self._widgets, self.LABELS, peaks + (None,) * 3
        ):
            if isinstance(peak, float):
                widget.text = f"{label:<13} {peak/1000:.4f} {'':<2}kHz"
            else:
                widget.text = f"{label:<15} --- {'':<2}kHz"
