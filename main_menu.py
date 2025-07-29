import sys
import subprocess
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QSizePolicy

# Állítható gombméret (szélesség, magasság)
BUTTON_SIZE = (300, 40)

class MainMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Főmenü")
        self.setMinimumSize(320, 160)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        label = QLabel("Válassz egy alkalmazást:")
        layout.addWidget(label)

        self.pdf_button = QPushButton("Merkantil PDF Feldolgozó")
        self.pdf_button.setFixedSize(*BUTTON_SIZE)
        layout.addWidget(self.pdf_button)
        self.pdf_button.clicked.connect(self.launch_pdf_feldolgozo)

        self.barcode_button = QPushButton("Vonalkód PDF Másolás")
        self.barcode_button.setFixedSize(*BUTTON_SIZE)
        layout.addWidget(self.barcode_button)
        self.barcode_button.clicked.connect(self.launch_barcode_pdf_masolas)

        self.cofanet_button = QPushButton("Cofanet Help")
        self.cofanet_button.setFixedSize(*BUTTON_SIZE)
        layout.addWidget(self.cofanet_button)
        self.cofanet_button.clicked.connect(self.launch_cofanet_help)

        self.setLayout(layout)

    def launch_pdf_feldolgozo(self):
        subprocess.Popen([sys.executable, "merkantil_pdf_feldolgozo/run.py"])

    def launch_barcode_pdf_masolas(self):
        subprocess.Popen([sys.executable, "barcode_pdf_masolas/run.py"])

    def launch_cofanet_help(self):
        subprocess.Popen([sys.executable, "cofanet_help/run.py"])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainMenu()
    window.show()
    sys.exit(app.exec())