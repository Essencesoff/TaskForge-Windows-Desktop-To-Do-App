from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QDateEdit, QCheckBox, QPushButton, QHBoxLayout
from PySide6.QtCore import QDate


class GoalDialog(QDialog):
    def __init__(self, goal: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Goal" if goal else "New Goal")
        self.goal = goal

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.title_edit = QLineEdit(goal["title"] if goal else "")
        form.addRow("Title", self.title_edit)
        self.desc_edit = QTextEdit(goal["description"] if goal else "")
        self.desc_edit.setFixedHeight(60)
        form.addRow("Description", self.desc_edit)

        self.deadline_check = QCheckBox("Set deadline")
        self.deadline_edit = QDateEdit(calendarPopup=True)
        self.deadline_edit.setDate(QDate.currentDate().addMonths(1))
        if goal and goal.get("deadline"):
            self.deadline_check.setChecked(True)
            y, m, d = map(int, goal["deadline"].split("-"))
            self.deadline_edit.setDate(QDate(y, m, d))
        else:
            self.deadline_edit.setEnabled(False)
        self.deadline_check.toggled.connect(self.deadline_edit.setEnabled)
        form.addRow(self.deadline_check, self.deadline_edit)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save Goal")
        save_btn.setObjectName("Primary")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def get_values(self):
        deadline = self.deadline_edit.date().toString("yyyy-MM-dd") if self.deadline_check.isChecked() else None
        return {
            "title": self.title_edit.text().strip() or "Untitled goal",
            "description": self.desc_edit.toPlainText(),
            "deadline": deadline,
        }
