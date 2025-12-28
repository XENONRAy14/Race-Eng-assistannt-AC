"""
Setup Engine V2.2 - Complete physics-based setup generation with all V2.2 features.
Integrates: Dynamic mapping, smart conversion, slider interdependencies, debug logging.
"""

from pathlib import Path
from typing import Optional, Dict, Tuple, List
from dataclasses import dataclass

from models.setup import Setup, SetupSection
from models.car import Car
from models.track import Track
from models.driver_profile import DriverProfile

from core.setup_engine_v2 import SetupEngineV2, CATEGORY_TARGETS, CategoryTargets
from core.physics_refiner import PhysicsRefiner
from core.dynamic_mapper import DynamicMapper, ValueTypeDetector
from core.clicks_converter import SmartConverter, ClicksConverter
from core.slider_interdependencies import SliderInterdependencyEngine
from core.setup_debug_logger import SetupDebugLogger
from core.setup_writer_v2 import SetupWriterV2


# ═══════════════════════════════════════════════════════════════════════════
# V2.2 CATEGORY TARGETS (Updated based on engineer feedback)
# ═══════════════════════════════════════════════════════════════════════════

CATEGORY_TARGETS_V22 = {
    # GT3 / Race - Engineer validated
    "gt": CategoryTargets(
        frequency_front=2.8,
        frequency_rear=3.0,
        damping_ratio=0.7,
        hot_pressure_front=27.5,
        hot_pressure_rear=27.0,
        camber_front=-4.0,
        camber_rear=-3.0,
        toe_front=-0.05,
        toe_rear=0.15,
        caster=6.0,
        rake_angle=0.8,
        diff_power=65.0,
        diff_coast=50.0,
        diff_preload=30.0,
        brake_bias=58.0,
        arb_bias=0.55
    ),
    
    # Formula - Engineer validated (3.5-4.5 Hz)
    "formula": CategoryTargets(
        frequency_front=3.8,
        frequency_rear=4.2,
        damping_ratio=0.65,
        hot_pressure_front=24.0,
        hot_pressure_rear=23.0,
        camber_front=-3.5,
        camber_rear=-2.0,
        toe_front=-0.03,
        toe_rear=0.08,
        caster=5.5,
        rake_angle=1.5,
        diff_power=75.0,
        diff_coast=55.0,
        diff_preload=40.0,
        brake_bias=56.0,
        arb_bias=0.50
    ),
    
    # Prototype / LMP
    "prototype": CategoryTargets(
        frequency_front=3.5,
        frequency_rear=3.8,
        damping_ratio=0.68,
        hot_pressure_front=26.0,
        hot_pressure_rear=25.5,
        camber_front=-3.8,
        camber_rear=-2.5,
        toe_front=-0.04,
        toe_rear=0.10,
        caster=5.8,
        rake_angle=1.8,
        diff_power=70.0,
        diff_coast=55.0,
        diff_preload=35.0,
        brake_bias=57.0,
        arb_bias=0.52
    ),
    
    # Street / Touge - Engineer validated (1.8-2.2 Hz)
    "street": CategoryTargets(
        frequency_front=1.8,
        frequency_rear=2.0,
        damping_ratio=0.5,
        hot_pressure_front=32.0,
        hot_pressure_rear=30.0,
        camber_front=-2.0,
        camber_rear=-1.5,
        toe_front=0.0,
        toe_rear=0.10,
        caster=5.0,
        rake_angle=0.0,
        diff_power=40.0,
        diff_coast=30.0,
        diff_preload=20.0,
        brake_bias=60.0,
        arb_bias=0.50
    ),
    
    # Street Sport
    "street_sport": CategoryTargets(
        frequency_front=2.2,
        frequency_rear=2.4,
        damping_ratio=0.55,
        hot_pressure_front=30.0,
        hot_pressure_rear=28.0,
        camber_front=-2.8,
        camber_rear=-2.2,
        toe_front=-0.02,
        toe_rear=0.12,
        caster=5.5,
        rake_angle=0.3,
        diff_power=45.0,
        diff_coast=35.0,
        diff_preload=25.0,
        brake_bias=58.0,
        arb_bias=0.52
    ),
    
    # Drift - Engineer validated (2.2-2.5 Hz, diff 85%+)
    "drift": CategoryTargets(
        frequency_front=2.5,
        frequency_rear=1.8,  # Softer rear for easier slide
        damping_ratio=0.6,
        hot_pressure_front=32.0,
        hot_pressure_rear=36.0,  # Higher rear = less grip
        camber_front=-5.0,  # More front grip
        camber_rear=0.0,    # Zero rear camber for slide
        toe_front=-0.05,
        toe_rear=0.30,      # Toe-out for rotation
        caster=7.0,
        rake_angle=0.2,
        diff_power=85.0,    # Very locked
        diff_coast=65.0,
        diff_preload=50.0,
        brake_bias=65.0,    # Forward bias for initiation
        arb_bias=0.60
    ),
    
    # Vintage
    "vintage": CategoryTargets(
        frequency_front=1.5,
        frequency_rear=1.6,
        damping_ratio=0.45,
        hot_pressure_front=28.0,
        hot_pressure_rear=26.0,
        camber_front=-1.5,
        camber_rear=-1.0,
        toe_front=0.0,
        toe_rear=0.05,
        caster=4.0,
        rake_angle=0.0,
        diff_power=30.0,
        diff_coast=20.0,
        diff_preload=10.0,
        brake_bias=55.0,
        arb_bias=0.45
    ),
}


