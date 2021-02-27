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

        self.init_fileview()

        # self.init_table_view()
        self.init_tablewidget()

        # END OF INIT
        self.show()

    def init_fileview(self):
        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath(QDir.currentPath())
        self.file_view.setModel(self.model)

    def init_tablewidget(self):
        settings = json.loads(Path(SETTINGS_NAME).read_text())
        for i, row in enumerate(settings):
            self.mod_list.insertRow(i)
            self.mod_list.setItem(i, 0, QTableWidgetItem(row.get('name')))
            self.mod_list.setItem(i, 1, QTableWidgetItem(row.get('folder_name')))
            self.mod_list.setItem(i, 2, QTableWidgetItem(row.get('subfolder')))


    def letsgo_mydudes(self):
        print(self.mod_list.item(1, 0))


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
