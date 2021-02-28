from pathlib import Path
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QLineEdit, QMessageBox, QTableWidgetItem, QMainWindow, QFileSystemModel
from PyQt5.uic import loadUi
import shutil
import modpack
import json
import sys

INPUT_FOLDER = Path('input')
SETTINGS_NAME = 'settings.json'
ROOT_FOLDER_NAME = 'gamedata'
OUTPUT_FOLDER = Path('output') / ROOT_FOLDER_NAME
GAME_PRESET_FOLDER = Path('games')
PRESET_FILE_NAME = 'game_setting.json'


class Ui(QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        loadUi('ui/modbuddy.ui', self)

        self.init_settings()

        # Initialize some components
        self.fs_mod = QFileSystemModel()

        # Connect buttons
        self.move_up.clicked.connect(self.move_row_up)
        self.move_down.clicked.connect(self.move_row_down)
        self.new_mod_button.clicked.connect(self.install_new_mod)
        self.new_mod_archived_button.clicked.connect(self.install_new_archived_mod)
        self.clean_modfolder_button.clicked.connect(self.clean_target_modfolder)

        # - Game profiles
        self.load_profile_button.clicked.connect(self.load_current_profile)
        self.save_profile_button.clicked.connect(self.save_mod_table_config)

        # - Game
        self.new_game_button.clicked.connect(self.create_new_game)
        self.load_game_button.clicked.connect(self.load_targeted_game)
        self.initialize_mod.clicked.connect(self.letsgo_mydudes)

        self.update_game_combobox()
        self.init_tablewidget()
        self.retrieve_last_activity()
        self.update_fileview()
        self.show()

    @staticmethod
    def export_modlist_to_list(table) -> dict:
        output = []
        for i in range(table.rowCount()):
            output.append({
                'name': table.item(i, 0).text(),
                'path': table.item(i, 1).text(),
                'enabled': bool(table.item(i, 2).checkState())
            })

        return output

    def init_settings(self):
        try:
            self.settings = json.loads(Path(SETTINGS_NAME).read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            self.settings = {}
        self.game_setting = {}

    def get_current_game(self) -> str:
        return self.game_combobox.currentText()

    def get_current_profile(self) -> str:
        return self.profile_combobox.currentText()

    def update_game_combobox(self):
        self.game_combobox.clear()
        for x in GAME_PRESET_FOLDER.iterdir():
            self.game_combobox.addItem(x.stem)

    def update_last_activity(self):
        last_activity = {
            'game': self.get_current_game(),
            'profile': self.get_current_profile()
        }
        self.settings['lastactivity'] = last_activity
        print("updated")
        print(last_activity)
        Path(SETTINGS_NAME).write_text(
            json.dumps(self.settings, indent=4))

    def retrieve_last_activity(self):

        last = self.settings.get('lastactivity')
        if last:
            game = last.get('game')
            profile = last.get('profile')
            self.load_game(game)
            self.load_profile(profile)

    def update_profile_combobox(self):
        self.profile_combobox.clear()
        for x in self.game_setting.get('profiles'):
            self.profile_combobox.addItem(x)

    def save_mod_table_config(self):
        preset_name, ok = QInputDialog.getText(
            self, "", "Preset name:", QLineEdit.Normal, self.get_current_profile())
        if not ok:
            return

        config = self.export_modlist_to_list(self.mod_list)
        self.game_setting[preset_name] = config

        Path(self.target_preset_folder / PRESET_FILE_NAME).write_text(
            json.dumps(self.game_setting, indent=4))

    def load_profile(self, target_profile: str):
        self.current_profile = self.game_setting.get(target_profile)
        self.init_tablewidget()

    def load_current_profile(self):
        preset = self.get_current_profile()
        self.load_profile(preset)
        self.update_last_activity()

    def update_fileview(self):
        path = self.game_setting.get('game_root_folder')
        mod_path = self.game_setting.get('game_mod_folder')
        print(f"updating path {path}")

        self.fs_mod.setRootPath(path)
        self.file_view.setModel(self.fs_mod)
        self.file_view.setRootIndex(self.fs_mod.index(path))
        self.file_view.expand(self.fs_mod.index(mod_path))

    def create_new_game(self):
        game_path = QFileDialog.getExistingDirectory(self, 'Get game folder')
        if not game_path:
            return
        game_mod_folder = QFileDialog.getExistingDirectory(
            self, 'Get volatile mod folder', game_path
        )
        if not game_mod_folder:
            return
        game_preset_name, ok = QInputDialog.getText(
            self, "", "Game preset name:", QLineEdit.Normal, Path(game_path).stem)
        if ok:
            QMessageBox.information(self, 'Done', 'Game is set up and ready to go!')

        game_preset_folder = GAME_PRESET_FOLDER / game_preset_name
        game_preset_folder.mkdir()

        preset = {
            'game_preset_folder': str(game_preset_folder.resolve()),
            'game_root_folder': game_path,
            'game_mod_folder': game_mod_folder,
            'profiles': {
                'default': {}
            },
            'mods': []
        }
        Path(game_preset_folder / PRESET_FILE_NAME).write_text(
            json.dumps(preset, indent=4))
        self.update_game_combobox()
        self.update_fileview()

    def load_game(self, target_preset):
        self.target_preset_folder = GAME_PRESET_FOLDER / target_preset
        self.game_setting = json.loads((self.target_preset_folder / PRESET_FILE_NAME).read_text())
        self.mod_dest.setText(self.game_setting.get('game_root_folder'))
        self.update_profile_combobox()
        self.load_current_profile()
        self.update_fileview()

    def load_targeted_game(self):
        target_game = self.get_current_game()
        self.load_game(target_game)
        self.update_last_activity()

    def install_new_mod(self):
        self.add_mod(Path(GAME_PRESET_FOLDER / self.game_setting.get('game_preset_folder')))

    def install_new_archived_mod(self):
        archives = QFileDialog.getOpenFileNames(self, 'Select archives to be installed', str(Path.home()))
        if not archives:
            return
        for archive in archives[0]:
            try:
                suff = Path(archive).suffix
                folder_name = Path(archive).stem
                target_folder = (self.target_preset_folder / folder_name)
                shutil.unpack_archive(archive, target_folder)
            except shutil.ReadError:
                QMessageBox.warning(self, '', f'Sorry, but {suff}-archives is not supported')
            else:
                self.add_mod(target_folder)

    def add_mod(self, folder_path: Path):
        folder = QFileDialog.getExistingDirectory(self, 'Choose subfolder', str(folder_path))
        if not folder:
            return
        folder_name = Path(folder_path).stem
        text, ok = QInputDialog.getText(
            self, "Get mod name", "Name input of mod:", QLineEdit.Normal, folder_name)
        if ok:
            self.add_row_to_mods({
                'name': text,
                'path': folder,
                'enabled': False
            })

    def add_row_to_mods(self, row: dict):
        i = self.mod_list.rowCount()
        self.mod_list.insertRow(i)
        chkBoxItem = QTableWidgetItem()
        chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        is_enabled = row.get('enabled')
        if is_enabled:
            chkBoxItem.setCheckState(QtCore.Qt.Checked)
        else:
            chkBoxItem.setCheckState(QtCore.Qt.Unchecked)
        self.mod_list.setItem(i, 0, QTableWidgetItem(row.get('name')))
        self.mod_list.setItem(i, 1, QTableWidgetItem(row.get('path')))
        self.mod_list.setItem(i, 2, QTableWidgetItem(chkBoxItem))
        self.mod_list.resizeColumnsToContents()

    def move_row_up(self):
        row = self.mod_list.currentRow()
        column = self.mod_list.currentColumn()
        if row > 0:
            self.mod_list.insertRow(row - 1)
            for i in range(self.mod_list.columnCount()):
                self.mod_list.setItem(
                    row - 1, i, self.mod_list.takeItem(row + 1, i))
                self.mod_list.setCurrentCell(row - 1, column)
            self.mod_list.removeRow(row + 1)

    def move_row_down(self):
        row = self.mod_list.currentRow()
        column = self.mod_list.currentColumn()
        if row < self.mod_list.rowCount() - 1:
            self.mod_list.insertRow(row + 2)
            for i in range(self.mod_list.columnCount()):
                self.mod_list.setItem(row + 2, i, self.mod_list.takeItem(row, i))
                self.mod_list.setCurrentCell(row + 2, column)
            self.mod_list.removeRow(row)

    def init_tablewidget(self):
        self.mod_list.clearContents()
        self.mod_list.setRowCount(0)
        current_preset = self.game_setting.get(self.get_current_profile()) or []
        for row in current_preset:
            self.add_row_to_mods(row)

    def clean_target_modfolder(self):
        target_modfolder = Path(self.game_setting.get('game_mod_folder'))
        if not target_modfolder:
            QMessageBox.warning(self, '', 'No target modfolder found')
        else:
            del_path_target = target_modfolder.resolve()
            x = QMessageBox.question(
                self, 'DELETING FOLDER', f"Are you sure you want to delete \
everything inside this folder?\n{del_path_target}")

        if x == QMessageBox.Yes:
            for subpath in sorted(del_path_target.glob('**/*'), reverse=True):
                if subpath.is_dir():
                    subpath.rmdir()
                else:
                    subpath.unlink()
            QMessageBox.information(self, 'Done', 'Mods are cleaned!')

    def letsgo_mydudes(self):
        conf = self.export_modlist_to_list(self.mod_list)

        x = QMessageBox.question(self, '', "are u sure")
        if x == QMessageBox.Yes:
            try:
                modpack.initialize_configs(conf, INPUT_FOLDER, self.game_setting['game_mod_folder'])
            except Exception:
                QMessageBox.warning(self, '', 'Something went wrong')
            else:
                QMessageBox.information(self, 'Done', 'Mods are loaded!')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()
