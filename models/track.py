"""
Track model - Represents an Assetto Corsa track.
"""

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class Track:
    """Represents a track in Assetto Corsa."""
    
    # Unique identifier (folder name)
    track_id: str
    
    # Display name
    name: str
    
    # Track configuration (layout variant)
    config: str = ""
    
    # Track length in meters
    length_m: int = 0
    
    # Track type (circuit, touge, street, drift)
    track_type: str = "touge"
    
    # Number of corners
    corners: int = 0
    
    # Elevation change in meters
    elevation_change_m: int = 0
    
    # Average corner speed (low, medium, high)
    corner_speed: str = "medium"
    
    # Surface grip level (0.0 to 1.0)
    grip_level: float = 0.95
    
    # Path to track folder
    path: Optional[Path] = None
    
    # Track characteristics for AI
    characteristics: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate track data after initialization."""
        if not self.track_id:
            raise ValueError("track_id cannot be empty")
        if not self.name:
            self.name = self.track_id
        
        # Set default characteristics for touge
        if not self.characteristics:
            self.characteristics = self._default_touge_characteristics()
    
    def _default_touge_characteristics(self) -> dict:
        """Default characteristics for touge tracks."""
        return {
            "requires_stability": True,
            "requires_rotation": True,
            "tight_corners": True,
            "elevation_changes": True,
            "grip_priority": 0.7,
            "rotation_priority": 0.6,
            "stability_priority": 0.8
        }
    
    @property
    def full_id(self) -> str:
        """Get full track ID including config."""
        if self.config:
            return f"{self.track_id}/{self.config}"
        return self.track_id
    
    def is_touge(self) -> bool:
        """Check if track is a touge/mountain road."""
        return self.track_type == "touge"
    
    def is_technical(self) -> bool:
        """Check if track is technical (many tight corners)."""
        if self.length_m <= 0:
            return True  # Assume technical for unknown tracks
        corners_per_km = (self.corners / self.length_m) * 1000
        return corners_per_km > 15
    
    def has_elevation(self) -> bool:
        """Check if track has significant elevation changes."""
        return self.elevation_change_m > 50
    
    def to_dict(self) -> dict:
        """Convert track to dictionary."""
        return {
            "track_id": self.track_id,
            "name": self.name,
            "config": self.config,
            "length_m": self.length_m,
            "track_type": self.track_type,
            "corners": self.corners,
            "elevation_change_m": self.elevation_change_m,
            "corner_speed": self.corner_speed,
            "grip_level": self.grip_level,
            "path": str(self.path) if self.path else None,
            "characteristics": self.characteristics
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Track":
        """Create track from dictionary."""
        path = Path(data["path"]) if data.get("path") else None
        return cls(
            track_id=data["track_id"],
            name=data.get("name", data["track_id"]),
            config=data.get("config", ""),
            length_m=data.get("length_m", 0),
            track_type=data.get("track_type", "touge"),
            corners=data.get("corners", 0),
            elevation_change_m=data.get("elevation_change_m", 0),
            corner_speed=data.get("corner_speed", "medium"),
            grip_level=data.get("grip_level", 0.95),
            path=path,
            characteristics=data.get("characteristics", {})
        )
