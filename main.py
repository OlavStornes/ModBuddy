from pathlib import Path
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QLineEdit, QMessageBox, QTableWidgetItem, QMainWindow
from PyQt5.uic import loadUi
import modpack
import json
import sys

INPUT_FOLDER = Path('input')
SETTINGS_NAME = 'settings.json'
ROOT_FOLDER_NAME = 'gamedata'
OUTPUT_FOLDER = Path('output') / ROOT_FOLDER_NAME
GAME_PRESET_FOLDER = Path('games')
PRESET_FILE_NAME = 'modlist.json'


class Ui(QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        loadUi('ui/modbuddy.ui', self)

        # Load settings
        self.settings = json.loads(Path(SETTINGS_NAME).read_text())
        self.game_setting = {}

        # Initialize some components
        self.filesystem_model = QtWidgets.QFileSystemModel()

        # Connect buttons
        self.move_up.clicked.connect(self.move_row_up)
        self.move_down.clicked.connect(self.move_row_down)
        self.new_mod_button.clicked.connect(self.install_new_mod)

        # - Game profiles
        self.load_profile_button.clicked.connect(self.load_current_profile)
        self.save_profile_button.clicked.connect(self.save_mod_table_config)

        # - Game
        self.new_game_button.clicked.connect(self.create_new_game)
        self.load_game_button.clicked.connect(self.load_targeted_game)
        self.initialize_mod.clicked.connect(self.letsgo_mydudes)

        self.update_fileview(str(OUTPUT_FOLDER))
        self.update_game_combobox()
        self.init_tablewidget()
        self.retrieve_last_activity()
        self.show()

    @staticmethod
    def export_modlist_to_list(table) -> dict:
        output = []
        for i in range(table.rowCount()):
            output.append({
                'name': table.item(i, 0).text(),
                'folder_name': table.item(i, 1).text(),
                'subfolder': table.item(i, 2).text(),
                'enabled': bool(table.item(i, 3).checkState())
            })

        return output

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

    def update_fileview(self, path):
        index = self.filesystem_model.index(path)
        self.filesystem_model.setRootPath(path)
        self.file_view.setModel(self.filesystem_model)
        self.file_view.expand(index)

    def create_new_game(self):
        game_path = QFileDialog.getExistingDirectory(self, 'Get game folder')
        game_mod_folder = QFileDialog.getExistingDirectory(
            self, 'Get volatile mod folder', game_path
        )
        game_preset_name, ok = QInputDialog.getText(
            self, "", "Game preset name:", QLineEdit.Normal, Path(game_path).stem)
        if ok:
            QMessageBox.information(self, 'Done', 'Game is set up and ready to go!')

        self.game_preset_folder = GAME_PRESET_FOLDER / game_preset_name
        self.game_preset_folder.mkdir()

        preset = {
            'game_root_folder': game_path,
            'game_mod_folder': game_mod_folder,
            'profiles': {
                'default': {}
            },
            'mods': []
        }
        Path(self.game_preset_folder / PRESET_FILE_NAME).write_text(
            json.dumps(preset, indent=4))
        self.update_game_combobox()

    def load_game(self, target_preset):
        self.target_preset_folder = GAME_PRESET_FOLDER / target_preset
        self.game_setting = json.loads((self.target_preset_folder / PRESET_FILE_NAME).read_text())
        self.update_profile_combobox()

    def load_targeted_game(self):
        target_game = self.get_current_game()
        self.load_game(target_game)
        self.update_last_activity()

    def install_new_mod(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Install mod')
        if not folder_path:
            return
        subfolder = QFileDialog.getExistingDirectory(self, 'Choose subfolder', folder_path)
        if not subfolder:
            return
        folder_name = Path(folder_path).stem
        text, ok = QInputDialog.getText(
            self, "Get mod name", "Name input of mod:", QLineEdit.Normal, folder_name)
        if ok:
            self.add_row_to_mods({
                'name': text,
                'folder_name': folder_name,
                'subfolder': subfolder,
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
        self.mod_list.setItem(i, 1, QTableWidgetItem(row.get('folder_name')))
        self.mod_list.setItem(i, 2, QTableWidgetItem(row.get('subfolder')))
        self.mod_list.setItem(i, 3, QTableWidgetItem(chkBoxItem))

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
        current_preset = self.game_setting.get(self.get_current_profile()) or []
        for row in current_preset:
            self.add_row_to_mods(row)

    def letsgo_mydudes(self):
        conf = self.export_modlist_to_list(self.mod_list)

        x = QMessageBox.question(self, '', "are u sure")
        if x == QMessageBox.Yes:
            try:
                modpack.initialize_configs(conf, INPUT_FOLDER, OUTPUT_FOLDER)
            except Exception:
                QMessageBox.warning(self, '', 'Something went wrong')
            else:
                QMessageBox.information(self, 'Done', 'Mods are loaded!')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()
