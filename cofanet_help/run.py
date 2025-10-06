from PySide6.QtWidgets import QApplication
from .app.main_ui import CofanetHelpUI  # relatív import

def main():
    app = QApplication.instance()
    owns_app = False
    if app is None:
        app = QApplication([])
        owns_app = True

    w = CofanetHelpUI()
    w.show()

    if owns_app:
        app.exec()

    return w

if __name__ == "__main__":
    main()