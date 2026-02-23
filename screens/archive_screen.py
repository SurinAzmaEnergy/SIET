import os
import re
import mimetypes
import shutil
import math
import platform
import psutil
import time
import threading
from types import MethodType

import numpy as np
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.window import Window
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.button import MDFlatButton
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.datatables import MDDataTable
from kivy.input.providers.mouse import MouseMotionEvent
from kivymd.uix.datatables.datatables import (
    TableData,
    TableRecycleGridLayout
)


TableRecycleGridLayout.select_row = MethodType(
    lambda self, _: None,
    TableRecycleGridLayout
)


class OneTimeTriggererFlatbutton(MDFlatButton):
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if not isinstance(touch, MouseMotionEvent):
                super().on_touch_down(touch)



def _get_checked_rows(self):
    checked_rows = []
    total_cols = self.total_col_headings
    for page in self.current_selection_check:
        if page >= len(self._row_data_parts):
            continue
        page_data = self._row_data_parts[page]
        for index in self.current_selection_check[page]:
            row_in_page = index // total_cols
            if row_in_page < len(page_data):
                checked_rows.append(page_data[row_in_page])
    return checked_rows


class CustomDataTable(MDDataTable):
    def __init__(self, screen, **kwargs):
        super().__init__(**kwargs)
        self.screen = screen
        self.stop_propagation = False
        self.table_data._get_row_checks = MethodType(
            _get_checked_rows,
            self.table_data
        )

    def on_row_press(self, cell):
        Window.release_all_keyboards()
        try:
            if not self.stop_propagation:
                path_candidate = os.path.join(
                    self.screen.current_path, cell.text)
                if os.path.isdir(path_candidate):
                    self.screen.change_directory(path_candidate)
        finally:
            # Always reset the flag after handling the row press!
            self.stop_propagation = False

    def on_check_press(self, row):
        self.stop_propagation = True
        self.screen.update_buttons_state()
        self.screen.update_copy_on_usb_button_state()
        self.screen.update_select_deselect_buttons()


class ArchiveScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.table = None
        self.archive_path = 'Archive/'
        self.current_path = self.archive_path

    def on_enter(self):
        if not self.table:
            self.setup_table()
            self.update_breadcrumbs()
        self.update_buttons_state()
        self.update_new_folder_button_state()
        self.get_removable_drives()
        self.update_copy_on_usb_button_state()
        self.update_select_deselect_buttons()

    def setup_table(self):
        self.table = CustomDataTable(
            screen=self,
            elevation=0,
            check=True,
            use_pagination=True,
            background_color_header=(.23, .29, .36, .5),
            row_data=self.list_contents(),
            column_data=[
                ('Name', dp(100)),
                ('Type', dp(30)),
                ('Size', dp(20))
            ],
        )
        self.ids.data_table.add_widget(self.table)

    def update_breadcrumbs(self):
        self.ids.breadcrumb.text = self.current_path

    def change_directory(self, target):
        self.current_path = target
        self.update_breadcrumbs()
        self.refresh()

    def refresh(self):
        self.table.update_row_data(
            self.table,
            self.list_contents()
        )
        self.update_buttons_state()
        self.update_new_folder_button_state()
        self.update_copy_on_usb_button_state()

    def back(self):
        norm_current = os.path.normpath(self.current_path)
        norm_archive = os.path.normpath(self.archive_path)
        if norm_current != norm_archive:
            self.current_path = os.path.dirname(self.current_path)
            self.update_breadcrumbs()
            self.refresh()
        else:
            self.manager.current = 'home'
            self.manager.transition.direction = 'right'

    def create_directory(self):
        os.makedirs(
            os.path.join(
                self.current_path,
                self.create_directory_dialog.content_cls.text
            ),
            exist_ok=True
        )
        self.create_directory_dialog.dismiss()
        self.refresh()

    def rename_item(self, old_path, new_name):
        new_path = os.path.join(self.current_path, new_name)
        try:
            os.rename(old_path, new_path)
        except:
            pass
        self.rename_dialog.dismiss()
        self.refresh()

    def delete_items(self):
        for path in self.files_to_delete:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        self.delete_dialog.dismiss()
        self.refresh()

    def set_default(self, new_path):
        self.manager.default = new_path
        self.manager.config_manager.set('SIET1010', 'archive_path', new_path)
        self.refresh()
        self.set_default_dialog.dismiss()

    def show_create_directory_dialog(self):
        print('Directory')
        self.create_directory_dialog = MDDialog(
            title='New Folder',
            type='custom',
            pos_hint={'center_x': .5, 'center_y': .8},
            content_cls=MDTextField(mode='round'),
            buttons=[
                MDFlatButton(
                    text='CANCEL',
                    # Only available KivyMD 1.2.0!
                    text_color=self.theme_cls.error_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.create_directory_dialog.dismiss()
                ),
                MDFlatButton(
                    text='OK',
                    # Only available in KivyMD 1.2.0!
                    text_color=self.theme_cls.primary_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.create_directory()
                )
            ]
        )
        self.create_directory_dialog.open()

    def show_rename_dialog(self):
        print('Rename')
        selected_rows = self.table.get_row_checks()
        if not selected_rows or len(selected_rows) != 1:
            return
        old_name = selected_rows[0][0]
        old_path = os.path.join(self.current_path, old_name)
        if old_path == self.manager.default:
            return
        self.rename_dialog = MDDialog(
            title='Rename',
            type='custom',
            pos_hint={'center_x': .5, 'center_y': 0.8},
            content_cls=MDTextField(
                mode='round',
                text=old_name
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
                    on_release=lambda _: self.rename_item(
                        old_path,
                        self.rename_dialog.content_cls.text
                    ),
                )
            ]
        )
        self.rename_dialog.open()

    def show_delete_dialog(self):
        print('Delete!')
        # TODO: This function may need some improvments!
        selected_rows = self.table.get_row_checks()
        if not selected_rows:
            return
        self.files_to_delete = [
            os.path.join(self.current_path, row[0])
            for row in selected_rows
            if os.path.normpath(row[0]) != self.manager.default
            and re.sub(r'\[.*?\]', '', row[1]).strip() != 'Default Folder'
        ]
        if len(self.files_to_delete) > 20:
            message = 'More than 20 files is going to deleted!'
        else:
            message = '\n'.join(self.files_to_delete)
        self.delete_dialog = MDDialog(
            title='Delete',
            text=message,
            buttons=[
                MDFlatButton(
                    text='CANCEL',
                    # Only available KivyMD 1.2.0!
                    text_color=self.theme_cls.error_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.delete_dialog.dismiss()
                ),
                MDFlatButton(
                    text='OK',
                    # Only available in KivyMD 1.2.0!
                    text_color=self.theme_cls.primary_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.delete_items()
                )
            ]
        )
        self.delete_dialog.open()

    def show_set_default_dialog(self):
        selected_rows = self.table.get_row_checks()
        if not selected_rows or len(selected_rows) != 1:
            return
        default_candidate = os.path.join(
            self.current_path, selected_rows[0][0])
        if default_candidate == self.manager.default:
            return
        if os.path.isfile(default_candidate):
            return
        self.set_default_dialog = MDDialog(
            title='Set as Default Folder?',
            text=default_candidate,
            buttons=[
                MDFlatButton(
                    text='NO',
                    text_color=self.theme_cls.error_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.set_default_dialog.dismiss()
                ),
                MDFlatButton(
                    text='YES',
                    text_color=self.theme_cls.primary_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.set_default(default_candidate)
                )
            ]
        )
        self.set_default_dialog.open()

    def list_contents(self):
        try:
            self.contents = []
            with os.scandir(self.current_path) as entries:
                for entry in entries:
                    if entry.is_dir():
                        file_type = (
                            f'[color=#FF0000]Default Folder[/color]'
                            if entry.path == self.manager.default
                            else 'Folder'
                        )
                        size = ArchiveScreen.get_directory_size(entry.path)
                    else:
                        file_type, _ = mimetypes.guess_type(entry.name)
                        file_type = file_type or 'Unknown'
                        size = entry.stat().st_size
                    self.contents.append((
                        entry.name,
                        file_type,
                        ArchiveScreen.human_readable_size(size)
                    ))
            return self.contents
        # TODO: Notify the user about `PermissionError` and `FileNotFoundErrors`.
        except FileNotFoundError:
            return []
        except PermissionError:
            return []

    def can_create_new_folder(self):
        try:
            count = sum(1 for entry in os.scandir(
                self.current_path) if entry.is_dir())
            return count < 5
        except (PermissionError, FileNotFoundError):
            return False

    def update_new_folder_button_state(self):
        self.ids.new_folder_button.disabled = not self.can_create_new_folder()

    def update_buttons_state(self):
        selected = self.table.get_row_checks()
        num_selected = len(selected)

        if num_selected == 1:
            selected_path = os.path.join(self.current_path, selected[0][0])
            if not os.path.isdir(selected_path):
                with open(selected_path, 'r') as f:
                    first_line = f.readline().strip()
                    if first_line == '# WAVEFORM':
                        self.ids.import_button.disabled = False
                    else:
                        self.ids.import_button.disabled = True
        else:
            self.ids.import_button.disabled = True


        if num_selected == 1:
            selected_path = os.path.join(self.current_path, selected[0][0])
            if selected_path != self.manager.default:
                self.ids.rename_button.disabled = False
            else:
                self.ids.rename_button.disabled = True
        else:
            self.ids.rename_button.disabled = True

        delete_disabled = True
        if num_selected > 0:
            default_path = self.manager.default
            has_default = any(os.path.join(self.current_path,
                              row[0]) == default_path for row in selected)
            delete_disabled = has_default
        self.ids.delete_button.disabled = delete_disabled

        set_default_disabled = True
        if num_selected == 1:
            name = selected[0][0]
            item_path = os.path.join(self.current_path, name)
            if os.path.isdir(item_path) and item_path != self.manager.default:
                set_default_disabled = False
        self.ids.set_default_button.disabled = set_default_disabled

    @staticmethod
    def get_directory_size(directory):
        total_size = 0
        for entry in os.scandir(directory):
            if entry.is_dir():
                total_size += ArchiveScreen.get_directory_size(entry.path)
            else:
                total_size += entry.stat().st_size
        return total_size

    @staticmethod
    def human_readable_size(size_in_bytes):
        if size_in_bytes == 0:
            return '0 B'
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        power = int(math.log(size_in_bytes, 1024))
        power = min(power, len(units) - 1)
        size = size_in_bytes / (1024 ** power)
        return f'{size:.2f} {units[power]}'

    def get_removable_drives(self):
        removable_drives = []
        system = platform.system()
        partitions = psutil.disk_partitions()
        for p in partitions:
            if (system == 'Linux' and ('media' in p.mountpoint or 'removable' in p.opts)):
                usage = psutil.disk_usage(p.mountpoint)
                removable_drives.append({
                    'name': os.path.basename(os.path.normpath(p.mountpoint)),
                    'mountpoint': p.mountpoint,
                    'device': p.device,
                    'fstype': p.fstype,
                    'total_size': usage.total,
                    'used': usage.used,
                    'free': usage.free
                })
        return removable_drives

    def update_copy_on_usb_button_state(self):
        self.get_removable_drives()
        self.ids.archive_panel.ids.right_button.disabled = False if self.table.get_row_checks() else True

    def update_select_deselect_buttons(self):
        row_checks = self.table.get_row_checks()
        total_rows = len(self.table.row_data)
        self.ids.select_all_button.disabled = len(row_checks) == total_rows
        self.ids.deselect_all_button.disabled = not row_checks

    def show_copy_on_usb_dialog(self):
        if not self.table.get_row_checks():
            return
        removable_drives = self.get_removable_drives()
        if removable_drives:
            if len(removable_drives) == 1:
                self.files_to_copy = [
                    os.path.join(self.current_path, row[0])
                    for row in self.table.get_row_checks()
                ]
                if len(self.files_to_copy) > 20:
                    message = 'More than 20 files is going to copied!'
                else:
                    message = '\n'.join(self.files_to_copy)
                self.copy_on_usb_dialog = MDDialog(
                    title=f'Copy on {removable_drives[0]["name"]}?',
                    text=message,
                    buttons=[
                        MDFlatButton(
                            text='CANCEL',
                            # Only available KivyMD 1.2.0!
                            text_color=self.theme_cls.error_color,
                            theme_text_color='Custom',
                            on_release=lambda _: self.copy_on_usb_dialog.dismiss()
                        ),
                        OneTimeTriggererFlatbutton(
                            text='OK',
                            # Only available in KivyMD 1.2.0!
                            text_color=self.theme_cls.primary_color,
                            theme_text_color='Custom',
                            on_release=lambda _: self.copy_items(
                                self.files_to_copy,
                                removable_drives[0]['mountpoint']
                            )
                        )
                    ]
                )
                self.copy_on_usb_dialog.open()
            else:
                pass

        else:
            self.copy_on_usb_dialog = MDDialog(
                title='USB Not Detected!',
                buttons=[MDFlatButton(
                    text='OK',
                    # Only available KivyMD 1.2.0!
                    text_color=self.theme_cls.primary_color,
                    theme_text_color='Custom',
                    on_release=lambda _: self.copy_on_usb_dialog.dismiss()
                )]
            )
            self.copy_on_usb_dialog.open()

    def show_error_dialog(self, message):
        error_dialog = MDDialog(
            title='Error',
            text=message,
            buttons=[
                MDFlatButton(
                    text='OK',
                    on_release=lambda _: error_dialog.dismiss()
                )
            ]
        )
        error_dialog.open()

    @staticmethod
    def count_files_recursive(path):
        if os.path.isfile(path):
            return 1
        total_files = 0
        for entry in os.scandir(path):
            if entry.is_file():
                total_files += 1
            elif entry.is_dir():
                total_files += ArchiveScreen.count_files_recursive(entry.path)
        return total_files

    def copy_items(self, src_list, dst_path):
        total_files = 0
        for src in src_list:
            total_files += ArchiveScreen.count_files_recursive(src)

        self.progress_dialog = MDDialog(
            title='Copying Files...',
            type='custom',
            auto_dismiss=False,
            buttons=[
                MDFlatButton(
                    text='CANCEL',
                    theme_text_color='Custom',
                    text_color=self.theme_cls.error_color,
                    on_release=lambda _: self.cancel_copy()
                ),
                MDFlatButton(
                    text='OK',
                    theme_text_color='Custom',
                    text_color=self.theme_cls.primary_color,
                    on_release=lambda _: self.progress_dialog.dismiss()
                )
            ]
        )
        self.progress_bar = MDProgressBar()
        self.progress_box = MDBoxLayout(padding=15, size_hint=(1, .3))
        self.progress_box.add_widget(self.progress_bar)
        self.progress_dialog.add_widget(self.progress_box)
        self.progress_dialog.open()

        self.cancel_flag = False
        self.copied_files = 0

        def copy_recursive(src, dst):
            if self.cancel_flag:
                return

            if os.path.isdir(src):
                os.makedirs(dst, exist_ok=True)
                for entry in os.scandir(src):
                    new_src = entry.path
                    new_dst = os.path.join(dst, entry.name)
                    copy_recursive(new_src, new_dst)
            else:
                shutil.copy2(src, dst)
                self.copied_files += 1
                progress = (self.copied_files / total_files) * 100
                Clock.schedule_once(lambda dt: self.update_progress(progress))

        def copy_in_thread(src_list, dst_path):
            try:
                for src in src_list:
                    if self.cancel_flag:
                        break

                    dest = os.path.join(dst_path, os.path.basename(src))
                    if os.path.exists(dest):
                        self.progress_dialog.dismiss()
                        raise Exception(
                            f'Destination already exists: {os.path.basename(dest)}'
                        )
                    copy_recursive(src, dest)

                # Clock.schedule_once(lambda dt: self.progress_dialog.dismiss())
                Clock.schedule_once(lambda dt: self.refresh())
            except Exception as e:
                error_message = str(e)
                Clock.schedule_once(
                    lambda dt, msg=error_message: self.show_error_dialog(msg))
            finally:
                # Clock.schedule_once(lambda dt: self.progress_dialog.dismiss())
                # self.progress_dialog.dismiss()
                self.progress_dialog.title = 'Done!'

        threading.Thread(
            target=copy_in_thread,
            args=(src_list, dst_path),
            daemon=True
        ).start()
        # self.progress_dialog.dismiss()
        self.copy_on_usb_dialog.dismiss()

    def update_progress(self, progress):
        self.progress_bar.value = progress

    def cancel_copy(self):
        self.cancel_flag = True
        self.progress_dialog.dismiss()

    def import_wave(self):

        selected_rows = self.table.get_row_checks()
        if not selected_rows or len(selected_rows) != 1:
            return

        file_name = selected_rows[0][0]
        file_path = os.path.join(self.current_path, file_name)

        with open(file_path, 'r') as file:
            signature = file.readline().strip()

        if not signature == '# WAVEFORM': return # TODO: Show Error Dialog!

        self.manager.app.signal_processor.all_pass_value = self.manager.config_manager.getboolean(
            'SIET1010',
            'all_pass'
        )

        self.manager.app.signal_processor.low_frequency = float(self.manager.config_manager.get(
            'SIET1010',
            'low_frequency'
        ))

        self.manager.app.signal_processor.high_frequency = float(self.manager.config_manager.get(
            'SIET1010',
            'high_frequency'
        ))

        self.manager.app.signal_processor.distance = float(self.manager.config_manager.get(
            'SIET1010',
            'distance'
        ))

        time_ms, normalized_signal = np.loadtxt(
            file_path,
            delimiter=',',
            skiprows=2,
            unpack=True
        )

        self.manager.app.signal_processor.normalized_signal = normalized_signal
        self.manager.app.signal_processor.time_ms = time_ms

        (
            self.manager.app.signal_processor.fft_data,
            self.manager.app.signal_processor.fft_freqs
        ) = self.manager.app.signal_processor.calculate_fft(normalized_signal, importing=True)


        peaks = self.manager.app.signal_processor.get_peaks()
        peaks = self.manager.app.signal_processor.fft_frequencies[peaks]

        self.manager.app.update_ui(False, normalized_signal, peaks, True)

        self.manager.current = 'home'
        self.manager.transition.direction = 'left'

