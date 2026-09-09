"""Qt stylesheets for a clean, modern, rounded-card look in dark and light mode.
Pure QSS (no external image assets required) so the app looks polished
without dragging in a whole design-asset pipeline.
"""
import sys

DARK = {
    "bg": "#15171C",
    "surface": "#1E2129",
    "surface2": "#262A34",
    "border": "#31353F",
    "text": "#E8E9ED",
    "text_dim": "#9198A6",
    "accent": "#6C7CFF",
    "accent2": "#8B5CF6",
    "success": "#4CAF50",
    "danger": "#F44336",
}

LIGHT = {
    "bg": "#F5F6FA",
    "surface": "#FFFFFF",
    "surface2": "#F0F1F6",
    "border": "#E1E3EA",
    "text": "#1C1E26",
    "text_dim": "#666B78",
    "accent": "#5B6EF5",
    "accent2": "#8B5CF6",
    "success": "#2E7D32",
    "danger": "#D32F2F",
}


def build_qss(palette: dict) -> str:
    p = palette
    return f"""
    QWidget {{
        background-color: {p['bg']};
        color: {p['text']};
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 13px;
    }}
    QMainWindow, #Sidebar {{
        background-color: {p['bg']};
    }}
    #Sidebar {{
        background-color: {p['surface']};
        border-right: 1px solid {p['border']};
    }}
    QLabel#Heading {{
        font-size: 22px;
        font-weight: 600;
    }}
    QLabel#SubHeading {{
        color: {p['text_dim']};
        font-size: 13px;
    }}
    QPushButton {{
        background-color: {p['surface2']};
        border: 1px solid {p['border']};
        border-radius: 10px;
        padding: 8px 14px;
        color: {p['text']};
    }}
    QPushButton:hover {{
        background-color: {p['border']};
    }}
    QPushButton#Primary {{
        background-color: {p['accent']};
        color: white;
        border: none;
        font-weight: 600;
    }}
    QPushButton#Primary:hover {{
        background-color: {p['accent2']};
    }}
    QPushButton#NavButton {{
        text-align: left;
        border: none;
        background: transparent;
        padding: 10px 14px;
        border-radius: 10px;
        font-size: 14px;
    }}
    QPushButton#NavButton:checked {{
        background-color: {p['accent']};
        color: white;
        font-weight: 600;
    }}
    QPushButton#NavButton:hover:!checked {{
        background-color: {p['surface2']};
    }}
    QFrame#Card {{
        background-color: {p['surface']};
        border: 1px solid {p['border']};
        border-radius: 14px;
    }}
    QFrame#Card:hover {{
        border: 1px solid {p['accent']};
    }}
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox {{
        background-color: {p['surface2']};
        border: 1px solid {p['border']};
        border-radius: 8px;
        padding: 6px 10px;
        color: {p['text']};
    }}
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
        border: 1px solid {p['accent']};
    }}
    QScrollArea, QListWidget, QTableWidget, QCalendarWidget {{
        background-color: transparent;
        border: none;
    }}
    QListWidget::item {{
        border-radius: 8px;
        padding: 4px;
    }}
    QListWidget::item:selected {{
        background-color: {p['accent']};
        color: white;
    }}
    QProgressBar {{
        border: none;
        border-radius: 8px;
        background-color: {p['surface2']};
        text-align: center;
        height: 14px;
        color: {p['text']};
    }}
    QProgressBar::chunk {{
        background-color: {p['accent']};
        border-radius: 8px;
    }}
    QTabWidget::pane {{
        border: 1px solid {p['border']};
        border-radius: 10px;
    }}
    QTabBar::tab {{
        background: {p['surface2']};
        padding: 8px 16px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background: {p['accent']};
        color: white;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
    }}
    QScrollBar::handle:vertical {{
        background: {p['border']};
        border-radius: 5px;
        min-height: 30px;
    }}
    QCheckBox::indicator {{
        width: 16px; height: 16px;
        border-radius: 4px;
        border: 1px solid {p['border']};
    }}
    QCheckBox::indicator:checked {{
        background-color: {p['accent']};
    }}
    QToolTip {{
        background-color: {p['surface2']};
        color: {p['text']};
        border: 1px solid {p['border']};
        padding: 4px 8px;
        border-radius: 6px;
    }}
    """


def get_stylesheet(mode: str) -> str:
    return build_qss(LIGHT if mode == "light" else DARK)


def get_palette(mode: str) -> dict:
    return LIGHT if mode == "light" else DARK


def detect_system_theme() -> str:
    """Best-effort detection of the OS light/dark preference.

    On Windows this reads the real "AppsUseLightTheme" registry value.
    Elsewhere (and if the registry read fails for any reason) it falls back
    to inspecting the current Qt palette's window-color lightness.
    """
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return "light" if value == 1 else "dark"
        except OSError:
            pass
    try:
        from PySide6.QtGui import QGuiApplication
        app = QGuiApplication.instance()
        if app is not None:
            color = app.palette().window().color()
            return "light" if color.lightness() > 128 else "dark"
    except Exception:
        pass
    return "dark"
