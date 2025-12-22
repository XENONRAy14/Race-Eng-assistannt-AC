"""
Setup Engine - Generates complete car setups.
Combines behavior modifiers, rule adjustments, and base values.
"""

from typing import Optional
from pathlib import Path
import configparser
from models.setup import Setup, SetupSection
from models.driver_profile import DriverProfile
from models.car import Car
from models.track import Track
from core.behavior_engine import BehaviorEngine, Behavior
from core.rules_engine import RulesEngine
from core.scoring_engine import ScoringEngine, ScoreBreakdown


class SetupEngine:
    """
    Main engine for generating car setups.
    Orchestrates behavior, rules, and scoring engines.
    """
    
    # Base setup values (neutral starting point)
    BASE_VALUES = {
        "TYRES": {
            "PRESSURE_LF": 26.0,
            "PRESSURE_RF": 26.0,
            "PRESSURE_LR": 26.0,
            "PRESSURE_RR": 26.0,
            "COMPOUND": 2  # 0=soft, 1=medium, 2=hard (index varies by car)
        },
        "BRAKES": {
            "BIAS": 58.0,
            "FRONT_BIAS": 58.0,
            "BRAKE_POWER_MULT": 1.0
        },
        "SUSPENSION": {
            "SPRING_RATE_LF": 80000,
            "SPRING_RATE_RF": 80000,
            "SPRING_RATE_LR": 70000,
            "SPRING_RATE_RR": 70000,
            "DAMP_BUMP_LF": 3000,
            "DAMP_BUMP_RF": 3000,
            "DAMP_BUMP_LR": 2800,
            "DAMP_BUMP_RR": 2800,
            "DAMP_REBOUND_LF": 5000,
            "DAMP_REBOUND_RF": 5000,
            "DAMP_REBOUND_LR": 4500,
            "DAMP_REBOUND_RR": 4500,
            "DAMP_FAST_BUMP_LF": 2000,
            "DAMP_FAST_BUMP_RF": 2000,
            "DAMP_FAST_BUMP_LR": 1800,
            "DAMP_FAST_BUMP_RR": 1800,
            "DAMP_FAST_REBOUND_LF": 3500,
            "DAMP_FAST_REBOUND_RF": 3500,
            "DAMP_FAST_REBOUND_LR": 3200,
            "DAMP_FAST_REBOUND_RR": 3200,
            "RIDE_HEIGHT_LF": 50,
            "RIDE_HEIGHT_RF": 50,
            "RIDE_HEIGHT_LR": 55,
            "RIDE_HEIGHT_RR": 55,
            "PACKER_LF": 0,
            "PACKER_RF": 0,
            "PACKER_LR": 0,
            "PACKER_RR": 0
        },
        "DIFFERENTIAL": {
            "POWER": 45.0,
            "COAST": 35.0,
            "PRELOAD": 25.0
        },
        "ALIGNMENT": {
            "CAMBER_LF": -3.0,
            "CAMBER_RF": -3.0,
            "CAMBER_LR": -2.0,
            "CAMBER_RR": -2.0,
            "TOE_LF": 0.0,
            "TOE_RF": 0.0,
            "TOE_LR": 0.1,
            "TOE_RR": 0.1,
            "CASTER_LF": 0.0,
            "CASTER_RF": 0.0
        },
        "AERO": {
            "WING_FRONT": 0,
            "WING_REAR": 0,
            "SPLITTER": 0,
            "REAR_WING": 0
        },
        "FUEL": {
            "FUEL": 30
        },
        "ARB": {
            "FRONT": 5,
            "REAR": 4
        },
        "ELECTRONICS": {
            "TC": 5,           # Traction Control (0-12 typically)
            "ABS": 3,          # ABS level (0-12 typically)
            "ENGINE_MAP": 1,   # Engine map (power mode)
            "MGU_K_DELIVERY": 0,  # For hybrid cars
            "MGU_K_RECOVERY": 0   # For hybrid cars
        },
        "ENGINE": {
            "ENGINE_LIMITER": 0,   # Engine braking
            "TURBO_BOOST": 0       # Turbo boost level
        }
    }
    
    # Value limits (min, max) for clamping
    VALUE_LIMITS = {
        "TYRES": {
            "PRESSURE_LF": (20.0, 35.0),
            "PRESSURE_RF": (20.0, 35.0),
            "PRESSURE_LR": (20.0, 35.0),
            "PRESSURE_RR": (20.0, 35.0),
            "COMPOUND": (0, 10)  # Varies by car
        },
        "BRAKES": {
            "BIAS": (40.0, 80.0),
            "FRONT_BIAS": (40.0, 80.0),
            "BRAKE_POWER_MULT": (0.5, 1.5)
        },
        "SUSPENSION": {
            "SPRING_RATE_LF": (40000, 150000),
            "SPRING_RATE_RF": (40000, 150000),
            "SPRING_RATE_LR": (35000, 130000),
            "SPRING_RATE_RR": (35000, 130000),
            "DAMP_BUMP_LF": (1000, 8000),
            "DAMP_BUMP_RF": (1000, 8000),
            "DAMP_BUMP_LR": (1000, 8000),
            "DAMP_BUMP_RR": (1000, 8000),
            "DAMP_REBOUND_LF": (2000, 12000),
            "DAMP_REBOUND_RF": (2000, 12000),
            "DAMP_REBOUND_LR": (2000, 12000),
            "DAMP_REBOUND_RR": (2000, 12000),
            "RIDE_HEIGHT_LF": (30, 80),
            "RIDE_HEIGHT_RF": (30, 80),
            "RIDE_HEIGHT_LR": (35, 85),
            "RIDE_HEIGHT_RR": (35, 85),
            "DAMP_FAST_BUMP_LF": (500, 6000),
            "DAMP_FAST_BUMP_RF": (500, 6000),
            "DAMP_FAST_BUMP_LR": (500, 6000),
            "DAMP_FAST_BUMP_RR": (500, 6000),
            "DAMP_FAST_REBOUND_LF": (1000, 10000),
            "DAMP_FAST_REBOUND_RF": (1000, 10000),
            "DAMP_FAST_REBOUND_LR": (1000, 10000),
            "DAMP_FAST_REBOUND_RR": (1000, 10000),
            "PACKER_LF": (0, 30),
            "PACKER_RF": (0, 30),
            "PACKER_LR": (0, 30),
            "PACKER_RR": (0, 30)
        },
        "DIFFERENTIAL": {
            "POWER": (0.0, 100.0),
            "COAST": (0.0, 100.0),
            "PRELOAD": (0.0, 200.0)
        },
        "ALIGNMENT": {
            "CAMBER_LF": (-5.0, 0.0),
            "CAMBER_RF": (-5.0, 0.0),
            "CAMBER_LR": (-4.0, 0.0),
            "CAMBER_RR": (-4.0, 0.0),
            "TOE_LF": (-0.5, 0.5),
            "TOE_RF": (-0.5, 0.5),
            "TOE_LR": (-0.3, 0.5),
            "TOE_RR": (-0.3, 0.5),
            "CASTER_LF": (-2.0, 10.0),
            "CASTER_RF": (-2.0, 10.0)
        },
        "AERO": {
            "WING_FRONT": (0, 20),
            "WING_REAR": (0, 20),
            "SPLITTER": (0, 10),
            "REAR_WING": (0, 20)
        },
        "FUEL": {
            "FUEL": (5, 100)
        },
        "ARB": {
            "FRONT": (0, 10),
            "REAR": (0, 10)
        },
        "ELECTRONICS": {
            "TC": (0, 12),
            "ABS": (0, 12),
            "ENGINE_MAP": (0, 10),
            "MGU_K_DELIVERY": (0, 10),
            "MGU_K_RECOVERY": (0, 10)
        },
        "ENGINE": {
            "ENGINE_LIMITER": (0, 10),
            "TURBO_BOOST": (0, 10)
        }
    }
    
    def __init__(self):
        """Initialize setup engine with sub-engines."""
        self.behavior_engine = BehaviorEngine()
        self.rules_engine = RulesEngine()
        self.scoring_engine = ScoringEngine()
    
    def generate_setup(
        self,
        profile: DriverProfile,
        behavior_id: str,
        car: Optional[Car] = None,
        track: Optional[Track] = None,
        setup_name: str = "Generated Setup"
    ) -> tuple[Setup, ScoreBreakdown]:
        """
        Generate a complete setup based on profile and behavior.
        Returns the setup and its score breakdown.
        """
        # Get behavior
        behavior = self.behavior_engine.get_behavior(behavior_id)
        if not behavior:
            behavior = self.behavior_engine.get_behavior("balanced")
        
        # Start with base values
        setup = self._create_base_setup(car, track, setup_name, behavior_id)
        
        # Apply behavior modifiers
        setup = self._apply_behavior_modifiers(setup, behavior)
        
        # Apply rule-based adjustments
        setup = self._apply_rule_adjustments(setup, profile, car, track, behavior)
        
        # Apply driver profile fine-tuning
        setup = self._apply_profile_tuning(setup, profile)
        
        # Clamp all values to valid ranges
        setup = self._clamp_values(setup)
        
        # Score the final setup
        score = self.scoring_engine.score_setup(setup, profile, behavior, car, track)
        setup.ai_score = score.total_score
        setup.ai_confidence = score.confidence
        
        return setup, score
    
    # Race car classes that should use AC default setups
    RACE_CAR_CLASSES = [
        "gt3", "gt2", "gt4", "gte", "gtlm",
        "lmp1", "lmp2", "lmp3", "prototype",
        "formula", "f1", "f2", "f3", "f4",
        "dtm", "touring", "tcr",
        "race", "gt"
    ]
    
    def _create_base_setup(
        self,
        car: Optional[Car],
        track: Optional[Track],
        name: str,
        behavior_id: str
    ) -> Setup:
        """Create a setup with base values."""
        setup = Setup(
            name=name,
            car_id=car.car_id if car else "",
            track_id=track.full_id if track else "",
            behavior=behavior_id
        )
        
        # For race cars, try to load AC's default setup first
        if car and self._is_race_car(car):
            ac_setup = self._load_ac_default_setup(car)
            if ac_setup:
                # Use AC default setup as base
                for section_name, section in ac_setup.sections.items():
                    setup.sections[section_name] = SetupSection(
                        section_name, 
                        section.values.copy()
                    )
                print(f"[SETUP] Using AC default setup for {car.name}")
                return setup
            else:
                print(f"[SETUP] No AC default found for {car.name}, using generic values")
        
        # Fallback: Initialize with generic base values (good for Touge/street cars)
        for section_name, values in self.BASE_VALUES.items():
            setup.sections[section_name] = SetupSection(section_name, values.copy())
        
        return setup
    
    def _is_race_car(self, car: Car) -> bool:
        """Check if car is a race car that needs AC default setup."""
        if not car:
            return False
        
        # Check car_class
        car_class_lower = car.car_class.lower() if car.car_class else ""
        for race_class in self.RACE_CAR_CLASSES:
            if race_class in car_class_lower:
                return True
        
        # Check car_id for common race car patterns
        car_id_lower = car.car_id.lower()
        race_patterns = ["_gt3", "_gt2", "_gt4", "_gte", "_lmp", "_dtm", "_tcr", "_f1", "_f2", "_f3"]
        for pattern in race_patterns:
            if pattern in car_id_lower:
                return True
        
        # Check car name
        name_lower = car.name.lower() if car.name else ""
        if any(x in name_lower for x in ["gt3", "gt2", "gt4", "gte", "lmp", "dtm", "formula"]):
            return True
        
        return False
    
    def _load_ac_default_setup(self, car: Car) -> Optional[Setup]:
        """
        Load the default setup from AC's car data folder.
        Path: content/cars/{car_id}/data/setup.ini
        """
        if not car or not car.path:
            return None
        
        # Try multiple possible locations for default setup
        possible_paths = [
            car.path / "data" / "setup.ini",
            car.path / "data" / "default_setup.ini",
            car.path / "setups" / "default.ini",
        ]
        
        for setup_path in possible_paths:
            if setup_path.exists():
                setup = self._parse_ini_setup(setup_path, car)
                if setup:
                    return setup
        
        return None
    
    def _parse_ini_setup(self, file_path: Path, car: Car) -> Optional[Setup]:
        """Parse an INI setup file into a Setup object."""
        try:
            config = configparser.ConfigParser()
            config.read(file_path, encoding="utf-8")
            
            setup = Setup(
                name="AC_Default",
                car_id=car.car_id,
                track_id=""
            )
            
            for section_name in config.sections():
                section_values = {}
                for key, value in config.items(section_name):
                    parsed_value = self._parse_ini_value(value)
                    section_values[key.upper()] = parsed_value
                
                if section_values:
                    setup.sections[section_name.upper()] = SetupSection(
                        section_name.upper(), 
                        section_values
                    )
            
            return setup if setup.sections else None
            
        except (configparser.Error, IOError, Exception) as e:
            print(f"[SETUP] Error parsing {file_path}: {e}")
            return None
    
    def _parse_ini_value(self, value: str):
        """Parse a string value to appropriate type."""
        value = value.strip()
        
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        return value
    
    def _is_click_based_setup(self, setup: Setup) -> bool:
        """
        Detect if setup uses click-based values (race cars) or absolute values (street cars).
        Click-based setups have small spring rate values (1-30), absolute have large (40000+).
        """
        spring_rate = setup.get_value("SUSPENSION", "SPRING_RATE_LF", None)
        if spring_rate is None:
            return False
        return spring_rate < 1000  # Click-based if under 1000
    
    def _apply_behavior_modifiers(self, setup: Setup, behavior: Behavior) -> Setup:
        """Apply behavior modifiers to the setup."""
        
        # Detect if this is a click-based setup (race car) or absolute values (street car)
        is_click_based = self._is_click_based_setup(setup)
        
        # Suspension stiffness - use smaller adjustments for click-based
        if behavior.suspension_stiffness != 0:
            if is_click_based:
                # Click-based: add/subtract 1-2 clicks
                adjustment = int(behavior.suspension_stiffness * 2)
                for key in ["SPRING_RATE_LF", "SPRING_RATE_RF", "SPRING_RATE_LR", "SPRING_RATE_RR"]:
                    current = setup.get_value("SUSPENSION", key, 10)
                    setup.set_value("SUSPENSION", key, max(1, current + adjustment))
            else:
                # Absolute values: use multiplier
                multiplier = 1.0 + (behavior.suspension_stiffness * 0.2)
                for key in ["SPRING_RATE_LF", "SPRING_RATE_RF", "SPRING_RATE_LR", "SPRING_RATE_RR"]:
                    current = setup.get_value("SUSPENSION", key, 70000)
                    setup.set_value("SUSPENSION", key, int(current * multiplier))
        
        # Suspension damping
        if behavior.suspension_damping != 0:
            if is_click_based:
                # Click-based: add/subtract 1-2 clicks
                adjustment = int(behavior.suspension_damping * 2)
                for key in ["DAMP_BUMP_LF", "DAMP_BUMP_RF", "DAMP_BUMP_LR", "DAMP_BUMP_RR",
                           "DAMP_REBOUND_LF", "DAMP_REBOUND_RF", "DAMP_REBOUND_LR", "DAMP_REBOUND_RR"]:
                    current = setup.get_value("SUSPENSION", key, 5)
                    setup.set_value("SUSPENSION", key, max(1, current + adjustment))
            else:
                # Absolute values: use multiplier
                multiplier = 1.0 + (behavior.suspension_damping * 0.15)
                for key in ["DAMP_BUMP_LF", "DAMP_BUMP_RF", "DAMP_BUMP_LR", "DAMP_BUMP_RR",
                           "DAMP_REBOUND_LF", "DAMP_REBOUND_RF", "DAMP_REBOUND_LR", "DAMP_REBOUND_RR"]:
                    current = setup.get_value("SUSPENSION", key, 3000)
                    setup.set_value("SUSPENSION", key, int(current * multiplier))
        
        # Ride height - smaller adjustments for click-based
        if behavior.ride_height != 0:
            if is_click_based:
                adjustment = int(behavior.ride_height * 2)  # 1-2 clicks
            else:
                adjustment = int(behavior.ride_height * 10)  # 10mm
            for key in ["RIDE_HEIGHT_LF", "RIDE_HEIGHT_RF", "RIDE_HEIGHT_LR", "RIDE_HEIGHT_RR"]:
                current = setup.get_value("SUSPENSION", key, 50)
                setup.set_value("SUSPENSION", key, max(1, current + adjustment))
        
        # ARB - same logic for both (usually click-based anyway)
        if behavior.arb_front != 0:
            adjustment = int(behavior.arb_front * 2) if is_click_based else int(behavior.arb_front * 3)
            current = setup.get_value("ARB", "FRONT", 5)
            setup.set_value("ARB", "FRONT", max(0, current + adjustment))
        
        if behavior.arb_rear != 0:
            adjustment = int(behavior.arb_rear * 2) if is_click_based else int(behavior.arb_rear * 3)
            current = setup.get_value("ARB", "REAR", 4)
            setup.set_value("ARB", "REAR", max(0, current + adjustment))
        
        # Differential - smaller adjustments for race cars
        if behavior.diff_power != 0:
            current = setup.get_value("DIFFERENTIAL", "POWER", 45)
            adjustment = behavior.diff_power * 10 if is_click_based else behavior.diff_power * 25
            setup.set_value("DIFFERENTIAL", "POWER", current + adjustment)
        
        if behavior.diff_coast != 0:
            current = setup.get_value("DIFFERENTIAL", "COAST", 35)
            adjustment = behavior.diff_coast * 8 if is_click_based else behavior.diff_coast * 20
            setup.set_value("DIFFERENTIAL", "COAST", current + adjustment)
        
        if behavior.diff_preload != 0:
            current = setup.get_value("DIFFERENTIAL", "PRELOAD", 25)
            adjustment = behavior.diff_preload * 10 if is_click_based else behavior.diff_preload * 30
            setup.set_value("DIFFERENTIAL", "PRELOAD", current + adjustment)
        
        # Camber - smaller adjustments for race cars (already optimized)
        if behavior.camber_front != 0:
            adjustment = behavior.camber_front * -0.3 if is_click_based else behavior.camber_front * -1.0
            for key in ["CAMBER_LF", "CAMBER_RF"]:
                current = setup.get_value("ALIGNMENT", key, -3.0)
                setup.set_value("ALIGNMENT", key, current + adjustment)
        
        if behavior.camber_rear != 0:
            adjustment = behavior.camber_rear * -0.2 if is_click_based else behavior.camber_rear * -0.8
            for key in ["CAMBER_LR", "CAMBER_RR"]:
                current = setup.get_value("ALIGNMENT", key, -2.0)
                setup.set_value("ALIGNMENT", key, current + adjustment)
        
        # Toe - very small adjustments for race cars
        if behavior.toe_front != 0:
            adjustment = behavior.toe_front * 0.05 if is_click_based else behavior.toe_front * 0.15
            for key in ["TOE_LF", "TOE_RF"]:
                current = setup.get_value("ALIGNMENT", key, 0.0)
                setup.set_value("ALIGNMENT", key, current + adjustment)
        
        if behavior.toe_rear != 0:
            adjustment = behavior.toe_rear * 0.05 if is_click_based else behavior.toe_rear * 0.15
            for key in ["TOE_LR", "TOE_RR"]:
                current = setup.get_value("ALIGNMENT", key, 0.1)
                setup.set_value("ALIGNMENT", key, current + adjustment)
        
        # Brakes - smaller adjustments for race cars
        if behavior.brake_bias != 0:
            current = setup.get_value("BRAKES", "BIAS", 58)
            adjustment = behavior.brake_bias * 2 if is_click_based else behavior.brake_bias * 5
            setup.set_value("BRAKES", "BIAS", current + adjustment)
            setup.set_value("BRAKES", "FRONT_BIAS", current + adjustment)
        
        # Tyre pressure - smaller adjustments for race cars (more sensitive)
        if behavior.tyre_pressure != 0:
            adjustment = behavior.tyre_pressure * 0.5 if is_click_based else behavior.tyre_pressure * 2.0
            for key in ["PRESSURE_LF", "PRESSURE_RF", "PRESSURE_LR", "PRESSURE_RR"]:
                current = setup.get_value("TYRES", key, 26.0)
                setup.set_value("TYRES", key, current + adjustment)
        
        # Fast dampers (follow regular damper adjustments)
        if behavior.suspension_damping != 0:
            if is_click_based:
                adjustment = int(behavior.suspension_damping * 2)
                for key in ["DAMP_FAST_BUMP_LF", "DAMP_FAST_BUMP_RF", "DAMP_FAST_BUMP_LR", "DAMP_FAST_BUMP_RR",
                           "DAMP_FAST_REBOUND_LF", "DAMP_FAST_REBOUND_RF", "DAMP_FAST_REBOUND_LR", "DAMP_FAST_REBOUND_RR"]:
                    current = setup.get_value("SUSPENSION", key, 5)
                    setup.set_value("SUSPENSION", key, max(1, current + adjustment))
            else:
                multiplier = 1.0 + (behavior.suspension_damping * 0.15)
                for key in ["DAMP_FAST_BUMP_LF", "DAMP_FAST_BUMP_RF", "DAMP_FAST_BUMP_LR", "DAMP_FAST_BUMP_RR",
                           "DAMP_FAST_REBOUND_LF", "DAMP_FAST_REBOUND_RF", "DAMP_FAST_REBOUND_LR", "DAMP_FAST_REBOUND_RR"]:
                    current = setup.get_value("SUSPENSION", key, 2000)
                    setup.set_value("SUSPENSION", key, int(current * multiplier))
        
        # Aero - wing adjustments based on downforce preference
        if hasattr(behavior, 'aero_downforce') and behavior.aero_downforce != 0:
            adjustment = int(behavior.aero_downforce * 5)
            for key in ["WING_FRONT", "WING_REAR", "SPLITTER", "REAR_WING"]:
                current = setup.get_value("AERO", key, 0)
                setup.set_value("AERO", key, max(0, current + adjustment))
        
        # Electronics - TC/ABS based on behavior aggressiveness
        # More aggressive = less TC/ABS, more conservative = more TC/ABS
        if hasattr(behavior, 'stability') and behavior.stability != 0:
            tc_adj = int(behavior.stability * 3)  # -3 to +3
            abs_adj = int(behavior.stability * 2)  # -2 to +2
            
            current_tc = setup.get_value("ELECTRONICS", "TC", 5)
            current_abs = setup.get_value("ELECTRONICS", "ABS", 3)
            
            setup.set_value("ELECTRONICS", "TC", max(0, min(12, current_tc + tc_adj)))
            setup.set_value("ELECTRONICS", "ABS", max(0, min(12, current_abs + abs_adj)))
        
        return setup
    
    def _apply_rule_adjustments(
        self,
        setup: Setup,
        profile: DriverProfile,
        car: Optional[Car],
        track: Optional[Track],
        behavior: Behavior
    ) -> Setup:
        """Apply rule-based adjustments from the rules engine."""
        adjustments = self.rules_engine.get_adjustments(profile, car, track, behavior)
        
        # Track multipliers for special parameters
        spring_multiplier = 1.0
        damp_multiplier = 1.0
        ride_height_multiplier = 1.0
        camber_multiplier = 1.0
        
        for section, params in adjustments.items():
            for param, (adj_type, value) in params.items():
                # Handle special multiplier parameters
                if param == "SPRING_RATE_MULTIPLIER":
                    spring_multiplier *= value
                    continue
                elif param == "DAMP_MULTIPLIER":
                    damp_multiplier *= value
                    continue
                elif param == "RIDE_HEIGHT_MULTIPLIER":
                    ride_height_multiplier *= value
                    continue
                elif param == "CAMBER_MULTIPLIER":
                    camber_multiplier *= value
                    continue
                elif param == "PRESSURE_ALL":
                    # Apply to all tyre pressures
                    for p in ["PRESSURE_LF", "PRESSURE_RF", "PRESSURE_LR", "PRESSURE_RR"]:
                        current = setup.get_value("TYRES", p, 26.0)
                        setup.set_value("TYRES", p, current + value)
                    continue
                
                # Apply adjustment based on type
                current = setup.get_value(section, param)
                if current is None:
                    continue
                
                if adj_type == "absolute":
                    setup.set_value(section, param, value)
                elif adj_type == "relative":
                    setup.set_value(section, param, current + value)
                elif adj_type == "multiply":
                    setup.set_value(section, param, current * value)
        
        # Apply accumulated multipliers
        if spring_multiplier != 1.0:
            for key in ["SPRING_RATE_LF", "SPRING_RATE_RF", "SPRING_RATE_LR", "SPRING_RATE_RR"]:
                current = setup.get_value("SUSPENSION", key, 70000)
                setup.set_value("SUSPENSION", key, int(current * spring_multiplier))
        
        if damp_multiplier != 1.0:
            for key in ["DAMP_BUMP_LF", "DAMP_BUMP_RF", "DAMP_BUMP_LR", "DAMP_BUMP_RR",
                       "DAMP_REBOUND_LF", "DAMP_REBOUND_RF", "DAMP_REBOUND_LR", "DAMP_REBOUND_RR"]:
                current = setup.get_value("SUSPENSION", key, 3000)
                setup.set_value("SUSPENSION", key, int(current * damp_multiplier))
        
        if ride_height_multiplier != 1.0:
            for key in ["RIDE_HEIGHT_LF", "RIDE_HEIGHT_RF", "RIDE_HEIGHT_LR", "RIDE_HEIGHT_RR"]:
                current = setup.get_value("SUSPENSION", key, 50)
                setup.set_value("SUSPENSION", key, int(current * ride_height_multiplier))
        
        if camber_multiplier != 1.0:
            for key in ["CAMBER_LF", "CAMBER_RF", "CAMBER_LR", "CAMBER_RR"]:
                current = setup.get_value("ALIGNMENT", key, -2.5)
                setup.set_value("ALIGNMENT", key, current * camber_multiplier)
        
        return setup
    
    def _apply_profile_tuning(self, setup: Setup, profile: DriverProfile) -> Setup:
        """Apply fine-tuning based on driver profile factors.
        
        This method applies the user's preferences from the UI sliders to the setup.
        Each preference affects specific setup parameters.
        """
        factors = profile.get_all_factors()
        
        # ═══════════════════════════════════════════════════════════════
        # STABILITY vs ROTATION preference
        # ═══════════════════════════════════════════════════════════════
        rotation = factors["rotation"]  # 0 = stable, 1 = rotational
        
        # More rotation = looser rear, tighter front
        if rotation > 0.5:
            # Increase rear toe-out for rotation
            rear_toe_adj = (rotation - 0.5) * 0.3  # Up to +0.15 degrees
            for key in ["TOE_LR", "TOE_RR"]:
                current = setup.get_value("ALIGNMENT", key, 0.1)
                setup.set_value("ALIGNMENT", key, current + rear_toe_adj)
            
            # Softer rear ARB for rotation
            rear_arb = setup.get_value("ARB", "REAR", 4)
            setup.set_value("ARB", "REAR", rear_arb * (1.0 - (rotation - 0.5) * 0.3))
        else:
            # More stability = stiffer rear
            stability = factors["stability"]
            rear_arb = setup.get_value("ARB", "REAR", 4)
            setup.set_value("ARB", "REAR", rear_arb * (1.0 + stability * 0.2))
        
        # ═══════════════════════════════════════════════════════════════
        # GRIP vs SLIDE preference
        # ═══════════════════════════════════════════════════════════════
        slide = factors["slide"]  # 0 = max grip, 1 = allows sliding
        
        if slide > 0.5:
            # More slide = lower tire pressures, less camber
            pressure_adj = (slide - 0.5) * 2  # Up to -1 psi
            for key in ["PRESSURE_LF", "PRESSURE_RF", "PRESSURE_LR", "PRESSURE_RR"]:
                current = setup.get_value("TYRES", key, 26.0)
                setup.set_value("TYRES", key, current - pressure_adj)
            
            # Less aggressive camber for sliding
            camber_mult = 1.0 - (slide - 0.5) * 0.3
            for key in ["CAMBER_LF", "CAMBER_RF", "CAMBER_LR", "CAMBER_RR"]:
                current = setup.get_value("ALIGNMENT", key, -3.0)
                setup.set_value("ALIGNMENT", key, current * camber_mult)
        else:
            # More grip = optimal pressures, more camber
            grip = factors["grip"]
            camber_mult = 1.0 + grip * 0.15
            for key in ["CAMBER_LF", "CAMBER_RF"]:
                current = setup.get_value("ALIGNMENT", key, -3.0)
                setup.set_value("ALIGNMENT", key, current * camber_mult)
        
        # ═══════════════════════════════════════════════════════════════
        # AGGRESSION preference
        # ═══════════════════════════════════════════════════════════════
        aggression = factors["aggression"]  # 0 = safe, 1 = aggressive
        
        # Aggressive = stiffer suspension, more responsive
        if aggression > 0.5:
            stiffness_mult = 1.0 + (aggression - 0.5) * 0.3
            for key in ["SPRING_RATE_LF", "SPRING_RATE_RF", "SPRING_RATE_LR", "SPRING_RATE_RR"]:
                current = setup.get_value("SUSPENSION", key, 70000)
                setup.set_value("SUSPENSION", key, int(current * stiffness_mult))
            
            # More aggressive diff
            diff_power = setup.get_value("DIFFERENTIAL", "POWER", 45)
            setup.set_value("DIFFERENTIAL", "POWER", diff_power * (1.0 + (aggression - 0.5) * 0.4))
        else:
            # Safe = softer, more forgiving
            safety = factors["safety"]
            diff_power = setup.get_value("DIFFERENTIAL", "POWER", 45)
            setup.set_value("DIFFERENTIAL", "POWER", diff_power * (1.0 - safety * 0.2))
        
        # ═══════════════════════════════════════════════════════════════
        # DRIFT preference
        # ═══════════════════════════════════════════════════════════════
        drift = factors["drift"]  # 0 = grip-oriented, 1 = drift-oriented
        
        if drift > 0.3:
            # Drift setup: locked diff, rear bias, softer rear
            diff_power = setup.get_value("DIFFERENTIAL", "POWER", 45)
            setup.set_value("DIFFERENTIAL", "POWER", min(100, diff_power + drift * 40))
            
            diff_coast = setup.get_value("DIFFERENTIAL", "COAST", 30)
            setup.set_value("DIFFERENTIAL", "COAST", min(100, diff_coast + drift * 30))
            
            # More rear brake bias for drift initiation
            brake_bias = setup.get_value("BRAKES", "FRONT_BIAS", 60)
            setup.set_value("BRAKES", "FRONT_BIAS", brake_bias - drift * 10)
        
        # ═══════════════════════════════════════════════════════════════
        # COMFORT vs PERFORMANCE preference
        # ═══════════════════════════════════════════════════════════════
        performance = factors["performance"]  # 0 = comfort, 1 = performance
        
        if performance > 0.5:
            # Performance = stiffer damping, lower ride height
            damp_mult = 1.0 + (performance - 0.5) * 0.4
            for key in ["DAMP_BUMP_LF", "DAMP_BUMP_RF", "DAMP_BUMP_LR", "DAMP_BUMP_RR",
                       "DAMP_REBOUND_LF", "DAMP_REBOUND_RF", "DAMP_REBOUND_LR", "DAMP_REBOUND_RR"]:
                current = setup.get_value("SUSPENSION", key, 3000)
                setup.set_value("SUSPENSION", key, int(current * damp_mult))
            
            # Lower ride height for performance
            height_adj = (performance - 0.5) * 10  # Up to -5mm
            for key in ["RIDE_HEIGHT_LF", "RIDE_HEIGHT_RF", "RIDE_HEIGHT_LR", "RIDE_HEIGHT_RR"]:
                current = setup.get_value("SUSPENSION", key, 50)
                setup.set_value("SUSPENSION", key, max(30, current - height_adj))
        else:
            # Comfort = softer damping
            comfort = factors["comfort"]
            damp_mult = 1.0 - comfort * 0.2
            for key in ["DAMP_BUMP_LF", "DAMP_BUMP_RF", "DAMP_BUMP_LR", "DAMP_BUMP_RR"]:
                current = setup.get_value("SUSPENSION", key, 3000)
                setup.set_value("SUSPENSION", key, int(current * damp_mult))
        
        # ═══════════════════════════════════════════════════════════════
        # EXPERIENCE level adjustments
        # ═══════════════════════════════════════════════════════════════
        exp_mult = factors["experience"]
        
        # Beginners get more conservative settings
        if exp_mult < 0.7:
            # Reduce diff lock for beginners
            diff_power = setup.get_value("DIFFERENTIAL", "POWER", 45)
            setup.set_value("DIFFERENTIAL", "POWER", diff_power * 0.8)
            
            # More forgiving camber
            for key in ["CAMBER_LF", "CAMBER_RF", "CAMBER_LR", "CAMBER_RR"]:
                current = setup.get_value("ALIGNMENT", key, -3.0)
                setup.set_value("ALIGNMENT", key, current * 0.8)
        
        # Experts can handle more aggressive settings
        elif exp_mult > 1.0:
            # Allow more negative camber
            for key in ["CAMBER_LF", "CAMBER_RF"]:
                current = setup.get_value("ALIGNMENT", key, -3.0)
                setup.set_value("ALIGNMENT", key, current * 1.15)
        
        # ═══════════════════════════════════════════════════════════════
        # ELECTRONICS adjustments based on experience
        # ═══════════════════════════════════════════════════════════════
        # Beginners get more TC/ABS, experts get less
        if exp_mult < 0.7:
            # More assists for beginners
            current_tc = setup.get_value("ELECTRONICS", "TC", 5)
            current_abs = setup.get_value("ELECTRONICS", "ABS", 3)
            setup.set_value("ELECTRONICS", "TC", min(12, current_tc + 3))
            setup.set_value("ELECTRONICS", "ABS", min(12, current_abs + 2))
        elif exp_mult > 1.0:
            # Less assists for experts
            current_tc = setup.get_value("ELECTRONICS", "TC", 5)
            current_abs = setup.get_value("ELECTRONICS", "ABS", 3)
            setup.set_value("ELECTRONICS", "TC", max(0, current_tc - 2))
            setup.set_value("ELECTRONICS", "ABS", max(0, current_abs - 1))
        
        # ═══════════════════════════════════════════════════════════════
        # AERO adjustments based on aggression/performance
        # ═══════════════════════════════════════════════════════════════
        if aggression > 0.6:
            # More aggressive = less downforce for speed
            for key in ["WING_FRONT", "WING_REAR", "REAR_WING"]:
                current = setup.get_value("AERO", key, 5)
                setup.set_value("AERO", key, max(0, int(current * 0.8)))
        elif factors.get("safety", 0) > 0.6:
            # More safety = more downforce for stability
            for key in ["WING_FRONT", "WING_REAR", "REAR_WING"]:
                current = setup.get_value("AERO", key, 5)
                setup.set_value("AERO", key, min(20, int(current * 1.2)))
        
        return setup
    
    def _clamp_values(self, setup: Setup) -> Setup:
        """Clamp all values to valid ranges."""
        for section_name, limits in self.VALUE_LIMITS.items():
            section = setup.get_section(section_name)
            if not section:
                continue
            
            for param, (min_val, max_val) in limits.items():
                value = section.get(param)
                if value is not None:
                    clamped = max(min_val, min(max_val, value))
                    # Round appropriately
                    if isinstance(min_val, int):
                        clamped = int(round(clamped))
                    else:
                        clamped = round(clamped, 2)
                    section.set(param, clamped)
        
        return setup
    
    def get_available_behaviors(self) -> list[dict]:
        """Get list of available behaviors with descriptions."""
        behaviors = self.behavior_engine.get_all_behaviors()
        return [
            {
                "id": b.behavior_id,
                "name": b.name,
                "description": b.description
            }
            for b in behaviors
        ]
    
    def preview_setup(
        self,
        profile: DriverProfile,
        behavior_id: str,
        car: Optional[Car] = None,
        track: Optional[Track] = None
    ) -> dict:
        """Generate a preview of setup values without creating full setup."""
        setup, score = self.generate_setup(profile, behavior_id, car, track, "Preview")
        
        return {
            "behavior": behavior_id,
            "score": score.total_score,
            "confidence": score.confidence,
            "key_values": {
                "diff_power": setup.get_value("DIFFERENTIAL", "POWER"),
                "diff_coast": setup.get_value("DIFFERENTIAL", "COAST"),
                "brake_bias": setup.get_value("BRAKES", "BIAS"),
                "front_camber": setup.get_value("ALIGNMENT", "CAMBER_LF"),
                "rear_camber": setup.get_value("ALIGNMENT", "CAMBER_LR"),
                "front_arb": setup.get_value("ARB", "FRONT"),
                "rear_arb": setup.get_value("ARB", "REAR")
            },
            "notes": score.notes
        }
