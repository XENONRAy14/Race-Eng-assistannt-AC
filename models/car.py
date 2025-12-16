"""
Car model - Represents an Assetto Corsa car.
"""

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class Car:
    """Represents a car in Assetto Corsa."""
    
    # Unique identifier (folder name)
    car_id: str
    
    # Display name
    name: str
    
    # Car brand
    brand: str = ""
    
    # Car class (street, race, drift, etc.)
    car_class: str = "street"
    
    # Drivetrain type (RWD, FWD, AWD)
    drivetrain: str = "RWD"
    
    # Power in HP
    power_hp: int = 0
    
    # Weight in kg
    weight_kg: int = 0
    
    # Path to car folder
    path: Optional[Path] = None
    
    # Available setup sections for this car
    available_sections: list[str] = field(default_factory=lambda: [
        "TYRES", "BRAKES", "SUSPENSION", "DIFFERENTIAL", 
        "ALIGNMENT", "AERO", "FUEL"
    ])
    
    def __post_init__(self):
        """Validate car data after initialization."""
        if not self.car_id:
            raise ValueError("car_id cannot be empty")
        if not self.name:
            self.name = self.car_id
    
    @property
    def power_to_weight(self) -> float:
        """Calculate power to weight ratio (HP/ton)."""
        if self.weight_kg <= 0:
            return 0.0
        return (self.power_hp / self.weight_kg) * 1000
    
    def is_drift_car(self) -> bool:
        """Check if car is suitable for drifting."""
        return self.drivetrain == "RWD" and self.car_class in ["drift", "street"]
    
    def is_high_power(self) -> bool:
        """Check if car has high power output."""
        return self.power_hp >= 300
    
    def to_dict(self) -> dict:
        """Convert car to dictionary."""
        return {
            "car_id": self.car_id,
            "name": self.name,
            "brand": self.brand,
            "car_class": self.car_class,
            "drivetrain": self.drivetrain,
            "power_hp": self.power_hp,
            "weight_kg": self.weight_kg,
            "path": str(self.path) if self.path else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Car":
        """Create car from dictionary."""
        path = Path(data["path"]) if data.get("path") else None
        return cls(
            car_id=data["car_id"],
            name=data.get("name", data["car_id"]),
            brand=data.get("brand", ""),
            car_class=data.get("car_class", "street"),
            drivetrain=data.get("drivetrain", "RWD"),
            power_hp=data.get("power_hp", 0),
            weight_kg=data.get("weight_kg", 0),
            path=path
        )
