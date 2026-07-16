import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from app.frontend.main_window import MainWindow, start_auto_update


def main():
    qt_app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    QTimer.singleShot(500, lambda: start_auto_update(window.version_label))
    return qt_app.exec()


if __name__ == "__main__":
    sys.exit(main())
