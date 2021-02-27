from pathlib import Path
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtCore import QDir, QAbstractTableModel, QStringListModel
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QTableWidgetItem, QMainWindow
from PyQt5.uic import loadUi
import modpack
import json
import sys

INPUT_FOLDER = 'input'
SETTINGS_NAME = 'settings.json'
ROOT_FOLDER_NAME = 'root_folder'
OUTPUT_FOLDER = Path('output') / ROOT_FOLDER_NAME


class Ui(QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        loadUi('ui/modbuddy.ui', self)

        # Connect buttons
        self.initialize_mod.clicked.connect(self.letsgo_mydudes)
        self.move_up.clicked.connect(self.move_row_up)
        self.move_down.clicked.connect(self.move_row_down)

        self.init_fileview()

        # self.init_table_view()
        self.init_tablewidget()

        # END OF INIT
        self.show()

    @staticmethod
    def export_modlist_to_list(table) -> dict:
        output = []
        for i in range(table.rowCount()):
            output.append({
                'name': table.item(i, 0).text(),
                'folder_name': table.item(i, 1).text(),
                'subfolder': table.item(i, 2).text()
            })
        print(output)

    def init_fileview(self):
        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath(QDir.currentPath())
        self.file_view.setModel(self.model)

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


            

    def letsgo_mydudes(self):
        print(self.mod_list.item(1, 0))
        self.export_modlist_to_list(self.mod_list)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()
    # in_p = Path(INPUT_FOLDER)
    # settings = json.loads(Path(SETTINGS_NAME).read_text())
    # print(settings)
    # for single_mod in settings:
    #     print("~~~~ Adding {}".format(single_mod.get('name')))
    #     target_folder = in_p / single_mod.get('folder_name') / single_mod.get('subfolder')
    #     modpack.ModPack(target_folder, OUTPUT_FOLDER)
