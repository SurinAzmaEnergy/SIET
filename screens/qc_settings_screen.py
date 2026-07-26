from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton


class QCSettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.after_clavius = False

    def on_enter(self):
        self.display_slot_id()
        self.display_slot_name()
        if not self.after_clavius:
            self.import_settings()
        self.after_clavius = False

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

    def import_settings(self):
        freq_shift = self.manager.metadata_manager.get(
            self.slot_id - 1,
            'frequency_shift',
        )
        damping = self.manager.metadata_manager.get(
            self.slot_id - 1,
            'damping',
        )
        peak_splitting = self.manager.metadata_manager.get(
            self.slot_id - 1,
            'peak_splitting',
        )
        peak_intensity = self.manager.metadata_manager.get(
            self.slot_id - 1,
            'peak_intensity',
        )
        missing_mode = self.manager.metadata_manager.get(
            self.slot_id - 1,
            'missing_mode',
        )
        added_mode = self.manager.metadata_manager.get(
            self.slot_id - 1,
            'added_mode',
        )

        frequency_shift_limit = str(self.manager.metadata_manager.get(
            self.slot_id - 1,
            'frequency_shift_limit',
        ))
        damping_limit = str(self.manager.metadata_manager.get(
            self.slot_id - 1,
            'damping_limit',
        ))
        split_frequency_gap = str(self.manager.metadata_manager.get(
            self.slot_id - 1,
            'split_frequency_gap',
        ))
        peak_intensity_limit = str(self.manager.metadata_manager.get(
            self.slot_id - 1,
            'peak_intensity_limit',
        ))
        peak_matching_tolerance = str(self.manager.metadata_manager.get(
            self.slot_id - 1,
            'peak_matching_tolerance',
        ))
        min_peak_distance = str(self.manager.metadata_manager.get(
            self.slot_id - 1,
            'min_peak_distance',
        ))
        min_peak_prominence = str(self.manager.metadata_manager.get(
            self.slot_id - 1,
            'min_peak_prominence',
        ))

        self.ids.freq_shift.state = 'down' if freq_shift else 'normal'
        self.ids.damping.state = 'down' if damping else 'normal'
        self.ids.peak_splitting.state = 'down' if peak_splitting else 'normal'
        self.ids.peak_intensity.state = 'down' if peak_intensity else 'normal'
        self.ids.missing_mode.state = 'down' if missing_mode else 'normal'
        self.ids.added_mode.state = 'down' if added_mode else 'normal'

        self.ids.frequency_shift_limit.ids.label_field.text = frequency_shift_limit
        self.ids.damping_limit.ids.label_field.text = damping_limit
        self.ids.split_frequency_gap.ids.label_field.text = split_frequency_gap
        self.ids.peak_intensity_limit.ids.label_field.text = peak_intensity_limit
        self.ids.peak_matching_tolerance.ids.label_field.text = peak_matching_tolerance
        self.ids.min_peak_distance.ids.label_field.text = min_peak_distance
        self.ids.min_peak_prominence.ids.label_field.text = min_peak_prominence

    def save(self):

        fields = [

            (
                'frequency_shift_limit',
                float(self.ids.frequency_shift_limit.ids.label_field.text)
            ),
            (
                'damping_limit',
                float(self.ids.damping_limit.ids.label_field.text)
            ),
            (
                'split_frequency_gap',
                float(self.ids.split_frequency_gap.ids.label_field.text)
            ),
            (
                'peak_intensity_limit',
                float(self.ids.peak_intensity_limit.ids.label_field.text)
            ),
            (
                'peak_matching_tolerance',
                float(self.ids.peak_matching_tolerance.ids.label_field.text)
            ),
            (
                'min_peak_distance',
                float(self.ids.min_peak_distance.ids.label_field.text)
            ),
            (
                'min_peak_prominence',
                float(self.ids.min_peak_prominence.ids.label_field.text)
            ),

            ('frequency_shift', self.ids.freq_shift.state == 'down'),
            ('damping', self.ids.damping.state == 'down'),
            ('peak_splitting', self.ids.peak_splitting.state == 'down'),
            ('peak_intensity', self.ids.peak_intensity.state == 'down'),
            ('missing_mode', self.ids.missing_mode.state == 'down'),
            ('added_mode', self.ids.added_mode.state == 'down'),

        ]

        for field_name, value in fields:

            if isinstance(value, bool):
                stored_value = value
            else:
                stored_value = float(value)

            self.manager.metadata_manager.put(
                self.slot_id - 1,
                field_name,
                stored_value
            )

        success_dialog = MDDialog(
            title=f'QCT settings saved for slot {self.slot_id}',
            buttons=[MDFlatButton(
                text='OK',
                # Only available KivyMD 1.2.0!
                text_color=self.theme_cls.primary_color,
                theme_text_color='Custom',
                font_size="20sp",
                on_release=lambda _: success_dialog.dismiss()
            )]
        )

        success_dialog.open()
