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

from .barcode_copier import copy_matching_pdfs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from background_task import BackgroundTask
from theme import (
    get_action_button_stylesheet,
    get_browse_button_stylesheet,
    get_dark_theme_stylesheet,
)
from utils import resource_path


class BarcodeCopierWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vonalkód alapú PDF másoló")
        self.setWindowIcon(QIcon(resource_path("icons", "pdf_icon.png")))
        self.setMinimumWidth(320)
        self.setMinimumHeight(220)

        self.excel_path_input = QLineEdit()
        self.excel_path_input.setPlaceholderText("Excel fájl elérési útja...")
        self.excel_browse_btn = QPushButton("📂")
        self.excel_browse_btn.setMaximumWidth(45)
        self.excel_browse_btn.setToolTip("Tallózás az Excel fájlhoz")
        self.excel_browse_btn.setStyleSheet(get_browse_button_stylesheet())
        self.excel_browse_btn.clicked.connect(self.browse_excel)

        self.pdf_folder_input = QLineEdit()
        self.pdf_folder_input.setPlaceholderText("PDF mappa elérési útja...")
        self.pdf_browse_btn = QPushButton("📂")
        self.pdf_browse_btn.setMaximumWidth(45)
        self.pdf_browse_btn.setToolTip("Tallózás a PDF mappához")
        self.pdf_browse_btn.setStyleSheet(get_browse_button_stylesheet())
        self.pdf_browse_btn.clicked.connect(self.browse_pdf_folder)

        self.output_folder_input = QLineEdit()
        self.output_folder_input.setPlaceholderText("Kimeneti mappa elérési útja...")
        self.output_browse_btn = QPushButton("📂")
        self.output_browse_btn.setMaximumWidth(45)
        self.output_browse_btn.setToolTip("Tallózás a kimeneti mappához")
        self.output_browse_btn.setStyleSheet(get_browse_button_stylesheet())
        self.output_browse_btn.clicked.connect(self.browse_output_folder)

        self.copy_btn = QPushButton("📋 MÁSOL")
        self.copy_btn.setMinimumHeight(36)
        self.copy_btn.setStyleSheet(get_action_button_stylesheet())
        self.copy_btn.setToolTip("Vonalkódok alapján PDF fájlok másolása")
        self.copy_btn.clicked.connect(self.start_copying)

        # Grouping
        input_group = QGroupBox("📁 Fájlok")
        input_layout = QVBoxLayout()
        input_layout.addLayout(
            self._create_row("Excel:", self.excel_path_input, self.excel_browse_btn)
        )
        input_layout.addLayout(
            self._create_row("PDF mappa:", self.pdf_folder_input, self.pdf_browse_btn)
        )
        input_layout.addLayout(
            self._create_row(
                "Kimenet:", self.output_folder_input, self.output_browse_btn
            )
        )
        input_group.setLayout(input_layout)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(input_group)
        layout.addWidget(self.copy_btn)

        self.setLayout(layout)
        self.setStyleSheet(get_dark_theme_stylesheet())

        self._copy_task = None

    def _create_row(self, label_text, input_widget, button_widget):
        row = QHBoxLayout()
        row.addWidget(QLabel(label_text), 0)
        row.addWidget(input_widget, 1)
        row.addWidget(button_widget, 0)
        return row

    def browse_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Excel fájl kiválasztása", "", "Excel fájlok (*.xlsx *.xls)"
        )
        if path:
            self.excel_path_input.setText(path)

    def browse_pdf_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "PDF fájlokat tartalmazó mappa kiválasztása"
        )
        if folder:
            self.pdf_folder_input.setText(folder)

    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Kimeneti mappa kiválasztása")
        if folder:
            self.output_folder_input.setText(folder)

    def start_copying(self):
        excel_path = self.excel_path_input.text().strip()
        pdf_folder = self.pdf_folder_input.text().strip()
        output_folder = self.output_folder_input.text().strip()

        if not excel_path or not os.path.isfile(excel_path):
            QMessageBox.warning(self, "Hiányzó Excel", "Válassz létező Excel fájlt.")
            return
        if not pdf_folder or not os.path.isdir(pdf_folder):
            QMessageBox.warning(self, "Hiányzó PDF mappa", "Válassz létező PDF mappát.")
            return
        if not output_folder:
            QMessageBox.warning(self, "Hiányzó kimenet", "Válassz kimeneti mappát.")
            return

        self._copy_task = BackgroundTask(
            self,
            self.copy_btn,
            "PDF másolás",
            copy_matching_pdfs,
            (excel_path, pdf_folder, output_folder),
            self._on_copy_result,
            self._on_copy_error,
            self._on_copy_finished,
        )
        self._copy_task.start()

    def _on_copy_result(self, result):
        copied = result.get("copied_count", 0)
        missing = result.get("missing_count", 0)
        if result.get("cancelled"):
            QMessageBox.information(
                self,
                "Megszakítva",
                f"A másolás megszakítva. Eddig {copied} PDF lett átmásolva.",
            )
            return
        QMessageBox.information(
            self,
            "Siker",
            f"{copied} PDF fájl sikeresen átmásolva.\nHiányzó PDF-ek száma: {missing}",
        )

    def _on_copy_error(self, error_message):
        QMessageBox.critical(
            self,
            "Hiba",
            f"Hiba történt a másolás során:\n{error_message}",
        )

    def _on_copy_finished(self):
        self._copy_task = None

    def closeEvent(self, event):
        if self._copy_task is not None:
            self._copy_task.cancel()
        event.accept()
