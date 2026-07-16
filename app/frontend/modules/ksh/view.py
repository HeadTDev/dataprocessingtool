import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.backend.modules.ksh.service import Processor

from app.backend.workers.background_task import BackgroundTask
from app.frontend.theme import (
    get_action_button_stylesheet,
    get_browse_button_stylesheet,
    get_dark_theme_stylesheet,
)
from app.resources.resource_path import resource_path


class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KSH + Matstamm egyesítő")
        self.setWindowIcon(QIcon(resource_path("icons", "ksh_icon.png")))
        self.setMinimumWidth(320)
        self.setMinimumHeight(210)

        self.ksh_input = QLineEdit()
        self.ksh_input.setPlaceholderText("KSH fájl elérési útja...")
        ksh_btn = QPushButton("📂")
        ksh_btn.setMaximumWidth(45)
        ksh_btn.setToolTip("Tallózás a KSH fájlhoz")
        ksh_btn.setStyleSheet(get_browse_button_stylesheet())
        ksh_btn.clicked.connect(self.browse_ksh)

        self.mat_input = QLineEdit()
        self.mat_input.setPlaceholderText("Matstamm fájl elérési útja...")
        mat_btn = QPushButton("📂")
        mat_btn.setMaximumWidth(45)
        mat_btn.setToolTip("Tallózás a Matstamm fájlhoz")
        mat_btn.setStyleSheet(get_browse_button_stylesheet())
        mat_btn.clicked.connect(self.browse_mat)

        self.process_btn = QPushButton("⚙️ Feldolgozás")
        self.process_btn.setMinimumHeight(36)
        self.process_btn.setStyleSheet(get_action_button_stylesheet())
        self.process_btn.setToolTip("KSH és Matstamm fájlok feldolgozása")
        self.process_btn.clicked.connect(self.process_files)

        # Grouping
        input_group = QGroupBox("📁 Bemeneti fájlok")
        input_layout = QVBoxLayout()
        input_layout.addLayout(self._row("KSH fájl:", self.ksh_input, ksh_btn))
        input_layout.addLayout(self._row("Matstamm:", self.mat_input, mat_btn))
        input_group.setLayout(input_layout)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(input_group)
        layout.addWidget(self.process_btn)

        self.processor = Processor()
        self.setStyleSheet(get_dark_theme_stylesheet())

        self._process_task = None

    def _row(self, label_text, input_widget, button_widget):
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(QLabel(label_text), 0)
        row.addWidget(input_widget, 1)
        row.addWidget(button_widget, 0)
        return row

    def browse_ksh(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "KSH fájl kiválasztása",
            "",
            "Minden fájl (*.*)",
        )
        if path:
            self.ksh_input.setText(path)

    def browse_mat(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Matstamm fájl kiválasztása",
            "",
            "Excel munkafüzet (*.xlsx);;Minden fájl (*.*)",
        )
        if path:
            self.mat_input.setText(path)

    def process_files(self):
        ksh = self.ksh_input.text().strip()
        mat = self.mat_input.text().strip()

        if not ksh or not os.path.isfile(ksh):
            QMessageBox.warning(self, "Hiányzó KSH", "Válassz létező KSH fájlt.")
            return
        if not mat or not os.path.isfile(mat):
            QMessageBox.warning(
                self, "Hiányzó Matstamm", "Válassz létező Matstamm fájlt."
            )
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Kimeneti XLSX fájl mentése",
            "data.xlsx",
            "Excel fájlok (*.xlsx);;Minden fájl (*.*)",
        )
        if not save_path:
            QMessageBox.information(
                self, "Mentés megszakítva", "A feldolgozás nem indult el."
            )
            return

        self._process_task = BackgroundTask(
            self,
            self.process_btn,
            "KSH feldolgozás",
            self.processor.process,
            (ksh, mat, save_path),
            self._on_process_result,
            self._on_process_error,
            self._on_process_finished,
        )
        self._process_task.start()

    def _on_process_result(self, result):
        if result.get("cancelled"):
            QMessageBox.information(self, "Megszakítva", "A feldolgozás megszakítva.")
            return

        output_path = result.get("output_path")
        row_count = result.get("row_count", 0)
        cleanup_message = result.get("cleanup_message", "")
        message = f"A feldolgozás elkészült.\nFeldolgozott sorok: {row_count}\nAz új fájl itt található:\n{output_path}"
        if cleanup_message:
            message += f"\n{cleanup_message}"
        QMessageBox.information(self, "Kész", message)

    def _on_process_error(self, error_message):
        QMessageBox.critical(self, "Hiba", f"Hiba történt:\n{error_message}")

    def _on_process_finished(self):
        self._process_task = None

    def closeEvent(self, event):
        if self._process_task is not None:
            self._process_task.cancel()
        event.accept()
