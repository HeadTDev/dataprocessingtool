import sys
from PySide6.QtWidgets import QApplication
from app.barcode_ui import BarcodeCopierWindow

def main():
    app = QApplication(sys.argv)
    window = BarcodeCopierWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()