import datetime as dt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
                                QTextEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox,
                                QPushButton, QListWidget, QListWidgetItem, QLabel, QCheckBox,
                                QWidget)
from PySide6.QtCore import Qt, QDate, QTime

from app.config.constants import PRIORITIES, STATUSES, RECURRENCE_TYPES, REMINDER_OFFSETS_MIN, DATE_FMT, TIME_FMT
from app.models.task import Task, Subtask
from app.services import category_service, goal_service


class TaskEditorDialog(QDialog):
    def __init__(self, task: Task = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Task" if task else "New Task")
        self.resize(480, 640)
        self.task = task
        self._subtasks = list(task.subtasks) if task else []

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.title_edit = QLineEdit(task.title if task else "")
        self.title_edit.setPlaceholderText("Task title")
        form.addRow("Title", self.title_edit)

        self.desc_edit = QTextEdit(task.description if task else "")
        self.desc_edit.setFixedHeight(70)
        form.addRow("Description", self.desc_edit)

        date_row = QHBoxLayout()
        self.due_date_check = QCheckBox("Set date")
        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate())
        if task and task.due_date:
            self.due_date_check.setChecked(True)
            y, m, d = map(int, task.due_date.split("-"))
            self.date_edit.setDate(QDate(y, m, d))
        else:
            self.date_edit.setEnabled(False)
        self.due_date_check.toggled.connect(self.date_edit.setEnabled)
        date_row.addWidget(self.due_date_check)
        date_row.addWidget(self.date_edit)
        form.addRow("Due Date", date_row)

        time_row = QHBoxLayout()
        self.due_time_check = QCheckBox("Set time")
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(9, 0))
        if task and task.due_time:
            self.due_time_check.setChecked(True)
            h, mnt = map(int, task.due_time.split(":"))
            self.time_edit.setTime(QTime(h, mnt))
        else:
            self.time_edit.setEnabled(False)
        self.due_time_check.toggled.connect(self.time_edit.setEnabled)
        time_row.addWidget(self.due_time_check)
        time_row.addWidget(self.time_edit)
        form.addRow("Due Time", time_row)

        self.priority_combo = QComboBox()
        self.priority_combo.addItems(PRIORITIES)
        self.priority_combo.setCurrentText(task.priority if task else "Medium")
        form.addRow("Priority", self.priority_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(STATUSES)
        self.status_combo.setCurrentText(task.status if task else "To Do")
        form.addRow("Status", self.status_combo)

        self.category_combo = QComboBox()
        self.categories = category_service.list_categories()
        self.category_combo.addItem("None", None)
        for c in self.categories:
            self.category_combo.addItem(f"{c.icon} {c.name}", c.id)
        if task and task.category_id:
            idx = self.category_combo.findData(task.category_id)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
        form.addRow("Category", self.category_combo)

        self.goal_combo = QComboBox()
        self.goal_combo.addItem("None", None)
        for g in goal_service.list_goals():
            self.goal_combo.addItem(g["title"], g["id"])
        if task and task.goal_id:
            idx = self.goal_combo.findData(task.goal_id)
            if idx >= 0:
                self.goal_combo.setCurrentIndex(idx)
        form.addRow("Goal", self.goal_combo)

        self.tags_edit = QLineEdit(", ".join(task.tags) if task else "")
        self.tags_edit.setPlaceholderText("comma, separated, tags")
        form.addRow("Tags", self.tags_edit)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0, 1440)
        self.duration_spin.setSuffix(" min")
        self.duration_spin.setValue(task.estimated_minutes if task else 0)
        form.addRow("Estimated duration", self.duration_spin)

        self.reminder_combo = QComboBox()
        self.reminder_combo.addItem("None", None)
        for label, minutes in REMINDER_OFFSETS_MIN.items():
            self.reminder_combo.addItem(label, minutes)
        if task and task.reminder_offset_min:
            idx = self.reminder_combo.findData(task.reminder_offset_min)
            if idx >= 0:
                self.reminder_combo.setCurrentIndex(idx)
        form.addRow("Reminder", self.reminder_combo)

        self.recurrence_combo = QComboBox()
        self.recurrence_combo.addItems(RECURRENCE_TYPES)
        self.recurrence_combo.setCurrentText(task.recurrence if task else "None")
        form.addRow("Recurrence", self.recurrence_combo)

        self.recurrence_data_edit = QLineEdit(task.recurrence_data if task else "")
        self.recurrence_data_edit.setPlaceholderText("e.g. Mon,Wed,Fri (only for Custom)")
        form.addRow("Recurrence days", self.recurrence_data_edit)

        self.notes_edit = QTextEdit(task.notes if task else "")
        self.notes_edit.setFixedHeight(60)
        form.addRow("Notes", self.notes_edit)

        layout.addLayout(form)

        # Subtasks
        layout.addWidget(QLabel("Subtasks"))
        self.subtask_list = QListWidget()
        self._refresh_subtask_list()
        layout.addWidget(self.subtask_list)

        sub_row = QHBoxLayout()
        self.new_subtask_edit = QLineEdit()
        self.new_subtask_edit.setPlaceholderText("Add a subtask and press Enter")
        self.new_subtask_edit.returnPressed.connect(self._add_subtask)
        sub_row.addWidget(self.new_subtask_edit)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_subtask)
        sub_row.addWidget(add_btn)
        layout.addLayout(sub_row)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save Task")
        save_btn.setObjectName("Primary")
        # Intentionally not setDefault(True): the subtask field's own Enter-to-add
        # would otherwise also submit/close this multi-field dialog.
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        self.title_edit.setFocus()

    def _refresh_subtask_list(self):
        self.subtask_list.clear()
        for st in self._subtasks:
            item = QListWidgetItem(("\u2611 " if st.is_done else "\u2610 ") + st.title)
            item.setData(Qt.UserRole, st)
            self.subtask_list.addItem(item)
        self.subtask_list.itemDoubleClicked.connect(self._toggle_subtask_item)

    def _toggle_subtask_item(self, item):
        st = item.data(Qt.UserRole)
        st.is_done = not st.is_done
        self._refresh_subtask_list()

    def _add_subtask(self):
        text = self.new_subtask_edit.text().strip()
        if not text:
            return
        self._subtasks.append(Subtask(id=None, task_id=None, title=text, is_done=False,
                                       sort_order=len(self._subtasks)))
        self.new_subtask_edit.clear()
        self._refresh_subtask_list()

    def get_task(self) -> Task:
        due_date = self.date_edit.date().toString("yyyy-MM-dd") if self.due_date_check.isChecked() else None
        due_time = self.time_edit.time().toString("HH:mm") if self.due_time_check.isChecked() else None
        tags = [t.strip() for t in self.tags_edit.text().split(",") if t.strip()]

        base = self.task or Task(id=None, title="")
        base.title = self.title_edit.text().strip() or "Untitled task"
        base.description = self.desc_edit.toPlainText()
        base.due_date = due_date
        base.due_time = due_time
        base.priority = self.priority_combo.currentText()
        base.status = self.status_combo.currentText()
        base.category_id = self.category_combo.currentData()
        base.goal_id = self.goal_combo.currentData()
        base.tags = tags
        base.estimated_minutes = self.duration_spin.value()
        base.reminder_offset_min = self.reminder_combo.currentData()
        base.reminder_fired = False if (self.task is None or base.reminder_offset_min != self.task.reminder_offset_min) else base.reminder_fired
        base.recurrence = self.recurrence_combo.currentText()
        base.recurrence_data = self.recurrence_data_edit.text().strip()
        base.notes = self.notes_edit.toPlainText()
        base.subtasks = self._subtasks
        return base
