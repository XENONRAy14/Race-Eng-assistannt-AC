"""
Race Engineer Assistant - Assetto Corsa Virtual Race Engineer
Main entry point for the application.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from ui.main_window import MainWindow
from data.setup_repository import SetupRepository
from assetto.ac_detector import ACDetector


def main():
    """Application entry point."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("Race Engineer Assistant")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("TougeEngineering")
    
    # Initialize database
    db_path = PROJECT_ROOT / "data" / "database.db"
    repository = SetupRepository(db_path)
    repository.initialize_database()
    
    # Detect Assetto Corsa installation
    detector = ACDetector()
    ac_path = detector.detect_ac_documents_path()
    
    # Create and show main window
    window = MainWindow(repository, detector)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
