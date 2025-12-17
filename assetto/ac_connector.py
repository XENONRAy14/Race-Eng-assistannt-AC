"""
AC Connector - High-level interface for Assetto Corsa integration.
Combines detection, reading, and writing functionality.
"""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from models.car import Car
from models.track import Track
from models.setup import Setup
from assetto.ac_detector import ACDetector, ACInstallation
from assetto.setup_writer import SetupWriter


@dataclass
class ConnectionStatus:
    """Status of the Assetto Corsa connection."""
    
    is_connected: bool = False
    documents_found: bool = False
    game_found: bool = False
    can_write: bool = False
    
    documents_path: Optional[Path] = None
    game_path: Optional[Path] = None
    
    cars_count: int = 0
    tracks_count: int = 0
    
    error_message: str = ""
    
    def to_dict(self) -> dict:
        return {
            "is_connected": self.is_connected,
            "documents_found": self.documents_found,
            "game_found": self.game_found,
            "can_write": self.can_write,
            "documents_path": str(self.documents_path) if self.documents_path else None,
            "game_path": str(self.game_path) if self.game_path else None,
            "cars_count": self.cars_count,
            "tracks_count": self.tracks_count,
            "error_message": self.error_message
        }


class ACConnector:
    """
    High-level connector for Assetto Corsa.
    Provides unified interface for all AC operations.
    """
    
    def __init__(self, detector: Optional[ACDetector] = None):
        """Initialize connector with optional pre-configured detector."""
        self.detector = detector if detector is not None else ACDetector()
        self.writer = SetupWriter()
        
        self._installation: Optional[ACInstallation] = None
        self._status: Optional[ConnectionStatus] = None
    
    def connect(self) -> ConnectionStatus:
        """
        Establish connection to Assetto Corsa.
        Detects installation and validates access.
        """
        status = ConnectionStatus()
        
        # Detect installation
        self._installation = self.detector.detect_installation()
        
        if self._installation.documents_path:
            status.documents_found = True
            status.documents_path = self._installation.documents_path
        
        if self._installation.game_path:
            status.game_found = True
            status.game_path = self._installation.game_path
        
        if self._installation.is_valid:
            status.is_connected = True
            status.can_write = self._installation.can_write_setups
            
            # Set up writer
            if self._installation.setups_path:
                self.writer.set_base_path(self._installation.setups_path)
            
            # Scan content
            if self._installation.game_path:
                cars = self.detector.scan_cars()
                tracks = self.detector.scan_tracks()
                status.cars_count = len(cars)
                status.tracks_count = len(tracks)
        else:
            status.error_message = "Assetto Corsa installation not found or invalid"
        
        self._status = status
        return status
    
    def get_status(self) -> ConnectionStatus:
        """Get current connection status."""
        if self._status is None:
            return self.connect()
        return self._status
    
    def is_connected(self) -> bool:
        """Check if connected to Assetto Corsa."""
        status = self.get_status()
        return status.is_connected
    
    def get_cars(self, force_refresh: bool = False) -> list[Car]:
        """Get list of available cars."""
        if not self.is_connected():
            return []
        return self.detector.scan_cars(force_refresh)
    
    def get_tracks(self, force_refresh: bool = False) -> list[Track]:
        """Get list of available tracks."""
        if not self.is_connected():
            return []
        return self.detector.scan_tracks(force_refresh)
    
    def get_car(self, car_id: str) -> Optional[Car]:
        """Get a specific car by ID."""
        return self.detector.get_car(car_id)
    
    def get_track(self, track_id: str, config: str = "") -> Optional[Track]:
        """Get a specific track by ID."""
        return self.detector.get_track(track_id, config)
    
    def save_setup(
        self,
        setup: Setup,
        car_id: str,
        track_id: str,
        filename: Optional[str] = None,
        overwrite: bool = False
    ) -> tuple[bool, str, Optional[Path]]:
        """
        Save a setup to Assetto Corsa.
        
        Returns:
            Tuple of (success, message, file_path)
        """
        if not self.is_connected():
            return False, "Not connected to Assetto Corsa", None
        
        status = self.get_status()
        if not status.can_write:
            return False, "Cannot write to setups directory", None
        
        return self.writer.write_setup(
            setup=setup,
            car_id=car_id,
            track_id=track_id,
            filename=filename,
            overwrite=overwrite
        )
    
    def load_setup(self, file_path: Path) -> Optional[Setup]:
        """Load a setup from file."""
        return self.writer.read_setup(file_path)
    
    def list_setups(self, car_id: str, track_id: str) -> list[dict]:
        """List existing setups for a car/track combination."""
        if not self.is_connected():
            return []
        return self.writer.list_setups(car_id, track_id)
    
    def delete_setup(self, file_path: Path) -> tuple[bool, str]:
        """Delete a setup file."""
        return self.writer.delete_setup(file_path)
    
    def backup_setup(self, file_path: Path) -> tuple[bool, str, Optional[Path]]:
        """Create a backup of a setup file."""
        return self.writer.backup_setup(file_path)
    
    def validate_car_track(self, car_id: str, track_id: str) -> tuple[bool, str]:
        """
        Validate that a car/track combination is valid.
        
        Returns:
            Tuple of (valid, message)
        """
        car = self.get_car(car_id)
        if not car:
            return False, f"Car not found: {car_id}"
        
        # Parse track_id for config
        if "/" in track_id:
            track_base, config = track_id.split("/", 1)
        else:
            track_base, config = track_id, ""
        
        track = self.get_track(track_base, config)
        if not track:
            return False, f"Track not found: {track_id}"
        
        return True, f"Valid: {car.name} on {track.name}"
    
    def get_setup_directory(self, car_id: str, track_id: str) -> Optional[Path]:
        """Get the setup directory for a car/track combination."""
        return self.detector.get_setup_path(car_id, track_id)
    
    def ensure_setup_directory(self, car_id: str, track_id: str) -> tuple[bool, str]:
        """
        Ensure the setup directory exists and is writable.
        
        Returns:
            Tuple of (success, message)
        """
        return self.detector.validate_setup_path(car_id, track_id)
    
    def get_cars_by_drivetrain(self, drivetrain: str) -> list[Car]:
        """Get cars filtered by drivetrain type."""
        cars = self.get_cars()
        return [c for c in cars if c.drivetrain == drivetrain]
    
    def get_tracks_by_type(self, track_type: str) -> list[Track]:
        """Get tracks filtered by type."""
        tracks = self.get_tracks()
        return [t for t in tracks if t.track_type == track_type]
    
    def get_touge_tracks(self) -> list[Track]:
        """Get all touge/mountain tracks."""
        return self.get_tracks_by_type("touge")
    
    def get_drift_cars(self) -> list[Car]:
        """Get all drift-suitable cars (RWD)."""
        cars = self.get_cars()
        return [c for c in cars if c.is_drift_car()]
    
    def search_cars(self, query: str) -> list[Car]:
        """Search cars by name or brand."""
        if not query:
            return self.get_cars()
        query = str(query).lower()
        cars = self.get_cars()
        return [
            c for c in cars
            if (c.name and query in c.name.lower()) or 
               (c.brand and query in c.brand.lower()) or 
               (c.car_id and query in c.car_id.lower())
        ]
    
    def search_tracks(self, query: str) -> list[Track]:
        """Search tracks by name."""
        if not query:
            return self.get_tracks()
        query = str(query).lower()
        tracks = self.get_tracks()
        return [
            t for t in tracks
            if (t.name and query in t.name.lower()) or 
               (t.track_id and query in t.track_id.lower())
        ]
    
    def refresh(self) -> ConnectionStatus:
        """Refresh connection and rescan content."""
        self._status = None
        self.detector._cars_cache.clear()
        self.detector._tracks_cache.clear()
        return self.connect()
