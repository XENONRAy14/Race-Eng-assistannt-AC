"""
Driver Profile model - Represents driver preferences and style.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class DriverProfile:
    """
    Represents a driver's preferences and driving style.
    All slider values are normalized between 0 and 100.
    """
    
    # Profile identification
    profile_id: Optional[int] = None
    name: str = "Default Driver"
    
    # Core driving style sliders (0-100)
    # 0 = left preference, 100 = right preference
    
    # Stability (0) ↔ Rotation (100)
    # Low = stable, predictable | High = agile, rotational
    stability_rotation: float = 50.0
    
    # Grip (0) ↔ Slide (100)
    # Low = maximum grip | High = allows sliding
    grip_slide: float = 30.0
    
    # Safety (0) ↔ Aggression (100)
    # Low = safe, forgiving | High = aggressive, on the limit
    safety_aggression: float = 40.0
    
    # Drift (0) ↔ Grip (100)
    # Low = drift-oriented | High = grip-oriented
    drift_grip: float = 70.0
    
    # Comfort (0) ↔ Performance (100)
    # Low = comfortable, smooth | High = stiff, responsive
    comfort_performance: float = 50.0
    
    # Additional preferences
    preferred_behavior: str = "balanced"
    experience_level: str = "intermediate"  # beginner, intermediate, advanced, expert
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate and clamp slider values."""
        self._clamp_sliders()
    
    def _clamp_sliders(self) -> None:
        """Ensure all slider values are within 0-100 range."""
        self.stability_rotation = max(0.0, min(100.0, self.stability_rotation))
        self.grip_slide = max(0.0, min(100.0, self.grip_slide))
        self.safety_aggression = max(0.0, min(100.0, self.safety_aggression))
        self.drift_grip = max(0.0, min(100.0, self.drift_grip))
        self.comfort_performance = max(0.0, min(100.0, self.comfort_performance))
    
    # Computed properties for AI decision engine
    
    @property
    def wants_stability(self) -> bool:
        """Driver prefers stability over rotation."""
        return self.stability_rotation < 50
    
    @property
    def stability_factor(self) -> float:
        """Stability preference as 0-1 factor (1 = max stability)."""
        return 1.0 - (self.stability_rotation / 100.0)
    
    @property
    def rotation_factor(self) -> float:
        """Rotation preference as 0-1 factor (1 = max rotation)."""
        return self.stability_rotation / 100.0
    
    @property
    def wants_grip(self) -> bool:
        """Driver prefers grip over sliding."""
        return self.grip_slide < 50
    
    @property
    def grip_factor(self) -> float:
        """Grip preference as 0-1 factor (1 = max grip)."""
        return 1.0 - (self.grip_slide / 100.0)
    
    @property
    def slide_factor(self) -> float:
        """Slide preference as 0-1 factor (1 = max slide)."""
        return self.grip_slide / 100.0
    
    @property
    def is_aggressive(self) -> bool:
        """Driver has aggressive driving style."""
        return self.safety_aggression > 60
    
    @property
    def aggression_factor(self) -> float:
        """Aggression as 0-1 factor (1 = max aggression)."""
        return self.safety_aggression / 100.0
    
    @property
    def safety_factor(self) -> float:
        """Safety preference as 0-1 factor (1 = max safety)."""
        return 1.0 - (self.safety_aggression / 100.0)
    
    @property
    def prefers_drift(self) -> bool:
        """Driver prefers drift-oriented setup."""
        return self.drift_grip < 50
    
    @property
    def drift_factor(self) -> float:
        """Drift preference as 0-1 factor (1 = max drift)."""
        return 1.0 - (self.drift_grip / 100.0)
    
    @property
    def prefers_performance(self) -> bool:
        """Driver prefers performance over comfort."""
        return self.comfort_performance > 50
    
    @property
    def performance_factor(self) -> float:
        """Performance preference as 0-1 factor (1 = max performance)."""
        return self.comfort_performance / 100.0
    
    @property
    def comfort_factor(self) -> float:
        """Comfort preference as 0-1 factor (1 = max comfort)."""
        return 1.0 - (self.comfort_performance / 100.0)
    
    def get_experience_multiplier(self) -> float:
        """Get multiplier based on experience level."""
        multipliers = {
            "beginner": 0.6,
            "intermediate": 0.8,
            "advanced": 1.0,
            "expert": 1.2
        }
        return multipliers.get(self.experience_level, 0.8)
    
    def get_all_factors(self) -> dict[str, float]:
        """Get all preference factors as a dictionary."""
        return {
            "stability": self.stability_factor,
            "rotation": self.rotation_factor,
            "grip": self.grip_factor,
            "slide": self.slide_factor,
            "safety": self.safety_factor,
            "aggression": self.aggression_factor,
            "drift": self.drift_factor,
            "performance": self.performance_factor,
            "comfort": self.comfort_factor,
            "experience": self.get_experience_multiplier()
        }
    
    def to_dict(self) -> dict:
        """Convert profile to dictionary for storage."""
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "stability_rotation": self.stability_rotation,
            "grip_slide": self.grip_slide,
            "safety_aggression": self.safety_aggression,
            "drift_grip": self.drift_grip,
            "comfort_performance": self.comfort_performance,
            "preferred_behavior": self.preferred_behavior,
            "experience_level": self.experience_level,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DriverProfile":
        """Create profile from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
        
        last_used = data.get("last_used")
        if isinstance(last_used, str):
            last_used = datetime.fromisoformat(last_used)
        elif last_used is None:
            last_used = datetime.now()
        
        return cls(
            profile_id=data.get("profile_id"),
            name=data.get("name", "Default Driver"),
            stability_rotation=data.get("stability_rotation", 50.0),
            grip_slide=data.get("grip_slide", 30.0),
            safety_aggression=data.get("safety_aggression", 40.0),
            drift_grip=data.get("drift_grip", 70.0),
            comfort_performance=data.get("comfort_performance", 50.0),
            preferred_behavior=data.get("preferred_behavior", "balanced"),
            experience_level=data.get("experience_level", "intermediate"),
            created_at=created_at,
            last_used=last_used
        )
    
    @classmethod
    def create_preset(cls, preset_name: str) -> "DriverProfile":
        """Create a preset driver profile."""
        presets = {
            "safe_touge": cls(
                name="Safe Touge",
                stability_rotation=25.0,
                grip_slide=20.0,
                safety_aggression=20.0,
                drift_grip=80.0,
                comfort_performance=40.0,
                preferred_behavior="safe"
            ),
            "balanced_touge": cls(
                name="Balanced Touge",
                stability_rotation=50.0,
                grip_slide=40.0,
                safety_aggression=50.0,
                drift_grip=60.0,
                comfort_performance=50.0,
                preferred_behavior="balanced"
            ),
            "attack_touge": cls(
                name="Attack Touge",
                stability_rotation=70.0,
                grip_slide=50.0,
                safety_aggression=75.0,
                drift_grip=55.0,
                comfort_performance=70.0,
                preferred_behavior="attack"
            ),
            "drift_touge": cls(
                name="Drift Touge",
                stability_rotation=80.0,
                grip_slide=85.0,
                safety_aggression=60.0,
                drift_grip=15.0,
                comfort_performance=55.0,
                preferred_behavior="drift"
            )
        }
        return presets.get(preset_name, cls())
