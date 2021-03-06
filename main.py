#!/usr/bin/env python3
from sys import argv
from os import path as ospath
import models
from pathlib import Path
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QLineEdit, QMessageBox, QMainWindow, QFileSystemModel
from PyQt5.uic import loadUi
import shutil
import modpack
import json

PROJECT_PATH = Path(ospath.dirname(argv[0])).resolve()
INPUT_FOLDER = PROJECT_PATH / Path('input')
SETTINGS_NAME = PROJECT_PATH / 'settings.json'
GAME_PRESET_FOLDER = PROJECT_PATH / 'games'
PRESET_FILE_NAME = 'game_setting.json'
MAIN_UI_PATH = PROJECT_PATH / 'ui' / 'modbuddy.ui'


class Ui(QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        loadUi(MAIN_UI_PATH, self)

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
        self.save_profile_button.clicked.connect(self.write_preset_to_config)
        self.duplicate_profile_button.clicked.connect(self.create_new_mod_table_config)

        # - Game
        self.new_game_button.clicked.connect(self.create_new_game)
        self.load_game_button.clicked.connect(self.load_targeted_game)
        self.initialize_mod.clicked.connect(self.letsgo_mydudes)

        self.update_game_combobox()
        self.init_tablewidget()
        self.retrieve_last_activity()
        self.update_fileview()
        self.show()

    def init_settings(self):
        """ Initial setup for mod buddy"""
        GAME_PRESET_FOLDER.mkdir(exist_ok=True)
        try:
            self.settings = json.loads(Path(SETTINGS_NAME).read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            self.settings = {}
        self.game_setting = {}

    @staticmethod
    def recursive_rmdir(delpath: Path):
        for subpath in sorted(delpath.glob('**/*'), reverse=True):
            if subpath.is_dir():
                subpath.rmdir()
            else:
                subpath.unlink()

    def get_current_game(self) -> str:
        """ Retrieve what game is currently active"""
        return self.game_combobox.currentText()

    def get_current_profile(self) -> str:
        """ Retrieve what profile is currently active"""
        return self.profile_combobox.currentText()

    def update_game_combobox(self):
        """Update information inside the game combobox"""
        self.game_combobox.clear()
        current_game = self.settings.get('lastactivity', {}).get('game')
        index = None
        for i, x in enumerate(GAME_PRESET_FOLDER.glob('*.json')):
            self.game_combobox.addItem(x.stem)
            if current_game == x.stem:
                index = i
        if index:
            self.game_combobox.setCurrentIndex(index)

    def update_profile_combobox(self):
        """Update information inside the preset combobox"""
        self.profile_combobox.clear()
        current_game = self.settings.get('lastactivity', {}).get('profile')
        index = None
        for i, x in enumerate(self.game_setting.get('profiles')):
            self.profile_combobox.addItem(x)
            if current_game == x:
                index = i
        if index:
            self.profile_combobox.setCurrentIndex(index)

    def update_last_activity(self, game: str = "", profile: str = ""):
        """Update the current last_activity and store it

        :param game: Current game, defaults to ""
        :type game: str, optional
        :param profile: Current preset inside game, defaults to ""
        :type profile: str, optional
        """
        last_activity = {
            'game': game or self.get_current_game(),
            'profile': profile or self.get_current_profile()
        }
        self.settings['lastactivity'] = last_activity
        # print(last_activity)
        Path(SETTINGS_NAME).write_text(
            json.dumps(self.settings, indent=4))

    def retrieve_last_activity(self):
        """Update the UI with contents from lastactivity"""
        last = self.settings.get('lastactivity')
        if last:
            game = last.get('game')
            profile = last.get('profile')
            self.load_game(game)
            self.load_profile(profile)

    def create_new_mod_table_config(self):
        """Take the current mod setup presented,
        create a new mod preset and save it to the settings"""
        preset_name, ok = QInputDialog.getText(
            self, "", "Preset name:", QLineEdit.Normal, self.get_current_profile())
        if not ok:
            return

        config = self.game_setting.get('profiles').get(self.get_current_profile())
        self.game_setting.get('profiles')[preset_name] = config

        self.write_preset_to_config()
        self.update_last_activity(profile=preset_name)
        self.load_profile(preset_name)
        self.update_profile_combobox()

    def write_preset_to_config(self):
        """Update the current mod setup to its respective profile"""
        Path(self.target_preset_path).write_text(
            json.dumps(self.game_setting, indent=4))

    def load_profile(self, target_profile: str):
        """Initialize a chosen preset to the mod table

        :param target_profile: A profile that exists inside profiles in 'game_setting.json'
        :type target_profile: str
        """
        self.current_profile = self.game_setting.get('profiles').get(target_profile)
        self.init_tablewidget(target_profile)

    def load_current_profile(self):
        """Initialize the current preset (Chosen in GUI)"""
        preset = self.get_current_profile()
        self.load_profile(preset)
        self.update_last_activity()

    def update_fileview(self):
        """Update the file explorer with current game settings"""
        mod_path = self.game_setting.get('game_mod_folder')
        if not mod_path:
            return
        path = str(Path(mod_path).parent)

        self.fs_mod.setRootPath(path)
        self.file_view.setModel(self.fs_mod)
        self.file_view.setRootIndex(self.fs_mod.index(path))
        self.file_view.expand(self.fs_mod.index(mod_path))

    def create_new_game(self):
        """Start a wizard to create a new game"""
        game_mod_folder_str = QFileDialog.getExistingDirectory(
            self, 'Get mod folder'
        )
        if not game_mod_folder_str:
            return
        game_mod_folder = Path(game_mod_folder_str)
        game_preset_name, ok = QInputDialog.getText(
            self, "", "Game preset name:", QLineEdit.Normal, game_mod_folder.parent.stem)
        if ok:
            QMessageBox.information(self, 'Done', 'Game is set up and ready to go!')

        game_folder = game_mod_folder.parent
        backup_mod_folder = game_folder / '.mods'
        try:
            backup_mod_folder.mkdir()
        except FileExistsError:
            raise

        # Create a backup of the original files, will be used for modding
        initial_mod_content_folder = backup_mod_folder / 'base_content'
        initial_mod_content_folder.mkdir()

        x = modpack.ModPack(
            game_mod_folder, initial_mod_content_folder, case_sensitive=True)
        x.add_mod()

        BASE_CONTENT_NAME = 'Base content'

        preset = {
            'default_mod_folder': str(backup_mod_folder.resolve()),
            'game_mod_folder': str(game_mod_folder.resolve()),
            'profiles': {
                'default': [{
                    "enabled": True,
                    "name": BASE_CONTENT_NAME
                }]
            },
            'mods': {
                BASE_CONTENT_NAME: str(initial_mod_content_folder.resolve())
            }
        }
        Path(GAME_PRESET_FOLDER / f'{game_preset_name}.json').write_text(
            json.dumps(preset, indent=4))
        self.update_last_activity(game_preset_name, 'default')
        self.update_game_combobox()
        self.load_game(game_preset_name)

    def load_game(self, target_preset: str):
        """Load a new game and its presets

        :param target_preset: Name of game (set when creating a new game)
        :type target_preset: str
        """
        self.target_preset_path = GAME_PRESET_FOLDER / f'{target_preset}.json'
        self.game_setting = json.loads((self.target_preset_path).read_text())
        self.mod_dest.setText(self.game_setting.get('game_mod_folder'))
        self.update_profile_combobox()
        self.load_current_profile()
        self.update_fileview()

    def load_targeted_game(self):
        """Load the game selected in GUI"""
        target_game = self.get_current_game()
        self.load_game(target_game)
        self.update_last_activity()

    def install_new_mod(self):
        """Install a new mod already extracted somewhere"""
        self.add_mod(Path(self.game_setting.get('default_mod_folder') or "."))

    def install_new_archived_mod(self):
        """Install a new mod from an archive"""
        archives = QFileDialog.getOpenFileNames(
            self, 'Select archives to be installed', str(Path.home()), "Supported archives (*.zip *.tar)")
        if not archives:
            return
        default_mod_folder = self.game_setting.get('default_mod_folder')
        if not default_mod_folder:
            QMessageBox.warning(self, '', (
                "Sorry, but your settings doesn't have ",
                "a default destination for mods. Is it an old config?"))
        for archive in archives[0]:
            try:
                suff = Path(archive).suffix
                folder_name = Path(archive).stem
                target_folder = Path(default_mod_folder) / folder_name
                shutil.unpack_archive(archive, target_folder)
            except shutil.ReadError:
                QMessageBox.warning(self, '', f'Sorry, but {suff}-archives is not supported')
            else:
                self.add_mod(target_folder)

    def add_mod(self, folder_path: Path):
        """Import a mod to the current game

        :param folder_path: A path representing the 'root' of the mod folder
        :type folder_path: Path
        """
        folder = QFileDialog.getExistingDirectory(self, 'Choose subfolder', str(folder_path))
        if not folder:
            return
        folder_name = Path(folder_path).stem
        text, ok = QInputDialog.getText(
            self, "Get mod name", "Name input of mod:", QLineEdit.Normal, folder_name)
        if ok:
            self.add_row_to_mods(name=text, path=folder)

    def add_row_to_mods(self, name: str, path: Path):
        """Add a given mod to the current game

        :param name: unique name of the mod
        :type name: str
        :param path: A path representing the root of the folder, defaults to Path
        :type path: Path, optional
        """
        self.game_setting.get('mods')[name] = path
        for x in self.game_setting.get('profiles').values():
            x.append({
                'name': name,
                'enabled': False
            })
        self.modmodel.layoutChanged.emit()

    def get_mod_list_row(self):
        return self.mod_list.selectionModel().selectedRows()[0].row()

    def move_row_up(self):
        try:
            row = self.get_mod_list_row()
        except IndexError:
            pass
        self.modmodel.move_target_row_up(row)

    def move_row_down(self):
        try:
            row = self.get_mod_list_row()
        except IndexError:
            pass
        self.modmodel.move_target_row_down(row)

    def init_tablewidget(self, profile=""):
        """Initialize the table with mods

        :param profile: Profile name, defaults to ""
        :type profile: str, optional
        """
        if not profile:
            profile = self.get_current_profile()
        self.modmodel = models.ModModel(
            settings=self.game_setting, profile=profile)
        self.mod_list.setModel(self.modmodel)

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
            self.recursive_rmdir(del_path_target)
            QMessageBox.information(self, 'Done', 'Mods are cleaned!')

    def letsgo_mydudes(self):
        """Commit the current setup and fire the modifications"""
        profile = self.game_setting.get('profiles').get(self.get_current_profile())
        mod_list = self.game_setting.get('mods')
        enabled_mods = ',\n'.join([x.get('name') for x in profile if x.get('enabled')])
        target_mod_folder = Path(self.game_setting["game_mod_folder"])

        x = QMessageBox.question(self, '', (
            'This will delete all content inside:\n\n'
            f'{target_mod_folder.resolve()}\n'
            'and commit these mods afterwards:\n\n'
            f'{enabled_mods}\n\n'
            f'Are you sure about this?'
        ))
        if x == QMessageBox.Yes:
            self.write_preset_to_config()
            try:
                self.recursive_rmdir(target_mod_folder.resolve())
                modpack.initialize_configs(
                    profile, mod_list, INPUT_FOLDER, Path(self.game_setting['game_mod_folder']))
            except Exception as e:
                QMessageBox.warning(self, '', f'Something went wrong\n{e}')
            else:
                QMessageBox.information(self, 'Done', 'Mods are loaded!')


if __name__ == "__main__":
    app = QtWidgets.QApplication(argv)
    window = Ui()
    app.exec_()
