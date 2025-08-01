import os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QFileDialog,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from .processor import run
from .viewer import CSVViewer

class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Autóköltség Feldolgozó")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "otp_icon.png")))
        self.setMinimumWidth(320)

        # PDF fájl sor
        self.pdf_path_input = QLineEdit()
        self.pdf_browse_btn = QPushButton("📂 Tallózás")
        self.pdf_browse_btn.clicked.connect(self.browse_pdf)

        # Autók Excel sor
        self.xlsx_path_input = QLineEdit()
        self.xlsx_browse_btn = QPushButton("📂 Tallózás")
        self.xlsx_browse_btn.clicked.connect(self.browse_xlsx)

        # Feldolgozás gomb
        self.process_btn = QPushButton("⚙️ Feldolgozás")
        self.process_btn.setFixedSize(300, 40)
        self.process_btn.clicked.connect(self.process_file)

        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        layout.addLayout(self._create_row("PDF fájl:", self.pdf_path_input, self.pdf_browse_btn))
        layout.addLayout(self._create_row("Autók Excel:", self.xlsx_path_input, self.xlsx_browse_btn))
        layout.addWidget(self.process_btn)

        self.setLayout(layout)

    def _create_row(self, label_text, input_widget, button_widget):
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(QLabel(label_text))
        row.addWidget(input_widget)
        row.addWidget(button_widget)
        return row

    def browse_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "PDF fájl kiválasztása", "", "PDF fájlok (*.pdf)")
        if path:
            self.pdf_path_input.setText(path)

    def browse_xlsx(self):
        path, _ = QFileDialog.getOpenFileName(self, "Autók Excel kiválasztása", "", "Excel fájlok (*.xlsx)")
        if path:
            self.xlsx_path_input.setText(path)

    def process_file(self):
        pdf_path = self.pdf_path_input.text()
        xlsx_path = self.xlsx_path_input.text()
        if not pdf_path:
            QMessageBox.warning(self, "Nincs PDF", "Először válassz ki egy PDF-et.")
            return
        if not xlsx_path:
            QMessageBox.warning(self, "Nincs autók Excel", "Először válassz ki egy autók Excel fájlt.")
            return
        try:
            run(pdf_path, xlsx_path)
            QMessageBox.information(self, "Siker", "A feldolgozás sikeresen lefutott.")

            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_csv_path = os.path.join(BASE_DIR, "output", "output.csv")

            viewer = CSVViewer(output_csv_path)
            viewer.exec()
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Hiba történt:\n{str(e)}")