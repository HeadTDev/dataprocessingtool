# run.py

from PySide6.QtWidgets import QApplication
from app.main_ui import MainUI
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainUI()
    window.show()
    sys.exit(app.exec())