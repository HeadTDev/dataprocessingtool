#!/usr/bin/env python3
"""
Standalone test script for the mouse mover application.
This can be run independently to test the mouse mover.

Usage:
    python3 mouse_mover/test_standalone.py
"""

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    from app.mouse_mover_ui import MouseMoverWindow
    
    print("Starting Mouse Mover Application...")
    print("Note: This requires a display environment to run.")
    
    app = QApplication(sys.argv)
    window = MouseMoverWindow()
    window.show()
    
    print("Application window opened.")
    print("Close the window to exit.")
    
    sys.exit(app.exec())
