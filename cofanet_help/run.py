import sys
from PySide6.QtWidgets import QApplication
from app.main_ui import CofanetHelpUI

def main():
    app = QApplication(sys.argv)
    window = CofanetHelpUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()