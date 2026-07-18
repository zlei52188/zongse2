from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSettings, Qt

from browndust2_manager.services.root_service import DEFAULT_ROOT_DIR, EmulatorConfig


class EmulatorConfigModel(QAbstractTableModel):
    """Editable table model storing four rooted Android emulator targets."""

    HEADERS = ["模拟器", "名称", "adb serial", "Root目录"]

    def __init__(self, settings: QSettings | None = None) -> None:
        super().__init__()
        self._settings = settings or QSettings("BrownDust2Manager", "BrownDust2Manager")
        self.configs = [self._load_config(i) for i in range(1, 5)]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.configs)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if not index.isValid() or role not in {Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole}:
            return None
        config = self.configs[index.row()]
        return [f"模拟器{config.slot}", config.name, config.serial, config.root_dir][index.column()]

    def setData(self, index: QModelIndex, value: object, role: int = Qt.ItemDataRole.EditRole) -> bool:  # noqa: N802
        if not index.isValid() or role != Qt.ItemDataRole.EditRole or index.column() == 0:
            return False
        config = self.configs[index.row()]
        text = str(value)
        if index.column() == 1:
            config.name = text
        elif index.column() == 2:
            config.serial = text
        elif index.column() == 3:
            config.root_dir = text or DEFAULT_ROOT_DIR
        else:
            return False
        self._save_config(config)
        self.dataChanged.emit(index, index, [role])
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        flags = super().flags(index)
        if index.isValid() and index.column() != 0:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> object:  # noqa: N802
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return super().headerData(section, orientation, role)

    def config_for_slot(self, slot: int) -> EmulatorConfig:
        if slot not in {1, 2, 3, 4}:
            raise ValueError("模拟器编号必须是 1~4")
        return self.configs[slot - 1]

    def _load_config(self, slot: int) -> EmulatorConfig:
        prefix = f"emulators/{slot}"
        return EmulatorConfig(
            slot=slot,
            name=str(self._settings.value(f"{prefix}/name", f"模拟器{slot}")),
            serial=str(self._settings.value(f"{prefix}/serial", "")),
            root_dir=str(self._settings.value(f"{prefix}/root_dir", DEFAULT_ROOT_DIR)),
        )

    def _save_config(self, config: EmulatorConfig) -> None:
        prefix = f"emulators/{config.slot}"
        self._settings.setValue(f"{prefix}/name", config.name)
        self._settings.setValue(f"{prefix}/serial", config.serial)
        self._settings.setValue(f"{prefix}/root_dir", config.root_dir)