class SetupEngineV22:
    """
    Complete V2.2 Setup Engine with all features:
    
    1. Physics-based calculations (from V2)
    2. Motion ratio correction (from V2.1)
    3. Dynamic parameter mapping (V2.2)
    4. Smart clicks conversion (V2.2)
    5. Slider interdependencies (V2.2)
    6. Debug logging (V2.2)
    """
    
    def __init__(self, setups_path: Optional[Path] = None):
        """
        Initialize V2.2 engine.
        
        Args:
            setups_path: Path to AC setups folder
        """
        # Core engines
        self.v2_engine = SetupEngineV2()
        self.physics_refiner = PhysicsRefiner()
        
        # V2.2 components
        self.dynamic_mapper = DynamicMapper(setups_path)
        self.value_detector = ValueTypeDetector(setups_path)
        self.smart_converter = SmartConverter()
        self.clicks_converter = ClicksConverter()
        self.slider_engine = SliderInterdependencyEngine()
        self.writer = SetupWriterV2(setups_path)
        
        # State
        self.setups_path = setups_path
        self.logger: Optional[SetupDebugLogger] = None
        self.enable_debug_logging = True
    
    def set_setups_path(self, path: Path):
        """Set the setups path for all components."""
        self.setups_path = path
        self.dynamic_mapper.set_setups_path(path)
        self.value_detector.set_setups_path(path)
        self.writer.set_base_path(path)
    
    def generate_setup(
        self,
        car: Car,
        track: Track,
        behavior_id: str = "balanced",
        profile: Optional[DriverProfile] = None,
        ambient_temp: float = 25.0,
        road_temp: float = 30.0
    ) -> Tuple[Setup, Dict[str, any]]:
        """
        Generate a complete setup using V2.2 pipeline.
        
        Pipeline:
        1. Classify car → Get category targets
        2. Calculate physics-based values (V2)
        3. Apply motion ratio correction (V2.1)
        4. Apply behavior modifiers
        5. Apply slider interdependencies (V2.2)
        6. Convert to AC format (V2.2)
        
        Args:
            car: Car object
            track: Track object
            behavior_id: Behavior preset (safe, balanced, attack, drift)
            profile: Driver profile with slider values
            ambient_temp: Ambient temperature in °C
            road_temp: Road temperature in °C
        
        Returns:
            Tuple of (Setup, metadata_dict)
        """
        # Initialize logger
        if self.enable_debug_logging:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.logger = SetupDebugLogger(Path(f"debug_v22_{timestamp}.log"))
        
        metadata = {
            "version": "2.2",
            "car_id": car.car_id,
            "track_id": track.full_id,
            "behavior": behavior_id,
            "ambient_temp": ambient_temp,
            "road_temp": road_temp,
            "changes": []
        }
        
        # Step 1: Classify car
        category = self.v2_engine.classify_car(car)
        targets = CATEGORY_TARGETS_V22.get(category, CATEGORY_TARGETS_V22["street"])
        
        metadata["category"] = category
        print(f"[V2.2] Car category: {category}")
        
        if self.logger:
            self.logger.set_metadata(car.car_id, track.full_id, behavior_id, category)
        
        # Step 2: Generate base setup with V2 physics
        print(f"[V2.2] Generating physics-based setup...")
        base_setup = self.v2_engine.generate_setup(
            car=car,
            track=track,
            behavior_id=behavior_id,
            profile=profile,
            ambient_temp=ambient_temp,
            road_temp=road_temp
        )
        
        # Step 3: Apply physics refinement (motion ratio, anti-bottoming, fast damping cap)
        print(f"[V2.2] Applying physics refinement...")
        
        # Detect track type
        track_type = self._detect_track_type(track)
        metadata["track_type"] = track_type
        
        # Get car data for motion ratios
        from utils.car_data_loader import load_car_data
        car_data = load_car_data(car.car_id)
        
        refined_setup = self.physics_refiner.refine(
            setup=base_setup,
            category=category,
            rake_angle=targets.rake_angle,
            track_type=track_type,
            car_data=car_data
        )
        
        # Step 4: Apply slider interdependencies (V2.2 "wow" effect)
        if profile:
            print(f"[V2.2] Applying slider interdependencies...")
            
            # Detect if click-based
            is_click_based = self.value_detector.is_click_based(car.car_id, "spring")
            
            # Build profile dict
            profile_dict = {
                "rotation": getattr(profile, "rotation", 0.5),
                "slide": getattr(profile, "slide", 0.5),
                "aggression": getattr(profile, "aggression", 0.5),
                "drift": getattr(profile, "drift", 0.0),
                "performance": getattr(profile, "performance", 0.5),
                "aero": getattr(profile, "aero", 0.5) if hasattr(profile, "aero") else 0.5,
            }
            
            refined_setup, slider_changes = self.slider_engine.apply_all_sliders(
                refined_setup, profile_dict, is_click_based
            )
            
            metadata["changes"].extend(slider_changes)
            
            for change in slider_changes[:10]:  # Log first 10
                print(f"  {change}")
        
        # Step 5: Log final values
        if self.logger:
            self._log_final_values(refined_setup)
            self.logger.print_summary()
        
        metadata["is_click_based"] = self.value_detector.is_click_based(car.car_id, "spring")
        
        return refined_setup, metadata
    
    def generate_and_export(
        self,
        car: Car,
        track: Track,
        behavior_id: str = "balanced",
        profile: Optional[DriverProfile] = None,
        ambient_temp: float = 25.0,
        road_temp: float = 30.0,
        filename: Optional[str] = None,
        overwrite: bool = True
    ) -> Tuple[bool, str, Optional[Path], Setup]:
        """
        Generate and export a setup in one call.
        
        Returns:
            Tuple of (success, message, file_path, setup)
        """
        # Generate setup
        setup, metadata = self.generate_setup(
            car=car,
            track=track,
            behavior_id=behavior_id,
            profile=profile,
            ambient_temp=ambient_temp,
            road_temp=road_temp
        )
        
        # Export using V2.2 writer
        success, message, file_path = self.writer.write_setup(
            setup=setup,
            car_id=car.car_id,
            track_id=track.full_id,
            category=metadata["category"],
            filename=filename,
            overwrite=overwrite
        )
        
        return success, message, file_path, setup
    
    def _detect_track_type(self, track: Track) -> str:
        """Detect track type from track object."""
        track_name_lower = track.name.lower()
        
        # Touge / Mountain roads
        touge_keywords = ["touge", "akina", "usui", "irohazaka", "haruna", "myogi", 
                         "sadamine", "happogahara", "tsuchisaka", "shomaru"]
        for keyword in touge_keywords:
            if keyword in track_name_lower:
                return "touge"
        
        # Street circuits
        street_keywords = ["street", "city", "urban", "highway", "shutoko", "wangan"]
        for keyword in street_keywords:
            if keyword in track_name_lower:
                return "street"
        
        # Drift tracks
        drift_keywords = ["drift", "ebisu", "meihan"]
        for keyword in drift_keywords:
            if keyword in track_name_lower:
                return "drift"
        
        # Default to circuit
        return "circuit"
    
    def _log_final_values(self, setup: Setup):
        """Log all final setup values."""
        if not self.logger:
            return
        
        sections = ["TYRES", "ALIGNMENT", "SUSPENSION", "ARB", "DIFFERENTIAL", "BRAKES", "AERO"]
        
        for section in sections:
            if section in setup.sections:
                for key, value in setup.sections[section].values.items():
                    self.logger.log_exported(
                        f"{section}/{key}",
                        value,
                        f"Final value: {value}"
                    )
    
    def get_car_mapping(self, car_id: str) -> Dict[str, str]:
        """Get parameter mapping for a car."""
        return self.dynamic_mapper.get_car_mapping(car_id)
    
    def get_mapping_summary(self, car_id: str) -> str:
        """Get human-readable mapping summary."""
        return self.dynamic_mapper.get_mapping_summary(car_id)
    
    def classify_car(self, car: Car) -> str:
        """Classify a car into a category."""
        return self.v2_engine.classify_car(car)
    
    def get_category_targets(self, category: str) -> CategoryTargets:
        """Get targets for a category."""
        return CATEGORY_TARGETS_V22.get(category, CATEGORY_TARGETS_V22["street"])


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def create_v22_engine(setups_path: Optional[Path] = None) -> SetupEngineV22:
    """
    Create a fully configured V2.2 engine.
    
    Args:
        setups_path: Path to AC setups folder (auto-detected if None)
    
    Returns:
        Configured SetupEngineV22 instance
    """
    if setups_path is None:
        # Try to auto-detect
        from pathlib import Path
        import os
        
        docs = Path(os.path.expanduser("~/Documents"))
        ac_setups = docs / "Assetto Corsa" / "setups"
        
        if ac_setups.exists():
            setups_path = ac_setups
    
    engine = SetupEngineV22(setups_path)
    
    if setups_path:
        print(f"[V2.2] Engine initialized with setups path: {setups_path}")
    else:
        print("[V2.2] Warning: Setups path not found, some features may be limited")
    
    return engine
