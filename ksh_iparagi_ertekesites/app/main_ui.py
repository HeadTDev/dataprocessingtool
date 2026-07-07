import os
import sys

from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .process import Processor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from background_worker import BackgroundWorker
from theme import (
    get_action_button_stylesheet,
    get_browse_button_stylesheet,
    get_dark_theme_stylesheet,
)
from utils import resource_path


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

        self._process_thread = None
        self._process_worker = None
        self._progress_dialog = None

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

        self.process_btn.setEnabled(False)
        self._progress_dialog = QProgressDialog("Előkészítés...", "Mégse", 0, 100, self)
        self._progress_dialog.setWindowTitle("KSH feldolgozás")
        self._progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress_dialog.setMinimumDuration(0)
        self._progress_dialog.setAutoClose(False)
        self._progress_dialog.setAutoReset(False)

        self._process_thread = QThread(self)
        self._process_worker = BackgroundWorker(
            self.processor.process, ksh, mat, save_path
        )
        self._process_worker.moveToThread(self._process_thread)

        self._process_thread.started.connect(self._process_worker.run)
        self._process_worker.progress.connect(self._on_process_progress)
        self._process_worker.result.connect(self._on_process_result)
        self._process_worker.error.connect(self._on_process_error)
        self._process_worker.finished.connect(self._process_thread.quit)
        self._process_worker.finished.connect(self._process_worker.deleteLater)
        self._process_thread.finished.connect(self._process_thread.deleteLater)
        self._process_thread.finished.connect(self._on_process_finished)
        self._progress_dialog.canceled.connect(self._process_worker.request_cancel)

        self._process_thread.start()

    def _on_process_progress(self, message, current, total):
        if self._progress_dialog is None:
            return
        if total > 0:
            self._progress_dialog.setRange(0, total)
            self._progress_dialog.setValue(current)
        else:
            self._progress_dialog.setRange(0, 0)
        self._progress_dialog.setLabelText(message)

    def _on_process_result(self, result):
        self._close_progress_dialog()
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
        self._close_progress_dialog()
        QMessageBox.critical(self, "Hiba", f"Hiba történt:\n{error_message}")

    def _on_process_finished(self):
        self.process_btn.setEnabled(True)
        self._process_thread = None
        self._process_worker = None
        self._close_progress_dialog()

    def _close_progress_dialog(self):
        if self._progress_dialog is not None:
            self._progress_dialog.close()
            self._progress_dialog.deleteLater()
            self._progress_dialog = None

    def closeEvent(self, event):
        if self._process_worker is not None:
            self._process_worker.request_cancel()
        event.accept()
