"""
OpenFOAM Case Generator - Main Application Entry Point
"""

import sys
import os

from PyQt6.QtWidgets import QApplication
from view.main_window import MainWindow


def main():
    """Main application entry point"""
    # Create output folder if it doesn't exist
    output_dir = os.path.join(os.getcwd(), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # Pass default output directory to main window
    if hasattr(window, 'set_default_output_dir'):
        window.set_default_output_dir(output_dir)
    
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()