from PySide6.QtWidgets import QApplication
from .app.barcode_ui import BarcodeCopierWindow  # relatív import

def main():
    app = QApplication.instance()
    owns_app = False
    if app is None:
        app = QApplication([])
        owns_app = True

    w = BarcodeCopierWindow()
    w.show()

    if owns_app:
        app.exec()

    return w 

if __name__ == "__main__":
    main()