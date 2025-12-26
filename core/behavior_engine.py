"""
Behavior Engine - Defines and manages driving behaviors/presets.
Each behavior represents a complete setup philosophy for touge driving.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class BehaviorType(Enum):
    """Available behavior types for touge driving."""
    SAFE = "safe"
    BALANCED = "balanced"
    ATTACK = "attack"
    DRIFT = "drift"


@dataclass
class Behavior:
    """
    Represents a driving behavior with associated setup modifiers.
    All modifiers are relative adjustments (-1.0 to +1.0 range).
    """
    
    # Behavior identification
    behavior_id: str
    name: str
    description: str
    
    # Suspension modifiers
    suspension_stiffness: float = 0.0  # -1 = softer, +1 = stiffer
    suspension_damping: float = 0.0
    ride_height: float = 0.0  # -1 = lower, +1 = higher
    
    # Anti-roll bar modifiers
    arb_front: float = 0.0
    arb_rear: float = 0.0
    
    # Differential modifiers
    diff_power: float = 0.0  # -1 = less locking, +1 = more locking
    diff_coast: float = 0.0
    diff_preload: float = 0.0
    
    # Alignment modifiers
    camber_front: float = 0.0  # -1 = less negative, +1 = more negative
    camber_rear: float = 0.0
    toe_front: float = 0.0
    toe_rear: float = 0.0
    
    # Brake modifiers
    brake_bias: float = 0.0  # -1 = more rear, +1 = more front
    brake_power: float = 0.0
    
    # Tyre pressure modifiers
    tyre_pressure: float = 0.0  # -1 = lower, +1 = higher
    
    # Priority weights for AI scoring
    priorities: dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set default priorities if not provided."""
        if not self.priorities:
            self.priorities = {
                "stability": 0.5,
                "rotation": 0.5,
                "grip": 0.5,
                "predictability": 0.5
            }
    
    def get_modifier(self, name: str) -> float:
        """Get a modifier value by name."""
        return getattr(self, name, 0.0)
    
    def to_dict(self) -> dict:
        """Convert behavior to dictionary."""
        return {
            "behavior_id": self.behavior_id,
            "name": self.name,
            "description": self.description,
            "suspension_stiffness": self.suspension_stiffness,
            "suspension_damping": self.suspension_damping,
            "ride_height": self.ride_height,
            "arb_front": self.arb_front,
            "arb_rear": self.arb_rear,
            "diff_power": self.diff_power,
            "diff_coast": self.diff_coast,
            "diff_preload": self.diff_preload,
            "camber_front": self.camber_front,
            "camber_rear": self.camber_rear,
            "toe_front": self.toe_front,
            "toe_rear": self.toe_rear,
            "brake_bias": self.brake_bias,
            "brake_power": self.brake_power,
            "tyre_pressure": self.tyre_pressure,
            "priorities": self.priorities
        }


