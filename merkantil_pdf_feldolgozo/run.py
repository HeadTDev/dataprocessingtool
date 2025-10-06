from PySide6.QtWidgets import QApplication
from .app.main_ui import MainUI  # ha nálad más a név (pl. MainUI), itt is állítsd

def main():
    app = QApplication.instance()
    owns_app = False
    if app is None:
        app = QApplication([])
        owns_app = True

    w = MainUI()  # igazítsd a tényleges osztálynevet
    w.show()

    if owns_app:
        app.exec()

    return w

if __name__ == "__main__":
    main()