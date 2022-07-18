from typing import Any, Dict, List
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from typing import Union


class ModModel(QtCore.QAbstractTableModel):
    """An implementation for handling mod data in a QT.QTableView."""

    def __init__(self, *args: tuple[str], settings:Dict[str, Dict|str], profile: Any, **kwargs):
        super(ModModel, self).__init__(*args, **kwargs)
        self.profile = profile
        self.game_setting = settings
        self.mod_order = []
        self.headers = ('enabled', 'name', 'type', 'path')

        self.parse_mods_from_settings()

    def parse_mods_from_settings(self):
        """Read game_setting and update mod_order with the current profile."""
        if not self.game_setting:
            return 
        try:
            profile = self.game_setting['profiles']
            assert type(profile) is dict

            self.mod_order = profile.get(self.profile)
        except AttributeError:
            pass

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        """Overridden function to support own headers."""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return super().headerData(section, orientation, role)


    def parse_path(self, row: Dict):
        """Attempt to strip away the unneccecary parts of a path for display."""
        mod_settings = self.game_setting['mods']
        assert type(mod_settings) is dict

        relative_path = mod_settings.get(row.get('name'))
        try:
            assert isinstance(relative_path, str)
            path_parsed = relative_path.replace(self.game_setting.get('default_mod_folder'), '.')
        except:
            return relative_path
        return path_parsed



    def data(self,
            index: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex],
            role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Model-specific function to assist in displaying of data."""
        cur_profile = self.game_setting['profiles'][self.profile]

        row = cur_profile[index.row()]
        assert type(row) is dict

        if role == QtCore.Qt.CheckStateRole and self.headers[index.column()] == 'enabled':
            if row.get('enabled'):
                return Qt.Checked
            else:
                return Qt.Unchecked
        if role == QtCore.Qt.DisplayRole:
            if self.headers[index.column()] == 'enabled':
                return row.get('enabled')
            if self.headers[index.column()] == 'name':
                return row.get('name')
            if self.headers[index.column()] == 'type':
                return row.get('type', 'basic')
            if self.headers[index.column()] == 'path':
                return self.parse_path(row)

    def setData(self, index: QtCore.QModelIndex, value, role: int) -> bool:
        """Overridden funciton to help with checkboxes."""
        cur_profile = self.game_setting['profiles'][self.profile]
        assert type(cur_profile) is list
        if role == Qt.CheckStateRole and self.headers[index.column()] == 'enabled':
            if value == Qt.Checked:
                cur_profile[index.row()]['enabled'] = True
            else:
                cur_profile[index.row()]['enabled'] = False
        self.layoutChanged.emit()
        return super().setData(index, value, role=role)

    def flags(self, index: QtCore.QModelIndex):
        """Overridden function to support checkboxes"""
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable
        else:
            return super().flags(index)

    def rowCount(self, index=None) -> int:
        assert type(self.mod_order) is list
        return len(self.mod_order)

    def columnCount(self, index=None) -> int:
        try:
            return len(self.headers)
        except IndexError:
            return 0


class SourceModel(QtCore.QAbstractTableModel):
    """An implementation for handling mod data in a QT.QTableView."""

    def __init__(self, *args: tuple[str], sources:Dict[str, str], **kwargs):
        super(SourceModel, self).__init__(*args, **kwargs)
        self.sources = sources
        self.headers = ('title', 'installed', 'added', 'updated', 'size', 'url')

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        """Overridden function to support own headers."""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return super().headerData(section, orientation, role)

    def data(self,
            index: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex],
            role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Model-specific function to assist in displaying of data."""
        row = self.sources[index.row()]
        assert type(row) is dict

        if role == QtCore.Qt.DisplayRole:
            return row.get(self.headers[index.column()])

    # def setData(self, index: QtCore.QModelIndex, value, role: int) -> bool:
    #     """Overridden funciton to help with checkboxes."""
    #     cur_profile = self.game_setting['profiles'][self.profile]
    #     assert type(cur_profile) is list
    #     if role == Qt.CheckStateRole and self.headers[index.column()] == 'enabled':
    #         if value == Qt.Checked:
    #             cur_profile[index.row()]['enabled'] = True
    #         else:
    #             cur_profile[index.row()]['enabled'] = False
    #     self.layoutChanged.emit()
    #     return super().setData(index, value, role=role)

    # def flags(self, index: QtCore.QModelIndex):
    #     """Overridden function to support checkboxes"""
    #     if index.column() == 0:
    #         return Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable
    #     else:
    #         return super().flags(index)

    def rowCount(self, index=None) -> int:
        assert type(self.sources) is list
        return len(self.sources)

    def columnCount(self, index=None) -> int:
        try:
            return len(self.headers)
        except IndexError:
            return 0
