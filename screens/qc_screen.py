import json
from pathlib import Path

from kivymd.uix.screen import MDScreen


class QCScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metadata = {}

    def on_enter(self, *args):
        self.set_names()
        self.update_qct_buttons()

    def set_names(self):
        for i in range(8):
            self.ids[
                f'slot{i+1}_name'
            ].text = self.manager.metadata_manager.get(i, 'name')

    def update_qct_buttons_bak(self):
        for i in range(8):
            btn = self.ids[f'slot{i+1}_qct']
            ref = self.manager.metadata_manager.get(i, 'reference')
            if ref == '':
                btn.disabled = True
                continue
            else:
                ref_path = Path(ref)
                if ref_path.exists():
                    btn.disabled = False

    def update_qct_buttons(self):
        for i in range(8):
            btn = self.ids[f'slot{i+1}_qct']
            ref = self.manager.metadata_manager.get(i, 'reference')

            # Disable if no reference path OR file doesn't exist
            btn.disabled = (not ref or not Path(ref).exists())

    def open_general_settings(self):
        self.manager.settings_caller = 'qc'
        self.manager.transition.direction = "up"
        self.manager.current = "general_settings"
