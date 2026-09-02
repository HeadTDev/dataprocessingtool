"""
Shared theme and styling utilities for DataProcessingTool.
"""

import qtawesome as qta

# --- Color tokens -----------------------------------------------------------

COLOR_BG_BASE = "#1e1e1e"
COLOR_BG_INPUT = "#2a2a2a"
COLOR_BG_ELEVATED = "#2d2d2d"

COLOR_BORDER_DEFAULT = "#444444"
COLOR_BORDER_STRONG = "#555555"

COLOR_TEXT_PRIMARY = "#e0e0e0"
COLOR_TEXT_SECONDARY = "#9a9a9a"
COLOR_TEXT_DISABLED = "#666666"

COLOR_ACCENT = "#D8A468"
COLOR_ACCENT_HOVER = "#E6BD84"
COLOR_ACCENT_PRESSED = "#B9784F"
COLOR_ACCENT_SOFT_BG = "rgba(216, 164, 104, 0.14)"
COLOR_ACCENT_SOFT_BG_HOVER = "rgba(216, 164, 104, 0.24)"
COLOR_ACCENT_SOFT_BORDER = "rgba(216, 164, 104, 0.40)"

COLOR_SUCCESS = "#2fae60"
COLOR_WARNING = "#e6a23c"
COLOR_DANGER = "#e5484d"

COLOR_BUTTON_BG = "#555555"
COLOR_BUTTON_BG_HOVER = "#666666"
COLOR_BUTTON_BG_PRESSED = "#444444"
COLOR_BUTTON_BG_DISABLED = "#333333"

# --- Spacing / sizing tokens (px) -------------------------------------------

SPACE_1 = 2
SPACE_2 = 4
SPACE_3 = 8
SPACE_4 = 12
SPACE_5 = 16

RADIUS_SM = 3
RADIUS_MD = 4
RADIUS_LG = 8

ICON_SIZE_INLINE = 16

BUTTON_HEIGHT_PRIMARY = 36
BUTTON_HEIGHT_COMPACT = 28

SIDEBAR_WIDTH = 280


def get_icon(name: str, color: str = COLOR_ACCENT, color_disabled: str = COLOR_TEXT_DISABLED):
    """Returns a themed Phosphor icon (via qtawesome) for buttons/labels.

    Defaults to the gold accent color so every icon in the app reads as
    part of the same brand accent unless a status color is passed in
    explicitly (e.g. COLOR_DANGER for an error icon). Also greys the icon
    out in the Disabled state so it fades along with the button.

    `name` is the Phosphor glyph name without the "ph." prefix,
    e.g. get_icon("folder-open").
    """
    return qta.icon(f"ph.{name}", color=color, color_disabled=color_disabled)


def get_dark_theme_stylesheet():
    """Returns the dark theme stylesheet for the entire application."""
    return f"""
        QWidget {{
            background-color: {COLOR_BG_BASE};
            color: {COLOR_TEXT_PRIMARY};
        }}
        QGroupBox {{
            color: {COLOR_TEXT_PRIMARY};
            border: 1px solid {COLOR_BORDER_DEFAULT};
            border-radius: {RADIUS_MD}px;
            margin-top: {SPACE_3}px;
            padding-top: {SPACE_3}px;
            font-weight: bold;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
        }}
        QLineEdit {{
            background-color: {COLOR_BG_INPUT};
            color: {COLOR_TEXT_PRIMARY};
            border: 1px solid {COLOR_BORDER_DEFAULT};
            border-radius: {RADIUS_SM}px;
            padding: {SPACE_2}px;
        }}
        QLineEdit:focus {{
            border: 1px solid {COLOR_ACCENT};
        }}
        QSlider::groove:horizontal {{
            border: 1px solid {COLOR_BORDER_DEFAULT};
            height: 6px;
            background: {COLOR_BG_INPUT};
            border-radius: {RADIUS_SM}px;
        }}
        QSlider::handle:horizontal {{
            background: {COLOR_ACCENT};
            border: 1px solid {COLOR_ACCENT};
            width: 14px;
            margin: -4px 0;
            border-radius: 7px;
        }}
        QSlider::handle:horizontal:hover {{
            background: {COLOR_ACCENT_HOVER};
        }}
        QLabel {{
            color: {COLOR_TEXT_PRIMARY};
        }}
        QLabel[role="secondary"] {{
            color: {COLOR_TEXT_SECONDARY};
        }}
    """


def get_action_button_stylesheet():
    """Returns stylesheet for primary action buttons (Process, Copy, Start, etc.).

    Neutral fill so the button doesn't compete with the content, framed in a
    soft gold border that brightens to the full accent on hover - ties the
    button to the gold-accented icon it carries without a full gold fill.
    """
    return f"""
        QPushButton {{
            background-color: {COLOR_BUTTON_BG};
            color: {COLOR_TEXT_PRIMARY};
            border: 1px solid {COLOR_ACCENT_SOFT_BORDER};
            border-radius: {RADIUS_MD}px;
            font-weight: bold;
            font-size: 13px;
            padding: {SPACE_3}px;
        }}
        QPushButton:hover {{
            background-color: {COLOR_BUTTON_BG_HOVER};
            border: 1px solid {COLOR_ACCENT};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_BUTTON_BG_PRESSED};
            border: 1px solid {COLOR_ACCENT_PRESSED};
        }}
        QPushButton:disabled {{
            background-color: {COLOR_BUTTON_BG_DISABLED};
            color: {COLOR_TEXT_DISABLED};
            border: 1px solid {COLOR_BORDER_DEFAULT};
        }}
    """


def get_nav_button_stylesheet():
    """Returns stylesheet for the sidebar navigation buttons (checkable)."""
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {COLOR_TEXT_PRIMARY};
            border: none;
            border-radius: {RADIUS_MD}px;
            text-align: left;
            font-size: 12px;
            padding: {SPACE_3}px {SPACE_3}px;
        }}
        QPushButton:hover {{
            background-color: {COLOR_BG_INPUT};
        }}
        QPushButton:checked {{
            background-color: {COLOR_ACCENT_SOFT_BG};
            color: {COLOR_ACCENT};
            font-weight: bold;
        }}
        QPushButton:disabled {{
            color: {COLOR_TEXT_DISABLED};
        }}
    """


def get_browse_button_stylesheet():
    """Returns stylesheet for icon-only browse buttons - a soft gold "chip"."""
    return f"""
        QPushButton {{
            background-color: {COLOR_ACCENT_SOFT_BG};
            border: 1px solid {COLOR_ACCENT_SOFT_BORDER};
            border-radius: {RADIUS_LG}px;
        }}
        QPushButton:hover {{
            background-color: {COLOR_ACCENT_SOFT_BG_HOVER};
            border: 1px solid {COLOR_ACCENT};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_ACCENT_SOFT_BG_HOVER};
            border: 1px solid {COLOR_ACCENT_PRESSED};
        }}
        QPushButton:disabled {{
            background-color: {COLOR_BG_INPUT};
            border: 1px solid {COLOR_BORDER_DEFAULT};
        }}
    """
