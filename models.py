from PyQt5 import QtCore
from PyQt5.QtCore import Qt


class ModModel(QtCore.QAbstractTableModel):
    def __init__(self, *args, mods=None, **kwargs):
        super(ModModel, self).__init__(*args, **kwargs)
        self.mods = mods or []
        self.headers = ('enabled', 'name', 'path')

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return super().headerData(section, orientation, role)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            text = self.mods[index.row()].get(self.headers[index.column()])
            return text

    def rowCount(self, index=None) -> int:
        return len(self.mods)

    def columnCount(self, index=None) -> int:
        try:
            return len(self.mods[0])
        except IndexError:
            return 0

    def move_target_row_up(self, row: int):
        if row == 0:
            return
        should_be_at = row - 1
        self._switch_rows(row, should_be_at)

    def move_target_row_down(self, row: int):
        if row == self.rowCount():
            return
        should_be_at = row + 1
        self._switch_rows(row, should_be_at)

    def _switch_rows(self, old_index: dict, new_index: int):
        extracted_row = self.mods.pop(old_index)
        self.mods.insert(new_index, extracted_row)
        self.layoutChanged.emit()
