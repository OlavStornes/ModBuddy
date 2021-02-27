from pathlib import Path
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QFileDialog, QInputDialog, QLineEdit, QMessageBox, QTableWidgetItem, QMainWindow
from PyQt5.uic import loadUi
import modpack
import json
import sys

INPUT_FOLDER = Path('input')
SETTINGS_NAME = 'settings.json'
ROOT_FOLDER_NAME = 'gamedata'
OUTPUT_FOLDER = Path('output') / ROOT_FOLDER_NAME


class Ui(QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        loadUi('ui/modbuddy.ui', self)

        # Initialize some components
        self.filesystem_model = QtWidgets.QFileSystemModel()

        # Connect buttons
        self.initialize_mod.clicked.connect(self.letsgo_mydudes)
        self.move_up.clicked.connect(self.move_row_up)
        self.move_down.clicked.connect(self.move_row_down)
        self.save_settings.clicked.connect(self.save_table_config)
        self.new_mod_button.clicked.connect(self.install_new_mod)
        self.mod_dest_button.clicked.connect(self.choose_mod_dest)

        self.update_fileview(str(OUTPUT_FOLDER))

        self.init_tablewidget()

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

    def save_table_config(self):
        config = self.export_modlist_to_list(self.mod_list)
        Path(SETTINGS_NAME).write_text(json.dumps(config, indent=4))
        self.statusbar.showMessage(f"Settings saved to {SETTINGS_NAME}")

    def update_fileview(self, path):
        # self.filesystem_model.setRootPath(QtCore.QDir.currentPath())
        index = self.filesystem_model.index(path)
        self.filesystem_model.setRootPath(path)
        self.file_view.setModel(self.filesystem_model)
        self.file_view.expand(index)

    def install_new_mod(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Install mod')
        folder_name = Path(folder_path).stem
        text, ok = QInputDialog.getText(
            self, "Get mod name", "Name input of mod:", QLineEdit.Normal, folder_name)
        if ok:
            self.add_row_to_mods({
                'name': text,
                'folder_name': folder_name,
                'subfolder': folder_name,
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

    def choose_mod_dest(self):
        tmp = QFileDialog.getExistingDirectory(self, 'Choose mod destination')
        self.mod_dest.setText(tmp)
        self.update_fileview(tmp)

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
        settings = json.loads(Path(SETTINGS_NAME).read_text())
        for row in settings:
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
