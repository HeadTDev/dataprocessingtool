from PySide6.QtWidgets import QApplication
from barcode_ui import BarcodeCopierWindow
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BarcodeCopierWindow()
    window.show()
    sys.exit(app.exec())