class BehaviorEngine:
    """
    Engine for managing and applying driving behaviors.
    Provides predefined touge behaviors and custom behavior creation.
    """
    
    def __init__(self):
        """Initialize with predefined behaviors."""
        self._behaviors: dict[str, Behavior] = {}
        self._initialize_default_behaviors()
    
    def _initialize_default_behaviors(self) -> None:
        """Create the four main touge behaviors."""
        
        # SAFE TOUGE - Maximum stability and predictability
        self._behaviors["safe"] = Behavior(
            behavior_id="safe",
            name="Safe Touge",
            description="Maximum stability and predictability. Forgiving setup for learning or relaxed driving.",
            suspension_stiffness=-0.6,  # Much softer suspension (2x)
            suspension_damping=-0.5,  # Softer damping (2.5x)
            ride_height=0.3,  # Higher for bumps (3x)
            arb_front=-0.5,  # Much softer ARBs (2.5x)
            arb_rear=-0.6,  # Very soft rear (2x)
            diff_power=-0.7,  # Much less aggressive diff (1.75x)
            diff_coast=-0.6,  # Less coast locking (2x)
            diff_preload=-0.5,  # Less preload (2.5x)
            camber_front=-0.4,  # Less aggressive camber (2x)
            camber_rear=-0.4,  # Less rear camber (2x)
            toe_front=0.2,  # More toe-in for stability (2x)
            toe_rear=0.4,  # Significant toe-in rear (2x)
            brake_bias=0.2,  # More front bias (2x)
            brake_power=-0.2,  # Less brake power (2x)
            tyre_pressure=-0.3,  # Lower for more grip (3x)
            priorities={
                "stability": 0.9,
                "rotation": 0.2,
                "grip": 0.7,
                "predictability": 0.95
            }
        )
        
        # BALANCED TOUGE - Good all-around setup
        self._behaviors["balanced"] = Behavior(
            behavior_id="balanced",
            name="Balanced Touge",
            description="Well-rounded setup balancing grip, rotation, and stability.",
            suspension_stiffness=0.0,
            suspension_damping=0.0,
            ride_height=0.0,
            arb_front=0.0,
            arb_rear=0.0,
            diff_power=0.0,
            diff_coast=0.0,
            diff_preload=0.0,
            camber_front=0.0,
            camber_rear=0.0,
            toe_front=0.0,
            toe_rear=0.1,
            brake_bias=0.0,
            brake_power=0.0,
            tyre_pressure=0.0,
            priorities={
                "stability": 0.6,
                "rotation": 0.5,
                "grip": 0.6,
                "predictability": 0.6
            }
        )
        
        # ATTACK TOUGE - Aggressive grip-focused setup
        self._behaviors["attack"] = Behavior(
            behavior_id="attack",
            name="Attack Touge",
            description="Aggressive setup for maximum speed. Sharp turn-in, high grip limits.",
            suspension_stiffness=0.7,  # Much stiffer suspension (2.3x)
            suspension_damping=0.5,  # Stiffer damping (2.5x)
            ride_height=-0.5,  # Much lower for aero/CG (2.5x)
            arb_front=0.6,  # Much stiffer front ARB (3x)
            arb_rear=0.3,  # Stiffer rear (3x)
            diff_power=0.7,  # Very aggressive diff (2.3x)
            diff_coast=0.5,  # More coast locking (2.5x)
            diff_preload=0.5,  # More preload (2.5x)
            camber_front=0.7,  # Much more negative camber (2.3x)
            camber_rear=0.5,  # More rear camber (2.5x)
            toe_front=-0.3,  # More toe-out for sharp turn-in (3x)
            toe_rear=0.2,  # Slight toe-in rear (2x)
            brake_bias=0.0,  # Neutral
            brake_power=0.3,  # More brake power (3x)
            tyre_pressure=0.3,  # Higher for response (3x)
            priorities={
                "stability": 0.4,
                "rotation": 0.7,
                "grip": 0.9,
                "predictability": 0.4
            }
        )
        
        # DRIFT TOUGE - Setup optimized for controlled sliding
        self._behaviors["drift"] = Behavior(
            behavior_id="drift",
            name="Drift Touge",
            description="Setup for controlled drifting. Easy to initiate and maintain slides.",
            suspension_stiffness=0.3,  # Stiffer for response (3x)
            suspension_damping=0.3,  # Stiffer damping (3x)
            ride_height=0.1,  # Slightly higher (from 0)
            arb_front=0.7,  # Much stiffer front for oversteer (2.3x)
            arb_rear=-0.5,  # Much softer rear (2.5x)
            diff_power=1.0,  # Maximum locking for drift (1.67x)
            diff_coast=0.8,  # Very locked coast (2x)
            diff_preload=0.7,  # High preload (2.3x)
            camber_front=0.3,  # More front camber (3x)
            camber_rear=-0.6,  # Much less rear camber for sliding (2x)
            toe_front=-0.3,  # More toe-out front (3x)
            toe_rear=-0.3,  # Significant toe-out rear for instability (3x)
            brake_bias=-0.5,  # Much more rear bias for rotation (2.5x)
            brake_power=0.0,  # Neutral
            tyre_pressure=0.5,  # Much higher rear pressure (2.5x)
            priorities={
                "stability": 0.3,
                "rotation": 0.9,
                "grip": 0.4,
                "predictability": 0.5
            }
        )
    
    def get_behavior(self, behavior_id: str) -> Optional[Behavior]:
        """Get a behavior by ID."""
        return self._behaviors.get(behavior_id)
    
    def get_all_behaviors(self) -> list[Behavior]:
        """Get all available behaviors."""
        return list(self._behaviors.values())
    
    def get_behavior_names(self) -> list[str]:
        """Get list of behavior IDs."""
        return list(self._behaviors.keys())
    
    def add_custom_behavior(self, behavior: Behavior) -> None:
        """Add a custom behavior."""
        self._behaviors[behavior.behavior_id] = behavior
    
    def interpolate_behaviors(
        self, 
        behavior1_id: str, 
        behavior2_id: str, 
        factor: float
    ) -> Optional[Behavior]:
        """
        Create a new behavior by interpolating between two behaviors.
        Factor 0.0 = behavior1, 1.0 = behavior2.
        """
        b1 = self.get_behavior(behavior1_id)
        b2 = self.get_behavior(behavior2_id)
        
        if not b1 or not b2:
            return None
        
        factor = max(0.0, min(1.0, factor))
        
        def lerp(a: float, b: float) -> float:
            return a + (b - a) * factor
        
        return Behavior(
            behavior_id=f"{behavior1_id}_{behavior2_id}_blend",
            name=f"{b1.name} / {b2.name} Blend",
            description=f"Interpolated behavior ({factor:.0%} towards {b2.name})",
            suspension_stiffness=lerp(b1.suspension_stiffness, b2.suspension_stiffness),
            suspension_damping=lerp(b1.suspension_damping, b2.suspension_damping),
            ride_height=lerp(b1.ride_height, b2.ride_height),
            arb_front=lerp(b1.arb_front, b2.arb_front),
            arb_rear=lerp(b1.arb_rear, b2.arb_rear),
            diff_power=lerp(b1.diff_power, b2.diff_power),
            diff_coast=lerp(b1.diff_coast, b2.diff_coast),
            diff_preload=lerp(b1.diff_preload, b2.diff_preload),
            camber_front=lerp(b1.camber_front, b2.camber_front),
            camber_rear=lerp(b1.camber_rear, b2.camber_rear),
            toe_front=lerp(b1.toe_front, b2.toe_front),
            toe_rear=lerp(b1.toe_rear, b2.toe_rear),
            brake_bias=lerp(b1.brake_bias, b2.brake_bias),
            brake_power=lerp(b1.brake_power, b2.brake_power),
            tyre_pressure=lerp(b1.tyre_pressure, b2.tyre_pressure),
            priorities={
                k: lerp(b1.priorities.get(k, 0.5), b2.priorities.get(k, 0.5))
                for k in set(b1.priorities.keys()) | set(b2.priorities.keys())
            }
        )
    
    def get_recommended_behavior(
        self, 
        stability_factor: float, 
        aggression_factor: float,
        drift_factor: float
    ) -> str:
        """
        Recommend a behavior based on driver preferences.
        All factors are 0.0 to 1.0.
        """
        # High drift preference
        if drift_factor > 0.6:
            return "drift"
        
        # High aggression + low stability = attack
        if aggression_factor > 0.6 and stability_factor < 0.5:
            return "attack"
        
        # High stability + low aggression = safe
        if stability_factor > 0.6 and aggression_factor < 0.4:
            return "safe"
        
        # Default to balanced
        return "balanced"
