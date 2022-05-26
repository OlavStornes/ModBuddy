#!/usr/bin/env python3
import sys
from os import path as ospath
from fomod import FomodParser
import models
from pathlib import Path
from PySide6.QtWidgets import QFileDialog, QInputDialog, QLineEdit, QMessageBox, QMainWindow, QFileSystemModel, QApplication
from PySide6.QtCore import QFile, QIODevice, QCoreApplication, Qt
from PySide6.QtUiTools import QUiLoader
import shutil
import modpack
import json

PROJECT_PATH = Path(ospath.dirname(sys.argv[0])).resolve()
INPUT_FOLDER = PROJECT_PATH / Path('input')
SETTINGS_NAME = PROJECT_PATH / 'settings.json'
GAME_PRESET_FOLDER = PROJECT_PATH / 'games'
PRESET_FILE_NAME = 'game_setting.json'
MAIN_UI_PATH = PROJECT_PATH / 'ui' / 'modbuddy.ui'

ENABLED_COLUMN = 0
MODNAME_COLUMN = 1
PATH_COLUMN = 2


class Modbuddy():
    def __init__(self, ui: QMainWindow):

        self.ui = ui

        self.init_settings()

        # Initialize some components
        self.fs_mod = QFileSystemModel()

        # Connect buttons
        self.ui.move_up.clicked.connect(self.move_row_up)
        self.ui.move_down.clicked.connect(self.move_row_down)
        self.ui.new_mod_button.clicked.connect(self.install_new_mod)
        self.ui.new_mod_archived_button.clicked.connect(self.install_new_archived_mod)
        self.ui.clean_modfolder_button.clicked.connect(self.clean_target_modfolder)

        # - Game profiles
        self.ui.load_profile_button.clicked.connect(self.load_current_profile)
        self.ui.save_profile_button.clicked.connect(self.write_preset_to_config)
        self.ui.duplicate_profile_button.clicked.connect(self.create_new_mod_table_config)

        # - Game
        self.ui.new_game_button.clicked.connect(self.create_new_game)
        self.ui.load_game_button.clicked.connect(self.load_targeted_game)
        self.ui.initialize_mod.clicked.connect(self.letsgo_mydudes)

        self.update_game_combobox()
        self.init_tablewidget()
        self.retrieve_last_activity()
        self.update_fileview()


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
        return self.ui.game_combobox.currentText()

    def get_current_profile(self) -> str:
        """ Retrieve what profile is currently active"""
        return self.ui.profile_combobox.currentText()

    def update_game_combobox(self):
        """Update information inside the game combobox"""
        self.ui.game_combobox.clear()
        current_game = self.settings.get('lastactivity', {}).get('game')
        index = None
        for i, x in enumerate(GAME_PRESET_FOLDER.glob('*.json')):
            self.ui.game_combobox.addItem(x.stem)
            if current_game == x.stem:
                index = i
        if index:
            self.ui.game_combobox.setCurrentIndex(index)

    def update_profile_combobox(self):
        """Update information inside the preset combobox"""
        self.ui.profile_combobox.clear()
        current_game = self.settings.get('lastactivity', {}).get('profile')
        index = None
        for i, x in enumerate(self.game_setting['profiles']):
            self.ui.profile_combobox.addItem(x)
            if current_game == x:
                index = i
        if index:
            self.ui.profile_combobox.setCurrentIndex(index)

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
            self.ui, "", "Preset name:", QLineEdit.Normal, self.get_current_profile())
        if not ok:
            return

        config = self.game_setting['profiles'].get(self.get_current_profile())
        self.game_setting['profiles'][preset_name] = config

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
        self.current_profile = self.game_setting['profiles'].get(target_profile)
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
        self.ui.file_view.setModel(self.fs_mod)
        self.ui.file_view.setRootIndex(self.fs_mod.index(path))
        self.ui.file_view.expand(self.fs_mod.index(mod_path))
        
    def set_dirty_status(self, dirty: bool):
        """Update functionality on buttons with regards to modified contents"""
        self.is_dirty = dirty
        self.ui.initialize_mod.setEnabled(self.is_dirty)
        self.ui.save_profile_button.setEnabled(self.is_dirty)

    def create_new_game(self):
        """Start a wizard to create a new game"""
        game_mod_folder_str = QFileDialog.getExistingDirectory(
            self.ui, 'Get mod folder'
        )
        if not game_mod_folder_str:
            return
        game_mod_folder = Path(game_mod_folder_str)
        game_preset_name, ok = QInputDialog.getText(
            self.ui, "", "Game preset name:", QLineEdit.Normal, game_mod_folder.parent.stem)
        if ok:
            QMessageBox.information(self.ui, 'Done', 'Game is set up and ready to go!')

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

        :Param target_preset: Name of game (set when creating a new game)
        :type target_preset: str
        """
        self.target_preset_path = GAME_PRESET_FOLDER / f'{target_preset}.json'
        self.game_setting = json.loads((self.target_preset_path).read_text())
        assert type(self.game_setting) is dict

        self.ui.mod_dest.setText(self.game_setting.get('game_mod_folder'))
        self.update_profile_combobox()
        self.load_current_profile()
        self.update_fileview()
        self.set_dirty_status(False)

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
            self.ui, 'Select archives to be installed', str(Path.home()), "Supported archives (*.zip *.tar)")
        if not archives:
            return
        default_mod_folder = self.game_setting.get('default_mod_folder')
        if not default_mod_folder:
            QMessageBox.warning(self.ui, '', (
                "Sorry, but your settings doesn't have " \
                "a default destination for mods. Is it an old config?"))

        assert type(default_mod_folder) is str
        for archive in archives[0]:
            suff = Path(archive).suffix
            try:
                folder_name = Path(archive).stem
                target_folder = Path(default_mod_folder) / folder_name
                shutil.unpack_archive(archive, target_folder)
            except shutil.ReadError:
                QMessageBox.warning(self.ui, '', f'Sorry, but {suff}-archives is not supported')
            else:
                self.add_mod(target_folder)

    def add_mod(self, folder_path: Path):
        """Import a mod to the current game

        :param folder_path: A path representing the 'root' of the mod folder
        :type folder_path: Path
        """
        print(folder_path)
        folder = QFileDialog.getExistingDirectory(self.ui, 'Choose subfolder', str(folder_path),
                                                  options=QFileDialog.DontUseNativeDialog)
        if not folder:
            return
        folder_name = Path(folder_path).stem
        text, ok = QInputDialog.getText(
            self.ui, "Get mod name", "Name input of mod:", QLineEdit.Normal, folder_name)
        if ok:
            self.add_row_to_mods(name=text, path=folder)

    def add_row_to_mods(self, name: str, path: Path):
        """Add a given mod to the current game

        :param name: unique name of the mod
        :type name: str
        :param path: A path representing the root of the folder, defaults to Path
        :type path: Path, optional
        """
        self.game_setting['mods'][name] = path
        for x in self.game_setting['profiles'].values():
            x.append({
                'name': name,
                'enabled': False
            })
        self.modmodel.layoutChanged.emit()
        self.set_dirty_status(True)

    def add_row_to_mods_fomod_style(self, name: str, path: Path, fomod_results: dict):
        """Add a given mod to the current game with fomod-related presets

        :param name: unique name of the mod
        :type name: str
        :param path: A path representing the root of the folder, defaults to Path
        :type path: Path, optional
        """
        self.game_setting['mods'][name] = str(path)
        for x in self.game_setting['profiles'].values():
            x.append({
                'name': name,
                'enabled': False,
                'type': 'fomod',
                'options': fomod_results
            })
        self.modmodel.layoutChanged.emit()
        self.set_dirty_status(True)

    def get_mod_list_row(self):
        return self.ui.mod_list.selectionModel().selectedRows()[0].row()

    def move_row_up(self):
        row = self.get_mod_list_row()
        if row > 0:
            self._move_row(row, row-1)

    def move_row_down(self):
        row = self.get_mod_list_row()
        try:
            self._move_row(row, row+1)
        except IndexError:
            pass
        
    def _move_row(self, index_a: int, index_b: int):
        """Switch an entry between two rows in the mod list"""
        game_profile = self.game_setting['profiles'].get(self.get_current_profile())
        game_profile[index_a], game_profile[index_b] = game_profile[index_b], game_profile[index_a]
        self.modmodel.layoutChanged.emit()
        self.set_dirty_status(True)

    def init_tablewidget(self, profile=""):
        """Initialize the table with mods

        :param profile: Profile name, defaults to ""
        :type profile: str, optional
        """
        if not profile:
            profile = self.get_current_profile()
        self.modmodel = models.ModModel(
            settings=self.game_setting, profile=profile)
        self.ui.mod_list.setModel(self.modmodel)
        self.ui.mod_list.resizeColumnToContents(MODNAME_COLUMN)

    def clean_target_modfolder(self):
        target_modfolder = Path(self.game_setting['game_mod_folder'])
        if not target_modfolder:
            QMessageBox.warning(self.ui, '', 'No target modfolder found')
        else:
            del_path_target = target_modfolder.resolve()
            x = QMessageBox.question(
                self.ui, 'DELETING FOLDER', f"Are you sure you want to delete \
everything inside this folder?\n{del_path_target}")

            if x == QMessageBox.Yes:
                self.recursive_rmdir(del_path_target)
                QMessageBox.information(self.ui, 'Done', 'Mods are cleaned!')

    def letsgo_mydudes(self):
        """Commit the current setup and fire the modifications"""
        profile = self.game_setting['profiles'].get(self.get_current_profile())
        mod_list = self.game_setting['mods']
        enabled_mods = ',\n'.join([x.get('name') for x in profile if x.get('enabled')])
        target_mod_folder = Path(self.game_setting["game_mod_folder"])
        
        x = QMessageBox.question(self.ui, '', (
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
                QMessageBox.warning(self.ui, '', f'Something went wrong\n{e}')
            else:
                QMessageBox.information(self.ui, 'Done', 'Mods are loaded!')
                self.set_dirty_status(False)


    def begin_fomod_parsing(self, base_folder: Path):
        """Begin parsing of FOMOD-modpacks"""
        if self.fomod is not None:
            return

        self.fomod = FomodParser(base_folder)
        self.fomod.ui.show()
        self.fomod.finished.clicked.connect(self.handle_fomod_results)

    def handle_fomod_results(self):
        """Handle results from parsing a fomod-folder"""
        assert isinstance(self.fomod, FomodParser)
        results = self.fomod.handle_results()

        self.add_row_to_mods_fomod_style(str(self.fomod.module_name), self.fomod.mod_folder, results)
        self.fomod = None
        print(results)


if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)

    ui_file_name = MAIN_UI_PATH
    ui_file = QFile(ui_file_name)
    if not ui_file.open(QIODevice.ReadOnly):
        print(f"Cannot open {ui_file_name}: {ui_file.errorString()}")
        sys.exit(-1)
    loader = QUiLoader()
    window = loader.load(ui_file)
    ui_file.close()
    if not window:
        print(loader.errorString())
        sys.exit(-1)
    modbuddy = Modbuddy(window)
    window.show()

    sys.exit(app.exec())
