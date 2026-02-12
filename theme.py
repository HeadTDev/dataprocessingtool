"""
Shared theme and styling utilities for DataProcessingTool.
"""

# Color palette
DARK_BG = "#1e1e1e"
LIGHT_TEXT = "#e0e0e0"
BORDER_COLOR = "#444444"
INPUT_BG = "#2a2a2a"
ACCENT_CYAN = "#00aaff"

# Minimal gray button colors
BUTTON_BG = "#555555"
BUTTON_BG_HOVER = "#666666"
BUTTON_BG_PRESSED = "#444444"
DISABLED_BG = "#333333"
DISABLED_TEXT = "#666666"


def get_dark_theme_stylesheet():
    """Returns the dark theme stylesheet for the entire application."""
    return """
        QWidget {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }
        QGroupBox {
            color: #e0e0e0;
            border: 1px solid #444444;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
        }
        QLineEdit {
            background-color: #2a2a2a;
            color: #e0e0e0;
            border: 1px solid #444444;
            border-radius: 3px;
            padding: 4px;
        }
        QLineEdit:focus {
            border: 1px solid #00aaff;
        }
        QSlider::groove:horizontal {
            border: 1px solid #444444;
            height: 6px;
            background: #2a2a2a;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #00aaff;
            border: 1px solid #00aaff;
            width: 14px;
            margin: -4px 0;
            border-radius: 7px;
        }
        QSlider::handle:horizontal:hover {
            background: #00ccff;
        }
        QLabel {
            color: #e0e0e0;
        }
    """


def get_action_button_stylesheet():
    """Returns stylesheet for primary action buttons (Process, Copy, Start, etc.) - minimal gray with subtle hover"""
    return """
        QPushButton {
            background-color: #555555;
            color: #e0e0e0;
            border: 1px solid #444444;
            border-radius: 4px;
            font-weight: bold;
            font-size: 13px;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #666666;
        }
        QPushButton:pressed {
            background-color: #444444;
        }
        QPushButton:disabled {
            background-color: #333333;
            color: #666666;
        }
    """


def get_browse_button_stylesheet():
    """Returns stylesheet for browse buttons (secondary action) - compact, minimal"""
    return """
        QPushButton {
            background-color: #444444;
            color: #e0e0e0;
            border: 1px solid #333333;
            border-radius: 3px;
            font-size: 12px;
            padding: 4px 8px;
        }
        QPushButton:hover {
            background-color: #555555;
        }
        QPushButton:pressed {
            background-color: #333333;
        }
        QPushButton:disabled {
            background-color: #2a2a2a;
            color: #555555;
        }
    """
