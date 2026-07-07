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

from .processor import run
from .viewer import CSVViewer

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
        self.setWindowTitle("PDF Autóköltség Feldolgozó")
        self.setWindowIcon(QIcon(resource_path("icons", "otp_icon.png")))
        self.setMinimumWidth(320)
        self.setMinimumHeight(220)

        # PDF fájl sor
        self.pdf_path_input = QLineEdit()
        self.pdf_path_input.setPlaceholderText("PDF fájl elérési útja...")
        self.pdf_browse_btn = QPushButton("📂")
        self.pdf_browse_btn.setMaximumWidth(45)
        self.pdf_browse_btn.setToolTip("Tallózás a PDF fájlhoz")
        self.pdf_browse_btn.setStyleSheet(get_browse_button_stylesheet())
        self.pdf_browse_btn.clicked.connect(self.browse_pdf)

        # Autók Excel sor
        self.xlsx_path_input = QLineEdit()
        self.xlsx_path_input.setPlaceholderText("Autók Excel elérési útja...")
        self.xlsx_browse_btn = QPushButton("📂")
        self.xlsx_browse_btn.setMaximumWidth(45)
        self.xlsx_browse_btn.setToolTip("Tallózás az autók Excel fájlhoz")
        self.xlsx_browse_btn.setStyleSheet(get_browse_button_stylesheet())
        self.xlsx_browse_btn.clicked.connect(self.browse_xlsx)

        # Feldolgozás gomb
        self.process_btn = QPushButton("⚙️ Feldolgozás")
        self.process_btn.setMinimumHeight(36)
        self.process_btn.setStyleSheet(get_action_button_stylesheet())
        self.process_btn.setToolTip("PDF és Excel feldolgozása")
        self.process_btn.clicked.connect(self.process_file)

        # Grouping
        input_group = QGroupBox("📁 Bemeneti fájlok")
        input_layout = QVBoxLayout()
        input_layout.addLayout(
            self._create_row("PDF fájl:", self.pdf_path_input, self.pdf_browse_btn)
        )
        input_layout.addLayout(
            self._create_row("Autók Excel:", self.xlsx_path_input, self.xlsx_browse_btn)
        )
        input_group.setLayout(input_layout)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(input_group)
        layout.addWidget(self.process_btn)

        self.setLayout(layout)
        self.setStyleSheet(get_dark_theme_stylesheet())

        self._process_thread = None
        self._process_worker = None
        self._progress_dialog = None

    def _create_row(self, label_text, input_widget, button_widget):
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(QLabel(label_text), 0)
        row.addWidget(input_widget, 1)
        row.addWidget(button_widget, 0)
        return row

    def browse_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "PDF fájl kiválasztása", "", "PDF fájlok (*.pdf)"
        )
        if path:
            self.pdf_path_input.setText(path)

    def browse_xlsx(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Autók Excel kiválasztása", "", "Excel fájlok (*.xlsx)"
        )
        if path:
            self.xlsx_path_input.setText(path)

    def process_file(self):
        pdf_path = self.pdf_path_input.text().strip()
        xlsx_path = self.xlsx_path_input.text().strip()
        if not pdf_path or not os.path.isfile(pdf_path):
            QMessageBox.warning(self, "Nincs PDF", "Válassz létező PDF fájlt.")
            return
        if not xlsx_path or not os.path.isfile(xlsx_path):
            QMessageBox.warning(
                self, "Nincs autók Excel", "Válassz létező autók Excel fájlt."
            )
            return

        self.process_btn.setEnabled(False)
        self._progress_dialog = QProgressDialog("Előkészítés...", "Mégse", 0, 100, self)
        self._progress_dialog.setWindowTitle("PDF feldolgozás")
        self._progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress_dialog.setMinimumDuration(0)
        self._progress_dialog.setAutoClose(False)
        self._progress_dialog.setAutoReset(False)

        self._process_thread = QThread(self)
        self._process_worker = BackgroundWorker(run, pdf_path, xlsx_path)
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

        output_csv_path = result.get("output_csv")
        vehicle_count = result.get("vehicle_count", 0)
        QMessageBox.information(
            self,
            "Siker",
            f"A feldolgozás sikeresen lefutott. Feldolgozott autók: {vehicle_count}",
        )
        if output_csv_path:
            viewer = CSVViewer(output_csv_path)
            viewer.exec()

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
