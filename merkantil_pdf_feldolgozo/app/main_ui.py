from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QLabel
from .processor import run
from .viewer import CSVViewer
import os

BUTTON_SIZE = (300, 40)

class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Autóköltség Feldolgozó")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "otp_icon.png")))
        self.resize(320, 160)

        layout = QVBoxLayout()
        self.label = QLabel("Válaszd ki a PDF fájlt, amelyet feldolgozni szeretnél:")
        layout.addWidget(self.label)
        self.browse_button = QPushButton("📂 Tallózás (PDF)")
        self.browse_button.setFixedSize(*BUTTON_SIZE)
        self.process_button = QPushButton("⚙️ Feldolgozás")
        self.process_button.setFixedSize(*BUTTON_SIZE)

        layout.addWidget(self.browse_button)
        layout.addWidget(self.process_button)
        self.setLayout(layout)

        self.pdf_path = None
        self.browse_button.clicked.connect(self.browse_file)
        self.process_button.clicked.connect(self.process_file)

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "PDF kiválasztása", "Input", "PDF fájlok (*.pdf)")
        if path:
            self.pdf_path = path
            QMessageBox.information(self, "Fájl kiválasztva", f"Kiválasztott fájl:\n{self.pdf_path}")

    def process_file(self):
        if not self.pdf_path:
            QMessageBox.warning(self, "Nincs PDF", "Először válassz ki egy PDF-et.")
            return
        try:
            run(self.pdf_path)
            QMessageBox.information(self, "Siker", "A feldolgozás sikeresen lefutott.")
            viewer = CSVViewer("output/output.csv")
            viewer.exec()
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Hiba történt:\n{str(e)}")