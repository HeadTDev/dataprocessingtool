import sys
import subprocess
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel

BUTTON_SIZE = (300, 40)

class MainMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Főmenü")
        self.setWindowIcon(QIcon("synthwave_icon.png"))
        self.setMinimumSize(320, 160)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Válassz egy alkalmazást:"))

        buttons = [
            ("💸 Merkantil PDF Feldolgozó", "merkantil_pdf_feldolgozo/run.py"),
            ("📂 Vonalkód PDF Másolás", "barcode_pdf_masolas/run.py"),
            ("📚 Cofanet Help", "cofanet_help/run.py")
        ]

        for text, path in buttons:
            btn = QPushButton(text)
            btn.setFixedSize(*BUTTON_SIZE)
            btn.clicked.connect(lambda _, p=path: subprocess.Popen([sys.executable, p]))
            layout.addWidget(btn)

        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainMenu()
    window.show()
    sys.exit(app.exec())