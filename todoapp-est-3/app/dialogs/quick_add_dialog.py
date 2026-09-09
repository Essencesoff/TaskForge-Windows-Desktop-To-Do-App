from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QDateEdit, QPushButton, QLabel
from PySide6.QtCore import QDate, Qt

from app.config.constants import PRIORITIES
from app.models.task import Task
from app.services import category_service


class QuickAddDialog(QDialog):
    """Title -> Date -> Priority -> Category -> Create, Enter creates immediately."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Add Task")
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("What do you need to do?"))

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Task title\u2026")
        layout.addWidget(self.title_edit)

        row = QHBoxLayout()
        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setSpecialValueText("No date")
        row.addWidget(self.date_edit)

        self.priority_combo = QComboBox()
        self.priority_combo.addItems(PRIORITIES)
        self.priority_combo.setCurrentText("Medium")
        row.addWidget(self.priority_combo)
        layout.addLayout(row)

        self.category_combo = QComboBox()
        self.category_combo.addItem("None", None)
        for c in category_service.list_categories():
            self.category_combo.addItem(f"{c.icon} {c.name}", c.id)
        layout.addWidget(self.category_combo)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        create_btn = QPushButton("Create (Enter)")
        create_btn.setObjectName("Primary")
        create_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(create_btn)
        layout.addLayout(btn_row)

        self.title_edit.setFocus()
        self.title_edit.returnPressed.connect(self.accept)

    def get_task(self) -> Task:
        return Task(
            id=None,
            title=self.title_edit.text().strip() or "Untitled task",
            due_date=self.date_edit.date().toString("yyyy-MM-dd"),
            priority=self.priority_combo.currentText(),
            category_id=self.category_combo.currentData(),
        )
