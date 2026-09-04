import sys
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen, QMessageBox

from app.resources.resource_path import resource_path
from app.backend.services.logging_service import get_logger

logger = get_logger("app")


def _log_uncaught_exception(exc_type, exc_value, exc_traceback):
    """Safety net for .pyw (no console): without this, an exception that
    isn't wrapped in its own try/except would only ever go to stderr, which
    pythonw.exe silently discards - no window, no log entry, no trace of
    what happened. Routes every otherwise-unhandled exception (including
    ones raised inside Qt slots) into the same log the in-app log viewer
    reads, so nothing fails completely silently."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.opt(exception=(exc_type, exc_value, exc_traceback)).error("Uncaught exception.")


sys.excepthook = _log_uncaught_exception


def main():
    logger.info("Application starting.")
    qt_app = QApplication(sys.argv)

    pixmap = QPixmap(resource_path("icons", "synthwave_icon.png")).scaled(
        250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation
    )
    splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
    splash.setFont(QFont("Arial", 12, QFont.Bold))
    splash.show()
    
    # 1. Lépés: Gyors frissítéskeresés
    splash.showMessage("Frissítések keresése...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    qt_app.processEvents()

    from app.backend.services.update_service import check_update_available, do_update
    has_update, release = check_update_available()

    if has_update:
        splash.hide()  # Splash eltüntetése, amíg dönt a felhasználó
        remote_tag = release.get("tag_name")
        reply = QMessageBox.question(
            None,
            "Frissítés elérhető",
            f"Új verzió érhető el: {remote_tag}\nSzeretnéd most letölteni és telepíteni?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            splash.show()
            splash.showMessage("Frissítés letöltése... Kérlek várj.", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
            qt_app.processEvents()
            
            def splash_progress(label, current, total, done):
                if done:
                    return
                if total and total > 0:
                    pct = int((current / total) * 100)
                    splash.showMessage(f"Letöltés... {pct}%", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
                else:
                    splash.showMessage(f"{label} {current}", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
                qt_app.processEvents()

            try:
                do_update(release, progress_cb=splash_progress)
                splash.showMessage("Újraindítás...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
                qt_app.processEvents()
                
                # 2. Lépés: Automatikus újraindítás a letöltött, friss kóddal
                subprocess.Popen([sys.executable] + sys.argv)
                sys.exit(0)
            except Exception as e:
                logger.exception("Update failed.")
                splash.hide()
                QMessageBox.critical(None, "Hiba", f"Sikertelen frissítés:\n{e}")
        
        splash.show()

    # 3. Lépés: Nehéz modulok beimportálása és alkalmazás indítása
    splash.showMessage("Indítás...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    qt_app.processEvents()

    from app.frontend.main_window import MainWindow

    window = MainWindow()
    window.show()
    
    splash.finish(window)
    return qt_app.exec()


if __name__ == "__main__":
    sys.exit(main())
