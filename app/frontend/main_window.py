from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.backend.services.update_service import read_local_version_info
from app.backend.services.logging_service import get_logger
from app.frontend.routes import ROUTES
from app.frontend.theme import (
    COLOR_BG_ELEVATED,
    COLOR_BORDER_DEFAULT,
    ICON_SIZE_INLINE,
    SIDEBAR_WIDTH,
    SPACE_2,
    SPACE_3,
    SPACE_4,
    SPACE_5,
    get_dark_theme_stylesheet,
    get_icon,
    get_nav_button_stylesheet,
)
from app.resources.resource_path import resource_path

logger = get_logger("app")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DataProcessingTool")
        self.setWindowIcon(QIcon(resource_path("icons", "synthwave_icon.png")))
        self.setMinimumSize(600, 420)

        self._pages = {}
        self._nav_buttons = {}
        self._pinned_modules = []

        self.stack = QStackedWidget()
        sidebar = self._build_sidebar()

        for route in ROUTES:
            if route.pinned:
                continue
            try:
                page = route.view_class()
            except Exception:
                logger.exception(f"Failed to start module: {route.label}")
                page = QLabel(f"A modul indítása sikertelen: {route.label}")
                page.setAlignment(Qt.AlignCenter)
                page.setWordWrap(True)
            self._pages[route.id] = page
            self.stack.addWidget(page)

        first_enabled = next((r for r in ROUTES if not r.pinned and r.enabled), None)
        if first_enabled is not None:
            self._show_page(first_enabled.id)

        split_row = QHBoxLayout()
        split_row.setContentsMargins(0, 0, 0, 0)
        split_row.setSpacing(0)
        split_row.addWidget(sidebar)
        split_row.addWidget(self.stack, 1)

        footer = self._build_footer()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addLayout(split_row, 1)
        root_layout.addWidget(footer)

        self.setStyleSheet(get_dark_theme_stylesheet())

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(SPACE_4, SPACE_4, SPACE_4, SPACE_4)
        layout.setSpacing(SPACE_2)

        title = QLabel("DataProcessingTool")
        title_font = title.font()
        title_font.setPointSize(title_font.pointSize() + 1)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        layout.addSpacing(SPACE_3)

        icon_size = QSize(ICON_SIZE_INLINE, ICON_SIZE_INLINE)
        for route in ROUTES:
            if route.pinned:
                continue
            btn = QPushButton(f" {route.label}")
            btn.setIcon(get_icon(route.qta_icon))
            btn.setIconSize(icon_size)
            btn.setCheckable(True)
            # No setAutoExclusive: exclusivity is handled manually in
            # _show_page/_show_settings_page, since the Settings page needs a
            # state where none of the nav buttons are checked - Qt's
            # auto-exclusive group refuses to let the last checked button in
            # the group become unchecked.
            btn.setEnabled(route.enabled)
            btn.setStyleSheet(get_nav_button_stylesheet())
            btn.clicked.connect(lambda _, r=route: self._show_page(r.id))
            self._nav_buttons[route.id] = btn
            layout.addWidget(btn)

        layout.addStretch()
        return sidebar

    def _build_footer(self) -> QWidget:
        """Full-width bottom bar: pinned module(s) centered, version at the
        far right - separated from the sidebar/content split by a divider line."""
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"color: {COLOR_BORDER_DEFAULT};")
        outer.addWidget(divider)

        content = QWidget()
        content.setStyleSheet(f"background-color: {COLOR_BG_ELEVATED};")
        outer.addWidget(content)

        row = QHBoxLayout(content)
        row.setContentsMargins(SPACE_5, SPACE_2, SPACE_5, SPACE_2)
        row.setSpacing(SPACE_4)

        row.addStretch()
        for route in ROUTES:
            if not route.pinned:
                continue
            try:
                module = route.view_class()
            except Exception:
                logger.exception(f"Failed to start pinned module: {route.label}")
                placeholder = QLabel(f"Indítás sikertelen: {route.label}")
                row.addWidget(placeholder)
                continue
            self._pinned_modules.append(module)
            row.addWidget(module.footer)
            self.stack.addWidget(module.settings_page)
            module.footer.settingsRequested.connect(
                lambda page=module.settings_page: self._show_settings_page(page)
            )
        row.addStretch()

        info = read_local_version_info()
        ver = info.get("version") or "ismeretlen"
        version_label = QLabel(f"Verzió: {ver}")
        version_font = version_label.font()
        version_font.setPointSize(version_font.pointSize() - 1)
        version_label.setFont(version_font)
        row.addWidget(version_label)

        return container

    def _show_page(self, route_id: str):
        page = self._pages.get(route_id)
        if page is None:
            return
        self.stack.setCurrentWidget(page)
        for rid, btn in self._nav_buttons.items():
            btn.setChecked(rid == route_id)

    def _show_settings_page(self, page: QWidget):
        self.stack.setCurrentWidget(page)
        for btn in self._nav_buttons.values():
            btn.setChecked(False)

    def closeEvent(self, event):
        for page in list(self._pages.values()) + self._pinned_modules:
            try:
                page.close()
            except Exception:
                logger.exception("Failed to close a module page cleanly.")
        event.accept()
