from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                                QScrollArea, QPushButton, QMessageBox)
from app.services import task_service, category_service


class TrashPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        title = QLabel("Trash")
        title.setObjectName("Heading")
        header.addWidget(title)
        header.addStretch()
        empty_btn = QPushButton("Empty Trash")
        empty_btn.clicked.connect(self._empty_trash)
        header.addWidget(empty_btn)
        layout.addLayout(header)

        note = QLabel("Deleted tasks stay here until you empty the trash or restore them.")
        note.setObjectName("SubHeading")
        layout.addWidget(note)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.c_layout = QVBoxLayout(self.container)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)
        self.refresh()

    def _empty_trash(self):
        confirm = QMessageBox.question(
            self, "Empty Trash", "Permanently delete all trashed tasks? This can't be undone.")
        if confirm == QMessageBox.Yes:
            task_service.empty_trash()
            self.refresh()

    def refresh(self):
        while self.c_layout.count():
            item = self.c_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        tasks = task_service.list_tasks(include_deleted=True)
        tasks = [t for t in tasks if t.is_deleted]
        if not tasks:
            empty = QLabel("Trash is empty.")
            empty.setObjectName("SubHeading")
            self.c_layout.addWidget(empty)

        for t in tasks:
            card = QFrame()
            card.setObjectName("Card")
            row = QHBoxLayout(card)
            lbl = QLabel(t.title)
            row.addWidget(lbl, 1)
            restore_btn = QPushButton("Restore")
            restore_btn.clicked.connect(lambda _, tid=t.id: self._restore(tid))
            row.addWidget(restore_btn)
            del_btn = QPushButton("Delete Forever")
            del_btn.clicked.connect(lambda _, tid=t.id: self._delete_forever(tid))
            row.addWidget(del_btn)
            self.c_layout.addWidget(card)
        self.c_layout.addStretch()

    def _restore(self, task_id):
        task_service.restore_task(task_id)
        self.refresh()

    def _delete_forever(self, task_id):
        confirm = QMessageBox.question(
            self, "Delete Forever", "Permanently delete this task? This can't be undone.")
        if confirm == QMessageBox.Yes:
            task_service.permanently_delete_task(task_id)
            self.refresh()
