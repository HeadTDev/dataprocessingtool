from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from app.backend.services.update_service import read_local_version_info
from app.frontend.routes import ROUTES, AppRoute
from app.frontend.theme import get_action_button_stylesheet, get_dark_theme_stylesheet
from app.resources.resource_path import resource_path

BUTTON_SIZE = (300, 40)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Főmenü")
        self.setWindowIcon(QIcon(resource_path("icons", "synthwave_icon.png")))
        self.setMinimumSize(320, 220)
        
        info = read_local_version_info()
        ver = info.get("version") or "ismeretlen"
        self.version_label = QLabel(f"Verzió: {ver}")
        
        font = self.version_label.font()
        font.setPointSize(font.pointSize() - 1)
        self.version_label.setFont(font)
        
        self._open_windows = {}
        self.init_ui()
        self.setStyleSheet(get_dark_theme_stylesheet())

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Válassz egy alkalmazást:"))
        for route in ROUTES:
            btn = QPushButton(route.label)
            btn.setFixedSize(*BUTTON_SIZE)
            btn.setStyleSheet(get_action_button_stylesheet())
            btn.setEnabled(route.enabled)
            btn.clicked.connect(lambda _, r=route: self.open_route(r))
            layout.addWidget(btn)
        layout.addStretch()
        layout.addWidget(self.version_label, alignment=Qt.AlignRight)
        self.setLayout(layout)

    def open_route(self, route: AppRoute):
        window = self._open_windows.get(route.id)
        if window is not None:
            try:
                window.show()
                window.raise_()
                window.activateWindow()
                return
            except RuntimeError:
                self._open_windows.pop(route.id, None)
        try:
            window = route.view_class()
        except Exception as exc:
            QMessageBox.critical(self, "Hiba", f"Hiba a modul indításakor: {route.label}\n{exc}")
            return
        self._open_windows[route.id] = window
        try:
            window.destroyed.connect(lambda: self._open_windows.pop(route.id, None))
        except Exception:
            pass
        window.show()
        window.raise_()
        window.activateWindow()

    def closeEvent(self, event):
        for window in list(self._open_windows.values()):
            try:
                window.close()
            except Exception:
                pass
        event.accept()


# Static import hint for PyInstaller
if False:
    from app.frontend.modules.barcode_pdf.view import BarcodeCopierWindow as _BarcodeCopierWindow
    from app.frontend.modules.cofanet.view import CofanetHelpUI as _CofanetHelpUI
    from app.frontend.modules.ksh.view import MainUI as _KshView
    from app.frontend.modules.merkantil.view import MainUI as _MerkantilView
    from app.frontend.modules.mouse_mover.view import MainUI as _MouseMoverView
