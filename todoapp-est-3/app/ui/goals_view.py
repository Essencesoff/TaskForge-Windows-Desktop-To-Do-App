from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                                QProgressBar, QScrollArea, QPushButton, QMenu)
from app.services import goal_service
from app.dialogs.goal_dialog import GoalDialog
from app.utils.helpers import format_friendly_date


class GoalsPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        title = QLabel("Goals")
        title.setObjectName("Heading")
        header.addWidget(title)
        header.addStretch()
        new_btn = QPushButton("+ New Goal")
        new_btn.setObjectName("Primary")
        new_btn.clicked.connect(self._new_goal)
        header.addWidget(new_btn)
        layout.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.c_layout = QVBoxLayout(self.container)
        self.c_layout.setSpacing(10)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)
        self.refresh()

    def _new_goal(self):
        dlg = GoalDialog(parent=self)
        if dlg.exec():
            vals = dlg.get_values()
            goal_service.create_goal(vals["title"], vals["description"], vals["deadline"])
            self.refresh()

    def _edit_goal(self, goal):
        dlg = GoalDialog(goal, parent=self)
        if dlg.exec():
            vals = dlg.get_values()
            from app.models.task import Goal
            g = Goal(id=goal["id"], title=vals["title"], description=vals["description"],
                      deadline=vals["deadline"])
            goal_service.update_goal(g)
            self.refresh()

    def _delete_goal(self, goal_id):
        goal_service.delete_goal(goal_id)
        self.refresh()

    def refresh(self):
        while self.c_layout.count():
            item = self.c_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        goals = goal_service.list_goals()
        if not goals:
            empty = QLabel("No goals yet. Break a big ambition into tasks!")
            empty.setObjectName("SubHeading")
            self.c_layout.addWidget(empty)

        for g in goals:
            card = QFrame()
            card.setObjectName("Card")
            v = QVBoxLayout(card)
            top = QHBoxLayout()
            t = QLabel(g["title"])
            t.setStyleSheet("font-weight: 600; font-size: 15px;")
            top.addWidget(t)
            top.addStretch()
            menu_btn = QPushButton("\u22EF")
            menu_btn.setFixedWidth(32)

            def make_handler(goal=g, btn=menu_btn):
                def handler():
                    menu = QMenu(self)
                    edit_act = menu.addAction("Edit")
                    del_act = menu.addAction("Delete")
                    chosen = menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
                    if chosen == edit_act:
                        self._edit_goal(goal)
                    elif chosen == del_act:
                        self._delete_goal(goal["id"])
                return handler
            menu_btn.clicked.connect(make_handler())
            top.addWidget(menu_btn)
            v.addLayout(top)

            if g.get("description"):
                desc = QLabel(g["description"])
                desc.setObjectName("SubHeading")
                desc.setWordWrap(True)
                v.addWidget(desc)

            bar = QProgressBar()
            bar.setValue(g["progress_pct"])
            bar.setFormat(f"{g['progress_pct']}%")
            v.addWidget(bar)

            meta_bits = [f"{g['completed_tasks']} completed", f"{g['remaining_tasks']} remaining"]
            if g.get("deadline"):
                meta_bits.append(f"Due {format_friendly_date(g['deadline'])}")
            meta = QLabel("  \u2022  ".join(meta_bits))
            meta.setObjectName("SubHeading")
            v.addWidget(meta)

            self.c_layout.addWidget(card)
        self.c_layout.addStretch()
