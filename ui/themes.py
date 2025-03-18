from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

THEMES = {
    "light": {
        "window": "#FFFFFF",
        "text": "#000000",
        "link": "#0066CC",
        "toolbar": "#F0F0F0",
        "accent": "#1E90FF",
        "border": "#CCCCCC"
    },
    "dark": {
        "window": "#2B2B2B",
        "text": "#FFFFFF",
        "link": "#61AFEF",
        "toolbar": "#333333",
        "accent": "#528BFF",
        "border": "#555555"
    },
    "sepia": {
        "window": "#F8F0E0",
        "text": "#5B4636",
        "link": "#6B4226",
        "toolbar": "#EFE6D4",
        "accent": "#A67D5D",
        "border": "#D0C0A0"
    },
    "nord": {
        "window": "#2E3440",
        "text": "#ECEFF4",
        "link": "#88C0D0",
        "toolbar": "#3B4252",
        "accent": "#81A1C1",
        "border": "#4C566A"
    },
    "dracula": {
        "window": "#282A36",
        "text": "#F8F8F2",
        "link": "#BD93F9",
        "toolbar": "#383A59",
        "accent": "#FF79C6",
        "border": "#44475A"
    }
}

def apply_theme(app, theme_name):
    theme = THEMES.get(theme_name, THEMES["light"])
    palette = QPalette()
    
    # Configure main colors
    palette.setColor(QPalette.ColorRole.Window, QColor(theme["window"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(theme["text"]))
    palette.setColor(QPalette.ColorRole.Link, QColor(theme["link"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(theme["toolbar"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(theme["text"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(theme["accent"]))
    
    app.setPalette(palette)
    app.setStyleSheet(f"""
        QMainWindow {{
            background-color: {theme["window"]};
        }}
        QToolBar {{
            background-color: {theme["toolbar"]};
            border-bottom: 1px solid {theme["border"]};
            spacing: 5px;
            padding: 5px;
        }}
        QLineEdit, QComboBox, QSpinBox {{
            background-color: {theme["window"]};
            color: {theme["text"]};
            border: 1px solid {theme["border"]};
            border-radius: 4px;
            padding: 4px;
        }}
        QPushButton {{
            background-color: {theme["toolbar"]};
            color: {theme["text"]};
            border: 1px solid {theme["border"]};
            border-radius: 4px;
            padding: 6px 12px;
        }}
        QPushButton:hover {{
            background-color: {theme["accent"]};
            color: white;
        }}
        QTabWidget::pane {{
            border: 1px solid {theme["border"]};
        }}
        QTabBar::tab {{
            background-color: {theme["toolbar"]};
            color: {theme["text"]};
            padding: 8px 12px;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background-color: {theme["accent"]};
            color: white;
        }}
        QStatusBar {{
            background-color: {theme["toolbar"]};
            color: {theme["text"]};
        }}
        QMenu {{
            background-color: {theme["toolbar"]};
            color: {theme["text"]};
            border: 1px solid {theme["border"]};
        }}
        QMenu::item:selected {{
            background-color: {theme["accent"]};
            color: white;
        }}
        QScrollBar:vertical {{
            background: {theme["toolbar"]};
            width: 14px;
            margin: 2px 0;
            border: 1px solid {theme["border"]};
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {theme["accent"]};
            min-height: 20px;
            border-radius: 4px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            background: none;
        }}
        QTableWidget {{
            background: {theme["window"]};
            color: {theme["text"]};
            gridline-color: {theme["border"]};
        }}
        QHeaderView::section {{
            background-color: {theme["toolbar"]};
            color: {theme["text"]};
            padding: 4px;
            border: 1px solid {theme["border"]};
        }}
    """)
