import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from app.resources.resource_path import resource_path


def main():
    qt_app = QApplication(sys.argv)

    # Splash screen megjelenítése a nehéz importok előtt
    pixmap = QPixmap(resource_path("icons", "synthwave_icon.png")).scaled(
        250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation
    )
    splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
    splash.setFont(QFont("Arial", 12, QFont.Bold))
    splash.show()
    splash.showMessage("Indítás...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    
    # GUI frissítése, hogy a splash screen azonnal kirajzolódjon
    qt_app.processEvents()

    # Nehéz modulok beimportálása (pandas, PyPDF2 stb.)
    from app.frontend.main_window import MainWindow, start_auto_update

    window = MainWindow()
    window.show()
    
    # Splash eltüntetése, ahogy a főablak megjelenik
    splash.finish(window)

    QTimer.singleShot(500, lambda: start_auto_update(window.version_label))
    return qt_app.exec()


if __name__ == "__main__":
    sys.exit(main())
