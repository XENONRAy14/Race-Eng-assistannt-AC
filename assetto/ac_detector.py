"""
AC Detector - Detects Assetto Corsa installation and content.
Scans for cars, tracks, and validates paths.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import configparser

from models.car import Car
from models.track import Track


@dataclass
class ACInstallation:
    """Represents an Assetto Corsa installation."""
    
    documents_path: Optional[Path] = None
    game_path: Optional[Path] = None
    
    # Derived paths
    setups_path: Optional[Path] = None
    cars_path: Optional[Path] = None
    tracks_path: Optional[Path] = None
    
    # Status
    is_valid: bool = False
    can_write_setups: bool = False
    
    def __post_init__(self):
        """Calculate derived paths."""
        if self.documents_path:
            self.setups_path = self.documents_path / "setups"
            
        if self.game_path:
            self.cars_path = self.game_path / "content" / "cars"
            self.tracks_path = self.game_path / "content" / "tracks"


class ACDetector:
    """
    Detects and validates Assetto Corsa installation.
    Provides access to cars, tracks, and setup directories.
    """
    
    # Common AC installation paths
    COMMON_GAME_PATHS = [
        Path("C:/Program Files (x86)/Steam/steamapps/common/assettocorsa"),
        Path("C:/Program Files/Steam/steamapps/common/assettocorsa"),
        Path("D:/Steam/steamapps/common/assettocorsa"),
        Path("D:/Games/Steam/steamapps/common/assettocorsa"),
        Path("E:/Steam/steamapps/common/assettocorsa"),
        Path("D:/SteamLibrary/steamapps/common/assettocorsa"),
        Path("E:/SteamLibrary/steamapps/common/assettocorsa"),
        Path("F:/SteamLibrary/steamapps/common/assettocorsa"),
        Path("G:/SteamLibrary/steamapps/common/assettocorsa"),
    ]
    
    def __init__(self):
        """Initialize detector."""
        self._installation: Optional[ACInstallation] = None
        self._cars_cache: dict[str, Car] = {}
        self._tracks_cache: dict[str, Track] = {}
    
    def detect_ac_documents_path(self) -> Optional[Path]:
        """
        Detect the Assetto Corsa Documents folder.
        Returns the path if found, None otherwise.
        """
        # Standard Windows Documents path
        documents = Path.home() / "Documents" / "Assetto Corsa"
        
        if documents.exists():
            return documents
        
        # Try OneDrive Documents
        onedrive_docs = Path.home() / "OneDrive" / "Documents" / "Assetto Corsa"
        if onedrive_docs.exists():
            return onedrive_docs
        
        # Try environment variable
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            alt_docs = Path(user_profile) / "Documents" / "Assetto Corsa"
            if alt_docs.exists():
                return alt_docs
        
        return None
    
    def detect_ac_game_path(self) -> Optional[Path]:
        """
        Detect the Assetto Corsa game installation folder.
        Returns the path if found, None otherwise.
        """
        for path in self.COMMON_GAME_PATHS:
            if path.exists() and (path / "AssettoCorsa.exe").exists():
                return path
        
        # Try to find via Steam library folders
        steam_path = self._find_steam_library_path()
        if steam_path:
            ac_path = steam_path / "steamapps" / "common" / "assettocorsa"
            if ac_path.exists():
                return ac_path
        
        return None
    
    def _find_steam_library_path(self) -> Optional[Path]:
        """Try to find Steam library path from registry or common locations."""
        # Check common Steam paths
        common_steam = [
            Path("C:/Program Files (x86)/Steam"),
            Path("C:/Program Files/Steam"),
            Path("D:/Steam"),
            Path("E:/Steam"),
        ]
        
        for path in common_steam:
            if path.exists() and (path / "steam.exe").exists():
                return path
        
        return None
    
    def detect_installation(self) -> ACInstallation:
        """
        Detect full Assetto Corsa installation.
        Returns an ACInstallation object with all paths.
        If an installation was already set (e.g. from saved settings), use that.
        """
        # If already configured (from saved settings), return it
        if self._installation is not None and self._installation.is_valid:
            return self._installation
        
        docs_path = self.detect_ac_documents_path()
        game_path = self.detect_ac_game_path()
        
        installation = ACInstallation(
            documents_path=docs_path,
            game_path=game_path
        )
        
        # Validate installation - BOTH documents AND game path must exist
        if docs_path and docs_path.exists() and game_path and game_path.exists():
            installation.is_valid = True
            
            # Check write permissions
            setups_path = docs_path / "setups"
            try:
                setups_path.mkdir(parents=True, exist_ok=True)
                test_file = setups_path / ".write_test"
                test_file.touch()
                test_file.unlink()
                installation.can_write_setups = True
            except (PermissionError, OSError):
                installation.can_write_setups = False
        
        self._installation = installation
        return installation
    
    def get_installation(self) -> Optional[ACInstallation]:
        """Get cached installation or detect if not cached."""
        if self._installation is None:
            self.detect_installation()
        return self._installation
    
    def scan_cars(self, force_refresh: bool = False) -> list[Car]:
        """
        Scan for available cars.
        Returns list of Car objects.
        """
        if self._cars_cache and not force_refresh:
            return list(self._cars_cache.values())
        
        self._cars_cache.clear()
        installation = self.get_installation()
        
        if not installation or not installation.cars_path:
            return []
        
        cars_path = installation.cars_path
        if not cars_path.exists():
            return []
        
        for car_dir in cars_path.iterdir():
            if not car_dir.is_dir():
                continue
            
            car = self._parse_car(car_dir)
            if car:
                self._cars_cache[car.car_id] = car
        
        return list(self._cars_cache.values())
    
    def _parse_car(self, car_dir: Path) -> Optional[Car]:
        """Parse a car directory and return a Car object."""
        car_id = car_dir.name
        
        # Try to read ui_car.json or car.ini for metadata
        ui_json = car_dir / "ui" / "ui_car.json"
        car_ini = car_dir / "data" / "car.ini"
        
        name = car_id
        brand = ""
        car_class = "street"
        drivetrain = "RWD"
        power_hp = 0
        weight_kg = 0
        
        # Try to parse ui_car.json
        if ui_json.exists():
            try:
                import json
                with open(ui_json, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
                    name = data.get("name", car_id)
                    brand = data.get("brand", "")
                    car_class = data.get("class", "street")
                    
                    # Parse specs
                    specs = data.get("specs", {})
                    if "bhp" in specs:
                        try:
                            power_hp = int(specs["bhp"].replace(" bhp", "").replace(",", ""))
                        except (ValueError, AttributeError):
                            pass
                    if "weight" in specs:
                        try:
                            weight_kg = int(specs["weight"].replace(" kg", "").replace(",", ""))
                        except (ValueError, AttributeError):
                            pass
                    if "drivetrain" in specs:
                        drivetrain = specs["drivetrain"]
            except (json.JSONDecodeError, IOError):
                pass
        
        # Try to parse drivetrain.ini for drivetrain info
        drivetrain_ini = car_dir / "data" / "drivetrain.ini"
        if drivetrain_ini.exists():
            try:
                config = configparser.ConfigParser()
                config.read(drivetrain_ini, encoding="utf-8")
                if config.has_option("TRACTION", "TYPE"):
                    dt_type = config.get("TRACTION", "TYPE")
                    if dt_type == "RWD":
                        drivetrain = "RWD"
                    elif dt_type == "FWD":
                        drivetrain = "FWD"
                    elif dt_type == "AWD":
                        drivetrain = "AWD"
            except (configparser.Error, IOError):
                pass
        
        return Car(
            car_id=car_id,
            name=name,
            brand=brand,
            car_class=car_class,
            drivetrain=drivetrain,
            power_hp=power_hp,
            weight_kg=weight_kg,
            path=car_dir
        )
    
    def scan_tracks(self, force_refresh: bool = False) -> list[Track]:
        """
        Scan for available tracks.
        Returns list of Track objects.
        """
        if self._tracks_cache and not force_refresh:
            return list(self._tracks_cache.values())
        
        self._tracks_cache.clear()
        installation = self.get_installation()
        
        if not installation or not installation.tracks_path:
            return []
        
        tracks_path = installation.tracks_path
        if not tracks_path.exists():
            return []
        
        for track_dir in tracks_path.iterdir():
            if not track_dir.is_dir():
                continue
            
            # Check for track configurations
            ui_dir = track_dir / "ui"
            if not ui_dir.exists():
                continue
            
            # Check for multiple layouts
            layouts = []
            for item in ui_dir.iterdir():
                if item.is_dir() and (item / "ui_track.json").exists():
                    layouts.append(item.name)
            
            if layouts:
                # Multiple layouts
                for layout in layouts:
                    track = self._parse_track(track_dir, layout)
                    if track:
                        self._tracks_cache[track.full_id] = track
            else:
                # Single layout
                track = self._parse_track(track_dir, "")
                if track:
                    self._tracks_cache[track.full_id] = track
        
        return list(self._tracks_cache.values())
    
    def _parse_track(self, track_dir: Path, config: str) -> Optional[Track]:
        """Parse a track directory and return a Track object."""
        track_id = track_dir.name
        
        # Determine UI path
        if config:
            ui_json = track_dir / "ui" / config / "ui_track.json"
        else:
            ui_json = track_dir / "ui" / "ui_track.json"
        
        name = track_id
        length_m = 0
        track_type = "touge"  # Default to touge for this application
        
        if ui_json.exists():
            try:
                import json
                with open(ui_json, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
                    name = data.get("name", track_id)
                    
                    # Parse length
                    length_str = data.get("length", "0")
                    try:
                        # Handle formats like "5.2 km" or "5200 m"
                        length_str = length_str.lower().replace(",", "")
                        if "km" in length_str:
                            length_m = int(float(length_str.replace("km", "").strip()) * 1000)
                        elif "m" in length_str:
                            length_m = int(float(length_str.replace("m", "").strip()))
                        else:
                            length_m = int(float(length_str))
                    except (ValueError, AttributeError):
                        pass
                    
                    # Detect track type from tags or name
                    tags = data.get("tags", [])
                    description = data.get("description", "").lower()
                    
                    if any(t.lower() in ["touge", "mountain", "hill"] for t in tags):
                        track_type = "touge"
                    elif any(t.lower() in ["drift"] for t in tags):
                        track_type = "drift"
                    elif any(t.lower() in ["circuit", "race"] for t in tags):
                        track_type = "circuit"
                    elif "touge" in description or "mountain" in description:
                        track_type = "touge"
            except (json.JSONDecodeError, IOError):
                pass
        
        return Track(
            track_id=track_id,
            name=name,
            config=config,
            length_m=length_m,
            track_type=track_type,
            path=track_dir
        )
    
    def get_car(self, car_id: str) -> Optional[Car]:
        """Get a specific car by ID."""
        if not self._cars_cache:
            self.scan_cars()
        return self._cars_cache.get(car_id)
    
    def get_track(self, track_id: str, config: str = "") -> Optional[Track]:
        """Get a specific track by ID and optional config."""
        if not self._tracks_cache:
            self.scan_tracks()
        
        full_id = f"{track_id}/{config}" if config else track_id
        return self._tracks_cache.get(full_id)
    
    def get_setup_path(self, car_id: str, track_id: str) -> Optional[Path]:
        """Get the setup directory path for a car/track combination."""
        installation = self.get_installation()
        if not installation or not installation.setups_path:
            return None
        
        return installation.setups_path / car_id / track_id
    
    def validate_setup_path(self, car_id: str, track_id: str) -> tuple[bool, str]:
        """
        Validate that we can write setups for the given car/track.
        Returns (success, message).
        """
        installation = self.get_installation()
        
        if not installation:
            return False, "Assetto Corsa installation not detected"
        
        if not installation.is_valid:
            return False, "Invalid Assetto Corsa installation"
        
        if not installation.can_write_setups:
            return False, "Cannot write to setups directory (permission denied)"
        
        setup_path = self.get_setup_path(car_id, track_id)
        if not setup_path:
            return False, "Could not determine setup path"
        
        try:
            setup_path.mkdir(parents=True, exist_ok=True)
            return True, f"Setup path ready: {setup_path}"
        except (PermissionError, OSError) as e:
            return False, f"Cannot create setup directory: {e}"
