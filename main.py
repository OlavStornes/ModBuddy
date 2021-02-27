from pathlib import Path
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QMainWindow
from PyQt5.uic import loadUi
import modpack
import json
import sys

INPUT_FOLDER = 'input'
SETTINGS_NAME = 'settings.json'
ROOT_FOLDER_NAME = 'gamedata'
OUTPUT_FOLDER = Path('output') / ROOT_FOLDER_NAME


class Ui(QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        loadUi('ui/modbuddy.ui', self)

        # Connect buttons
        self.initialize_mod.clicked.connect(self.letsgo_mydudes)
        self.move_up.clicked.connect(self.move_row_up)
        self.move_down.clicked.connect(self.move_row_down)
        self.save_settings.clicked.connect(self.save_table_config)
        self.new_mod_button.clicked.connect(self.install_new_mod)
        self.mod_dest_button.clicked.connect(self.choose_mod_dest)

        self.init_fileview()

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

    def init_fileview(self):
        self.filesystem_model = QtWidgets.QFileSystemModel()
        self.filesystem_model.setRootPath('home')
        self.file_view.setModel(self.filesystem_model)

    def install_new_mod(self):
        tmp = QFileDialog.getExistingDirectory(self, 'Install mod')
        print(tmp)

    def choose_mod_dest(self):
        tmp = QFileDialog.getExistingDirectory(self, 'Choose mod destination')
        self.mod_dest.setText(tmp)

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
        for i, row in enumerate(settings):
            self.mod_list.insertRow(i)
            self.mod_list.setItem(i, 0, QTableWidgetItem(row.get('name')))
            self.mod_list.setItem(i, 1, QTableWidgetItem(row.get('folder_name')))
            self.mod_list.setItem(i, 2, QTableWidgetItem(row.get('subfolder')))
            is_enabled = row.get('enabled')
            chkBoxItem = QTableWidgetItem()
            chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            if is_enabled:
                chkBoxItem.setCheckState(QtCore.Qt.Checked)
            else:
                chkBoxItem.setCheckState(QtCore.Qt.Unchecked)

            self.mod_list.setItem(i, 3, QTableWidgetItem(chkBoxItem))

    def letsgo_mydudes(self):
        conf = self.export_modlist_to_list(self.mod_list)
        in_p = Path(INPUT_FOLDER)
        for single_mod in conf:
            if single_mod.get('enabled'):
                print("~~~~ Adding {}".format(single_mod.get('name')))
                target_folder = in_p / single_mod.get('folder_name') / single_mod.get('subfolder')
                modpack.ModPack(target_folder, OUTPUT_FOLDER)
        self.statusbar.showMessage("Modbuddy done!")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()
