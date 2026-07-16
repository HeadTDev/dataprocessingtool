import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.backend.modules.merkantil.service import run
from app.frontend.components.csv_viewer import CSVViewer
from app.frontend.components.drag_drop_line_edit import DragDropLineEdit

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
        self.setWindowTitle("PDF Autóköltség Feldolgozó")
        self.setWindowIcon(QIcon(resource_path("icons", "otp_icon.png")))
        self.setMinimumWidth(320)
        self.setMinimumHeight(220)

        # PDF fájl sor
        self.pdf_path_input = DragDropLineEdit(allowed_extensions=[".pdf"])
        self.pdf_path_input.setPlaceholderText("Húzd ide a PDF fájlt, vagy tallózz...")
        self.pdf_browse_btn = QPushButton("📂")
        self.pdf_browse_btn.setMaximumWidth(45)
        self.pdf_browse_btn.setToolTip("Tallózás a PDF fájlhoz")
        self.pdf_browse_btn.setStyleSheet(get_browse_button_stylesheet())
        self.pdf_browse_btn.clicked.connect(self.browse_pdf)

        # Autók Excel sor
        self.xlsx_path_input = DragDropLineEdit(allowed_extensions=[".xlsx", ".xls"])
        self.xlsx_path_input.setPlaceholderText("Húzd ide az autók Excel fájlt, vagy tallózz...")
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

        self._process_task = None

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

        self._process_task = BackgroundTask(
            self,
            self.process_btn,
            "PDF feldolgozás",
            run,
            (pdf_path, xlsx_path),
            self._on_process_result,
            self._on_process_error,
            self._on_process_finished,
        )
        self._process_task.start()

    def _on_process_result(self, result):
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
        QMessageBox.critical(self, "Hiba", f"Hiba történt:\n{error_message}")

    def _on_process_finished(self):
        self._process_task = None

    def closeEvent(self, event):
        if self._process_task is not None:
            self._process_task.cancel()
        event.accept()
