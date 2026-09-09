from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                                QScrollArea, QPushButton, QMessageBox)
from app.services import category_service
from app.dialogs.category_dialog import CategoryDialog


class CategoriesPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        title = QLabel("Categories")
        title.setObjectName("Heading")
        header.addWidget(title)
        header.addStretch()
        new_btn = QPushButton("+ New Category")
        new_btn.setObjectName("Primary")
        new_btn.clicked.connect(self._new_category)
        header.addWidget(new_btn)
        layout.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.c_layout = QVBoxLayout(self.container)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)
        self.refresh()

    def _new_category(self):
        dlg = CategoryDialog(parent=self)
        if dlg.exec():
            cat = dlg.get_category()
            category_service.create_category(cat.name, cat.icon, cat.color, cat.description)
            self.refresh()
            self.main_window.refresh_category_dependents()

    def _edit_category(self, cat):
        dlg = CategoryDialog(cat, parent=self)
        if dlg.exec():
            category_service.update_category(dlg.get_category())
            self.refresh()
            self.main_window.refresh_category_dependents()

    def _delete_category(self, cat_id):
        confirm = QMessageBox.question(self, "Delete Category",
                                        "Delete this category? Tasks will become uncategorized.")
        if confirm == QMessageBox.Yes:
            category_service.delete_category(cat_id)
            self.refresh()
            self.main_window.refresh_category_dependents()

    def refresh(self):
        while self.c_layout.count():
            item = self.c_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        for cat in category_service.list_categories():
            card = QFrame()
            card.setObjectName("Card")
            row = QHBoxLayout(card)
            lbl = QLabel(f"{cat.icon}  {cat.name}")
            lbl.setStyleSheet(f"font-weight: 600; color: {cat.color};")
            row.addWidget(lbl)
            desc = QLabel(cat.description)
            desc.setObjectName("SubHeading")
            row.addWidget(desc, 1)
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda _, c=cat: self._edit_category(c))
            row.addWidget(edit_btn)
            del_btn = QPushButton("Delete")
            del_btn.clicked.connect(lambda _, cid=cat.id: self._delete_category(cid))
            row.addWidget(del_btn)
            self.c_layout.addWidget(card)
        self.c_layout.addStretch()
