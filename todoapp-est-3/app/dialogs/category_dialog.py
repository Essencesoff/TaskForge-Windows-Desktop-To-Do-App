from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QColorDialog
from app.models.task import Category


class CategoryDialog(QDialog):
    def __init__(self, category: Category = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Category" if category else "New Category")
        self.category = category
        self._color = category.color if category else "#5C6BC0"

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit(category.name if category else "")
        form.addRow("Name", self.name_edit)
        self.icon_edit = QLineEdit(category.icon if category else "\U0001F4CC")
        form.addRow("Icon (emoji)", self.icon_edit)

        color_row = QHBoxLayout()
        self.color_btn = QPushButton()
        self._update_color_btn()
        self.color_btn.clicked.connect(self._pick_color)
        color_row.addWidget(self.color_btn)
        form.addRow("Color", color_row)

        self.desc_edit = QLineEdit(category.description if category else "")
        form.addRow("Description", self.desc_edit)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save")
        save_btn.setObjectName("Primary")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _update_color_btn(self):
        self.color_btn.setStyleSheet(f"background-color: {self._color}; min-width: 60px; min-height: 24px;")

    def _pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self._color = color.name()
            self._update_color_btn()

    def get_category(self) -> Category:
        base = self.category or Category(id=None, name="")
        base.name = self.name_edit.text().strip() or "Untitled"
        base.icon = self.icon_edit.text().strip()
        base.color = self._color
        base.description = self.desc_edit.text().strip()
        return base
