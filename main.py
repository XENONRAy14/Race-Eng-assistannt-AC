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
from assetto.ac_detector import ACDetector, ACInstallation
from config.user_settings import get_user_settings


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
    
    # Create detector
    detector = ACDetector()
    
    # Load saved AC path from user settings BEFORE detection
    user_settings = get_user_settings()
    saved_game_path = user_settings.get_ac_game_path()
    
    if saved_game_path and saved_game_path.exists():
        # Pre-configure detector with saved path
        docs_path = Path.home() / "Documents" / "Assetto Corsa"
        docs_path.mkdir(parents=True, exist_ok=True)
        
        detector._installation = ACInstallation(documents_path=docs_path)
        detector._installation.game_path = saved_game_path
        detector._installation.cars_path = saved_game_path / "content" / "cars"
        detector._installation.tracks_path = saved_game_path / "content" / "tracks"
        detector._installation.is_valid = True
        detector._installation.can_write_setups = True
    
    # Create and show main window
    window = MainWindow(repository, detector)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
