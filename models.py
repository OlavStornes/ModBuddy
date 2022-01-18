from PyQt5 import QtCore
from PyQt5.QtCore import Qt


class ModModel(QtCore.QAbstractTableModel):
    """An implementation for handling mod data in a QT.QTableView"""
    def __init__(self, *args, settings=None, profile=None, **kwargs):
        super(ModModel, self).__init__(*args, **kwargs)
        self.profile = profile
        self.game_setting = settings
        self.mod_order = []
        self.headers = ('enabled', 'name', 'path')

        self.parse_mods_from_settings()

    def parse_mods_from_settings(self):
        """Read game_setting and update mod_order with the current profile"""
        if not self.game_setting:
            return
        try:
            self.mod_order = self.game_setting.get('profiles').get(self.profile)
        except AttributeError:
            pass

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        """Overridden function to support own headers"""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return super().headerData(section, orientation, role)


    def parse_path(self, row: str):
        """Attempt to strip away the unneccecary parts of a path for display"""
        relative_path = self.game_setting.get('mods').get(row.get('name'))
        try:
            path_parsed = relative_path.replace(self.game_setting.get('default_mod_folder'), '.')
        except:
            return relative_path
        return path_parsed


    def data(self, index, role):
        """Model-specific function to assist in displaying of data"""
        cur_profile = self.game_setting.get('profiles').get(self.profile)

        row = cur_profile[index.row()]
        if role == QtCore.Qt.CheckStateRole and self.headers[index.column()] == 'enabled':
            if row.get('enabled'):
                return QtCore.QVariant(QtCore.Qt.Checked)
            else:
                return QtCore.QVariant(QtCore.Qt.Unchecked)
        if role == QtCore.Qt.DisplayRole:
            if self.headers[index.column()] == 'name':
                return row.get('name')
            if self.headers[index.column()] == 'path':
                return self.parse_path(row)

    def setData(self, index, value, role: int) -> bool:
        """Overridden funciton to help with checkboxes"""
        cur_profile = self.game_setting.get('profiles').get(self.profile)
        if role == Qt.CheckStateRole and self.headers[index.column()] == 'enabled':
            if value == Qt.Checked:
                cur_profile[index.row()]['enabled'] = True
            else:
                cur_profile[index.row()]['enabled'] = False
        self.layoutChanged.emit()
        return super().setData(index, value, role=role)

    def flags(self, index):
        """Overridden function to support checkboxes"""
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable
        else:
            return super().flags(index)

    def rowCount(self, index=None) -> int:
        return len(self.mod_order)

    def columnCount(self, index=None) -> int:
        try:
            return len(self.headers)
        except IndexError:
            return 0
