from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox,
                                QCheckBox, QSpinBox, QPushButton, QFileDialog, QMessageBox)
from app.services import settings_service, backup_service, category_service
from app.config.constants import PRIORITIES


def _section(title):
    frame = QFrame()
    frame.setObjectName("Card")
    layout = QVBoxLayout(frame)
    lbl = QLabel(title)
    lbl.setStyleSheet("font-weight: 700; font-size: 15px;")
    layout.addWidget(lbl)
    return frame, layout


class SettingsPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        outer = QVBoxLayout(self)
        title = QLabel("Settings")
        title.setObjectName("Heading")
        outer.addWidget(title)

        # Appearance
        frame, layout = _section("Appearance")
        row = QHBoxLayout()
        row.addWidget(QLabel("Theme"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light", "system"])
        self.theme_combo.setCurrentText(settings_service.get("theme", "dark"))
        self.theme_combo.currentTextChanged.connect(self._on_theme_change)
        row.addWidget(self.theme_combo)
        row.addWidget(QLabel("Density"))
        self.density_combo = QComboBox()
        self.density_combo.addItems(["comfortable", "compact"])
        self.density_combo.setCurrentText(settings_service.get("ui_density", "comfortable"))
        self.density_combo.currentTextChanged.connect(lambda v: settings_service.set("ui_density", v))
        row.addWidget(self.density_combo)
        layout.addLayout(row)
        outer.addWidget(frame)

        # Notifications
        frame, layout = _section("Notifications")
        self.notif_check = QCheckBox("Enable notifications")
        self.notif_check.setChecked(settings_service.get_bool("notifications_enabled"))
        self.notif_check.toggled.connect(lambda v: settings_service.set("notifications_enabled", int(v)))
        layout.addWidget(self.notif_check)
        row = QHBoxLayout()
        row.addWidget(QLabel("Default reminder (minutes before)"))
        self.reminder_spin = QSpinBox()
        self.reminder_spin.setRange(1, 1440)
        self.reminder_spin.setValue(int(settings_service.get("default_reminder_min", 30)))
        self.reminder_spin.valueChanged.connect(lambda v: settings_service.set("default_reminder_min", v))
        row.addWidget(self.reminder_spin)
        layout.addLayout(row)
        outer.addWidget(frame)

        # Tasks
        frame, layout = _section("Tasks")
        row = QHBoxLayout()
        row.addWidget(QLabel("Default priority"))
        self.default_priority_combo = QComboBox()
        self.default_priority_combo.addItems(PRIORITIES)
        self.default_priority_combo.setCurrentText(settings_service.get("default_priority", "Medium"))
        self.default_priority_combo.currentTextChanged.connect(
            lambda v: settings_service.set("default_priority", v))
        row.addWidget(self.default_priority_combo)

        row.addWidget(QLabel("Default category"))
        self.default_category_combo = QComboBox()
        self.default_category_combo.addItem("None", "")
        for c in category_service.list_categories():
            self.default_category_combo.addItem(f"{c.icon} {c.name}", str(c.id))
        current = settings_service.get("default_category_id", "")
        idx = self.default_category_combo.findData(current)
        if idx >= 0:
            self.default_category_combo.setCurrentIndex(idx)
        self.default_category_combo.currentIndexChanged.connect(
            lambda: settings_service.set("default_category_id", self.default_category_combo.currentData()))
        row.addWidget(self.default_category_combo)
        layout.addLayout(row)
        outer.addWidget(frame)

        # Windows integration
        frame, layout = _section("Windows Integration")
        self.start_min_check = QCheckBox("Start minimized to tray")
        self.start_min_check.setChecked(settings_service.get_bool("start_minimized"))
        self.start_min_check.toggled.connect(lambda v: settings_service.set("start_minimized", int(v)))
        layout.addWidget(self.start_min_check)
        self.launch_startup_check = QCheckBox("Launch on Windows startup")
        self.launch_startup_check.setChecked(settings_service.get_bool("launch_on_startup"))
        self.launch_startup_check.toggled.connect(self._on_launch_startup_toggle)
        layout.addWidget(self.launch_startup_check)
        outer.addWidget(frame)

        # Data
        frame, layout = _section("Data")
        row1 = QHBoxLayout()
        export_json_btn = QPushButton("Export JSON")
        export_json_btn.clicked.connect(self._export_json)
        row1.addWidget(export_json_btn)
        export_csv_btn = QPushButton("Export CSV")
        export_csv_btn.clicked.connect(self._export_csv)
        row1.addWidget(export_csv_btn)
        import_btn = QPushButton("Import JSON")
        import_btn.clicked.connect(self._import_json)
        row1.addWidget(import_btn)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        backup_btn = QPushButton("Create Backup")
        backup_btn.clicked.connect(self._create_backup)
        row2.addWidget(backup_btn)
        restore_btn = QPushButton("Restore Latest Backup")
        restore_btn.clicked.connect(self._restore_backup)
        row2.addWidget(restore_btn)
        layout.addLayout(row2)

        clear_btn = QPushButton("Clear All Data")
        clear_btn.setStyleSheet("color: #F44336;")
        clear_btn.clicked.connect(self._clear_all_data)
        layout.addWidget(clear_btn)
        outer.addWidget(frame)

        outer.addStretch()

    def _on_theme_change(self, value):
        settings_service.set("theme", value)
        self.main_window.apply_theme()

    def _on_launch_startup_toggle(self, checked):
        settings_service.set("launch_on_startup", int(checked))
        self.main_window.set_launch_on_startup(checked)

    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export JSON", "taskforge_export.json", "JSON Files (*.json)")
        if path:
            backup_service.export_json(path)
            QMessageBox.information(self, "Export complete", f"Exported to {path}")

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "taskforge_export.csv", "CSV Files (*.csv)")
        if path:
            backup_service.export_csv(path)
            QMessageBox.information(self, "Export complete", f"Exported to {path}")

    def _import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import JSON", "", "JSON Files (*.json)")
        if path:
            try:
                backup_service.import_json(path)
                QMessageBox.information(self, "Import complete", "Data imported successfully.")
                self.main_window.refresh_all()
            except Exception as e:
                QMessageBox.critical(self, "Import failed", str(e))

    def _create_backup(self):
        path = backup_service.create_backup()
        QMessageBox.information(self, "Backup created", f"Saved to {path}")

    def _restore_backup(self):
        backups = backup_service.list_backups()
        if not backups:
            QMessageBox.warning(self, "No backups", "No backups found yet.")
            return
        confirm = QMessageBox.question(
            self, "Restore Backup",
            f"Restore from most recent backup?\n{backups[0]}\nCurrent data will be replaced.")
        if confirm == QMessageBox.Yes:
            backup_service.restore_backup(backups[0])
            QMessageBox.information(self, "Restored", "Backup restored. Data reloaded.")
            self.main_window.refresh_all()

    def _clear_all_data(self):
        confirm = QMessageBox.question(
            self, "Clear All Data",
            "This will permanently delete ALL tasks, goals and habits. Continue?")
        if confirm == QMessageBox.Yes:
            backup_service.clear_all_data()
            self.main_window.refresh_all()
