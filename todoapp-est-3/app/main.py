"""TaskForge - entry point.

Run in development:
    python -m app.main

Build to .exe: see build.bat / README.md.
"""
import sys
import os
import logging
import traceback

# Allow running as `python app/main.py` too, not only `python -m app.main`
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from app.database.db import init_db
from app.config.constants import get_log_path
from app.services import settings_service
from app.ui.main_window import MainWindow

log = logging.getLogger("taskforge.main")


def _install_excepthook(app: QApplication):
    """Catch-all so unexpected errors are logged and shown, never a silent crash."""
    def handle(exc_type, exc_value, exc_tb):
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logging.getLogger("taskforge").error("Unhandled exception:\n%s", text)
        try:
            QMessageBox.critical(
                None, "Unexpected error",
                f"Something went wrong:\n\n{exc_value}\n\nDetails were written to:\n{get_log_path()}")
        except Exception:
            pass
    sys.excepthook = handle


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # keep running in tray
    app.setApplicationName("TaskForge")

    _install_excepthook(app)

    try:
        init_db()
    except Exception as e:
        QMessageBox.critical(None, "Database error",
                              f"Could not open or create the local database:\n{e}\n\n"
                              f"Try deleting the database file and restarting, or restore from a backup.")
        sys.exit(1)

    window = MainWindow(user_name="there")

    if settings_service.get_bool("start_minimized"):
        window.hide()
    else:
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
