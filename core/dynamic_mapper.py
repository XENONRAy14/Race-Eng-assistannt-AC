"""
Dynamic Mapper V2.2 - Universal parameter mapping for any car (Kunos or mods).
Parses existing setups to detect available parameters and creates dynamic mappings.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re


# ═══════════════════════════════════════════════════════════════════════════
# PARAMETER CATEGORIES - What we want to control
# ═══════════════════════════════════════════════════════════════════════════

PARAMETER_CATEGORIES = {
    # Tyres / Pressure
    "pressure_lf": ["PRESSURE_LF", "TYRE_PRESSURE_LF", "TYRE_PRESSURE_0", "PRESSURE_FL", "TIRE_PRESSURE_LF"],
    "pressure_rf": ["PRESSURE_RF", "TYRE_PRESSURE_RF", "TYRE_PRESSURE_1", "PRESSURE_FR", "TIRE_PRESSURE_RF"],
    "pressure_lr": ["PRESSURE_LR", "TYRE_PRESSURE_LR", "TYRE_PRESSURE_2", "PRESSURE_RL", "TIRE_PRESSURE_LR"],
    "pressure_rr": ["PRESSURE_RR", "TYRE_PRESSURE_RR", "TYRE_PRESSURE_3", "PRESSURE_RR", "TIRE_PRESSURE_RR"],
    
    # Camber
    "camber_lf": ["CAMBER_LF", "CAMBER_ANGLE_LF", "CAMBER_FL", "CAMBER_0", "FRONT_CAMBER_L"],
    "camber_rf": ["CAMBER_RF", "CAMBER_ANGLE_RF", "CAMBER_FR", "CAMBER_1", "FRONT_CAMBER_R"],
    "camber_lr": ["CAMBER_LR", "CAMBER_ANGLE_LR", "CAMBER_RL", "CAMBER_2", "REAR_CAMBER_L"],
    "camber_rr": ["CAMBER_RR", "CAMBER_ANGLE_RR", "CAMBER_RR", "CAMBER_3", "REAR_CAMBER_R"],
    
    # Toe
    "toe_lf": ["TOE_OUT_LF", "TOE_LF", "TOE_ANGLE_LF", "TOE_FL", "TOE_0", "FRONT_TOE_L"],
    "toe_rf": ["TOE_OUT_RF", "TOE_RF", "TOE_ANGLE_RF", "TOE_FR", "TOE_1", "FRONT_TOE_R"],
    "toe_lr": ["TOE_OUT_LR", "TOE_LR", "TOE_ANGLE_LR", "TOE_RL", "TOE_2", "REAR_TOE_L"],
    "toe_rr": ["TOE_OUT_RR", "TOE_RR", "TOE_ANGLE_RR", "TOE_RR", "TOE_3", "REAR_TOE_R"],
    
    # Springs
    "spring_lf": ["SPRING_RATE_LF", "SPRING_LF", "SPRING_RATE_FL", "SPRING_0", "FRONT_SPRING_L", "ROD_LENGTH_LF"],
    "spring_rf": ["SPRING_RATE_RF", "SPRING_RF", "SPRING_RATE_FR", "SPRING_1", "FRONT_SPRING_R", "ROD_LENGTH_RF"],
    "spring_lr": ["SPRING_RATE_LR", "SPRING_LR", "SPRING_RATE_RL", "SPRING_2", "REAR_SPRING_L", "ROD_LENGTH_LR"],
    "spring_rr": ["SPRING_RATE_RR", "SPRING_RR", "SPRING_RATE_RR", "SPRING_3", "REAR_SPRING_R", "ROD_LENGTH_RR"],
    
    # Ride Height
    "ride_height_lf": ["ROD_LENGTH_LF", "RIDE_HEIGHT_LF", "HEIGHT_LF", "FRONT_HEIGHT_L", "PACKER_LF"],
    "ride_height_rf": ["ROD_LENGTH_RF", "RIDE_HEIGHT_RF", "HEIGHT_RF", "FRONT_HEIGHT_R", "PACKER_RF"],
    "ride_height_lr": ["ROD_LENGTH_LR", "RIDE_HEIGHT_LR", "HEIGHT_LR", "REAR_HEIGHT_L", "PACKER_LR"],
    "ride_height_rr": ["ROD_LENGTH_RR", "RIDE_HEIGHT_RR", "HEIGHT_RR", "REAR_HEIGHT_R", "PACKER_RR"],
    
    # Dampers - Bump
    "damp_bump_lf": ["DAMP_BUMP_LF", "BUMP_LF", "SLOW_BUMP_LF", "DAMPER_BUMP_LF", "DAMPER_0_BUMP"],
    "damp_bump_rf": ["DAMP_BUMP_RF", "BUMP_RF", "SLOW_BUMP_RF", "DAMPER_BUMP_RF", "DAMPER_1_BUMP"],
    "damp_bump_lr": ["DAMP_BUMP_LR", "BUMP_LR", "SLOW_BUMP_LR", "DAMPER_BUMP_LR", "DAMPER_2_BUMP"],
    "damp_bump_rr": ["DAMP_BUMP_RR", "BUMP_RR", "SLOW_BUMP_RR", "DAMPER_BUMP_RR", "DAMPER_3_BUMP"],
    
    # Dampers - Rebound
    "damp_rebound_lf": ["DAMP_REBOUND_LF", "REBOUND_LF", "SLOW_REBOUND_LF", "DAMPER_REBOUND_LF", "DAMPER_0_REBOUND"],
    "damp_rebound_rf": ["DAMP_REBOUND_RF", "REBOUND_RF", "SLOW_REBOUND_RF", "DAMPER_REBOUND_RF", "DAMPER_1_REBOUND"],
    "damp_rebound_lr": ["DAMP_REBOUND_LR", "REBOUND_LR", "SLOW_REBOUND_LR", "DAMPER_REBOUND_LR", "DAMPER_2_REBOUND"],
    "damp_rebound_rr": ["DAMP_REBOUND_RR", "REBOUND_RR", "SLOW_REBOUND_RR", "DAMPER_REBOUND_RR", "DAMPER_3_REBOUND"],
    
    # Dampers - Fast Bump
    "damp_fast_bump_lf": ["DAMP_FAST_BUMP_LF", "FAST_BUMP_LF", "DAMPER_FAST_BUMP_LF"],
    "damp_fast_bump_rf": ["DAMP_FAST_BUMP_RF", "FAST_BUMP_RF", "DAMPER_FAST_BUMP_RF"],
    "damp_fast_bump_lr": ["DAMP_FAST_BUMP_LR", "FAST_BUMP_LR", "DAMPER_FAST_BUMP_LR"],
    "damp_fast_bump_rr": ["DAMP_FAST_BUMP_RR", "FAST_BUMP_RR", "DAMPER_FAST_BUMP_RR"],
    
    # Dampers - Fast Rebound
    "damp_fast_rebound_lf": ["DAMP_FAST_REBOUND_LF", "FAST_REBOUND_LF", "DAMPER_FAST_REBOUND_LF"],
    "damp_fast_rebound_rf": ["DAMP_FAST_REBOUND_RF", "FAST_REBOUND_RF", "DAMPER_FAST_REBOUND_RF"],
    "damp_fast_rebound_lr": ["DAMP_FAST_REBOUND_LR", "FAST_REBOUND_LR", "DAMPER_FAST_REBOUND_LR"],
    "damp_fast_rebound_rr": ["DAMP_FAST_REBOUND_RR", "FAST_REBOUND_RR", "DAMPER_FAST_REBOUND_RR"],
    
    # ARB (Anti-Roll Bar)
    "arb_front": ["ARB_FRONT", "FRONT_ARB", "ANTIROLL_FRONT", "SWAY_BAR_FRONT", "ARB_0"],
    "arb_rear": ["ARB_REAR", "REAR_ARB", "ANTIROLL_REAR", "SWAY_BAR_REAR", "ARB_1"],
    
    # Differential
    "diff_power": ["POWER", "DIFF_POWER", "LOCK_POWER", "ACCEL_LOCK", "DIFF_LOCK_POWER"],
    "diff_coast": ["COAST", "DIFF_COAST", "LOCK_COAST", "DECEL_LOCK", "DIFF_LOCK_COAST"],
    "diff_preload": ["PRELOAD", "DIFF_PRELOAD", "DIFF_PRELOAD_NM"],
    
    # Brakes
    "brake_bias": ["FRONT_BIAS", "BRAKE_BIAS", "BIAS", "BRAKE_BALANCE", "FRONT_BRAKE_BIAS"],
    "brake_power": ["BRAKE_POWER_MULT", "BRAKE_POWER", "BRAKE_FORCE"],
    
    # Aero - Front Wing
    "wing_front": ["WING_0", "FRONT_WING", "FWING", "WING_FRONT", "AERO_FRONT", "SPLITTER"],
    
    # Aero - Rear Wing
    "wing_rear": ["WING_1", "REAR_WING", "RWING", "WING_REAR", "AERO_REAR", "WING_2", "SPOILER", "WING"],
    
    # Fuel
    "fuel": ["FUEL", "FUEL_LOAD", "FUEL_LEVEL"],
    
    # Tyres compound
    "tyres": ["TYRES", "TYRE_COMPOUND", "COMPOUND", "TIRE_COMPOUND"],
    
    # Caster
    "caster_lf": ["CASTER_LF", "CASTER_FL", "FRONT_CASTER_L"],
    "caster_rf": ["CASTER_RF", "CASTER_FR", "FRONT_CASTER_R"],
}


class DynamicMapper:
    """
    Universal parameter mapper that adapts to any car.
    
    Instead of using fixed parameter names, this class:
    1. Reads existing setup files (last.ini or default)
    2. Detects which parameters are available
    3. Creates a dynamic mapping for injection
    """
    
    def __init__(self, setups_path: Optional[Path] = None):
        """
        Initialize dynamic mapper.
        
        Args:
            setups_path: Path to AC setups folder (Documents/Assetto Corsa/setups)
        """
        self.setups_path = setups_path
        self._cache: Dict[str, Dict[str, str]] = {}  # car_id -> mapping
    
    def set_setups_path(self, path: Path):
        """Set the setups path."""
        self.setups_path = path
    
    def get_car_mapping(self, car_id: str, force_refresh: bool = False) -> Dict[str, str]:
        """
        Get parameter mapping for a specific car.
        
        Args:
            car_id: Car identifier
            force_refresh: Force re-detection even if cached
        
        Returns:
            Dict mapping our internal names to AC parameter names
            Example: {"pressure_lf": "PRESSURE_LF", "wing_rear": "WING_1"}
        """
        if not force_refresh and car_id in self._cache:
            return self._cache[car_id]
        
        # Detect available parameters
        available_params = self._detect_available_parameters(car_id)
        
        # Build mapping
        mapping = self._build_mapping(available_params)
        
        # Cache it
        self._cache[car_id] = mapping
        
        print(f"[DYNAMIC MAPPER] Detected {len(mapping)} parameters for {car_id}")
        
        return mapping
    
    def _detect_available_parameters(self, car_id: str) -> List[str]:
        """
        Detect all available parameters for a car by reading existing setups.
        
        Returns:
            List of parameter names found in setup files
        """
        available = []
        
        if not self.setups_path:
            print("[DYNAMIC MAPPER] Warning: setups_path not set")
            return available
        
        car_dir = self.setups_path / car_id
        
        if not car_dir.exists():
            print(f"[DYNAMIC MAPPER] No setup folder for {car_id}")
            return available
        
        # Search for setup files
        setup_files = []
        
        # Priority 1: generic/last.ini
        generic_last = car_dir / "generic" / "last.ini"
        if generic_last.exists():
            setup_files.append(generic_last)
        
        # Priority 2: Any last.ini in track folders
        for track_dir in car_dir.iterdir():
            if track_dir.is_dir():
                last_ini = track_dir / "last.ini"
                if last_ini.exists():
                    setup_files.append(last_ini)
                    break  # One is enough
        
        # Priority 3: Any .ini file
        if not setup_files:
            for ini_file in car_dir.rglob("*.ini"):
                setup_files.append(ini_file)
                if len(setup_files) >= 3:
                    break
        
        # Parse all found files
        for setup_file in setup_files:
            params = self._parse_setup_file(setup_file)
            for param in params:
                if param not in available:
                    available.append(param)
        
        print(f"[DYNAMIC MAPPER] Found {len(available)} unique parameters in {len(setup_files)} files")
        
        return available
    
    def _parse_setup_file(self, file_path: Path) -> List[str]:
        """
        Parse an AC setup file and extract all parameter names.
        
        AC format:
        [PARAMETER_NAME]
        VALUE=123
        
        Returns:
            List of parameter names (section headers)
        """
        params = []
        
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = file_path.read_text(encoding="utf-16")
            except:
                try:
                    content = file_path.read_text(encoding="latin-1")
                except:
                    return params
        
        # Find all [SECTION] headers
        pattern = r'\[([A-Z0-9_]+)\]'
        matches = re.findall(pattern, content)
        
        for match in matches:
            # Skip meta sections
            if match in ["CAR", "__EXT_PATCH", "VERSION", "INFO"]:
                continue
            params.append(match)
        
        return params
    
    def _build_mapping(self, available_params: List[str]) -> Dict[str, str]:
        """
        Build mapping from our internal names to detected AC parameter names.
        
        Args:
            available_params: List of parameters found in car's setup files
        
        Returns:
            Dict mapping internal names to AC names
        """
        mapping = {}
        
        for internal_name, possible_names in PARAMETER_CATEGORIES.items():
            for ac_name in possible_names:
                if ac_name in available_params:
                    mapping[internal_name] = ac_name
                    break
        
        return mapping
    
    def get_ac_param_name(self, car_id: str, internal_name: str) -> Optional[str]:
        """
        Get the AC parameter name for a given internal name.
        
        Args:
            car_id: Car identifier
            internal_name: Our internal name (e.g., "pressure_lf", "wing_rear")
        
        Returns:
            AC parameter name or None if not available
        """
        mapping = self.get_car_mapping(car_id)
        return mapping.get(internal_name)
    
    def is_parameter_available(self, car_id: str, internal_name: str) -> bool:
        """Check if a parameter is available for a car."""
        return self.get_ac_param_name(car_id, internal_name) is not None
    
    def get_available_aero_params(self, car_id: str) -> Dict[str, str]:
        """
        Get all available aero parameters for a car.
        
        Returns:
            Dict of available aero params {"wing_front": "WING_0", "wing_rear": "WING_1"}
        """
        mapping = self.get_car_mapping(car_id)
        aero_params = {}
        
        for key in ["wing_front", "wing_rear"]:
            if key in mapping:
                aero_params[key] = mapping[key]
        
        return aero_params
    
    def get_mapping_summary(self, car_id: str) -> str:
        """
        Get a human-readable summary of the mapping for a car.
        
        Returns:
            Formatted string showing all mappings
        """
        mapping = self.get_car_mapping(car_id)
        
        lines = [
            f"=== PARAMETER MAPPING FOR {car_id} ===",
            f"Total parameters detected: {len(mapping)}",
            ""
        ]
        
        # Group by category
        categories = {
            "Tyres": ["pressure_lf", "pressure_rf", "pressure_lr", "pressure_rr", "tyres"],
            "Alignment": ["camber_lf", "camber_rf", "camber_lr", "camber_rr", 
                         "toe_lf", "toe_rf", "toe_lr", "toe_rr",
                         "caster_lf", "caster_rf"],
            "Suspension": ["spring_lf", "spring_rf", "spring_lr", "spring_rr",
                          "ride_height_lf", "ride_height_rf", "ride_height_lr", "ride_height_rr"],
            "Dampers": ["damp_bump_lf", "damp_bump_rf", "damp_bump_lr", "damp_bump_rr",
                       "damp_rebound_lf", "damp_rebound_rf", "damp_rebound_lr", "damp_rebound_rr",
                       "damp_fast_bump_lf", "damp_fast_bump_rf", "damp_fast_bump_lr", "damp_fast_bump_rr",
                       "damp_fast_rebound_lf", "damp_fast_rebound_rf", "damp_fast_rebound_lr", "damp_fast_rebound_rr"],
            "ARB": ["arb_front", "arb_rear"],
            "Differential": ["diff_power", "diff_coast", "diff_preload"],
            "Brakes": ["brake_bias", "brake_power"],
            "Aero": ["wing_front", "wing_rear"],
            "Other": ["fuel"]
        }
        
        for cat_name, params in categories.items():
            found = [(p, mapping[p]) for p in params if p in mapping]
            missing = [p for p in params if p not in mapping]
            
            if found or missing:
                lines.append(f"[{cat_name}]")
                for internal, ac in found:
                    lines.append(f"  ✓ {internal} → {ac}")
                for internal in missing:
                    lines.append(f"  ✗ {internal} (not available)")
                lines.append("")
        
        return "\n".join(lines)
    
    def clear_cache(self):
        """Clear the mapping cache."""
        self._cache.clear()
    
    def export_mapping(self, car_id: str, file_path: Path):
        """Export mapping to a JSON file for debugging."""
        import json
        
        mapping = self.get_car_mapping(car_id)
        
        data = {
            "car_id": car_id,
            "mapping": mapping,
            "summary": {
                "total_params": len(mapping),
                "has_aero": "wing_rear" in mapping or "wing_front" in mapping,
                "has_diff": "diff_power" in mapping,
                "has_fast_dampers": "damp_fast_bump_lf" in mapping
            }
        }
        
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
# VALUE DETECTION - Detect if car uses clicks or absolute values
# ═══════════════════════════════════════════════════════════════════════════

class ValueTypeDetector:
    """
    Detects whether a car uses click-based or absolute values for each parameter.
    
    Click-based: Small integers (0-30) representing slider positions
    Absolute: Real physical values (N/m, degrees, PSI)
    """
    
    # Thresholds for detection
    THRESHOLDS = {
        "spring": 1000,      # < 1000 = clicks, > 1000 = N/m
        "damper": 100,       # < 100 = clicks, > 100 = N/m/s
        "arb": 50,           # < 50 = clicks, > 50 = N/mm
        "ride_height": 200,  # < 200 = mm (absolute), always absolute
        "camber": 20,        # < 20 = degrees×10, > 20 = clicks (rare)
        "toe": 50,           # < 50 = degrees×10, > 50 = degrees×100
        "pressure": 50,      # Always PSI (absolute)
        "diff": 100,         # Always percentage (absolute)
        "brake": 100,        # Always percentage (absolute)
        "wing": 50,          # < 50 = clicks, > 50 = degrees (rare)
    }
    
    def __init__(self, setups_path: Optional[Path] = None):
        self.setups_path = setups_path
        self._cache: Dict[str, Dict[str, str]] = {}  # car_id -> {param: "clicks"|"absolute"}
    
    def set_setups_path(self, path: Path):
        self.setups_path = path
    
    def detect_value_types(self, car_id: str) -> Dict[str, str]:
        """
        Detect value types for all parameters of a car.
        
        Returns:
            Dict mapping parameter categories to "clicks" or "absolute"
        """
        if car_id in self._cache:
            return self._cache[car_id]
        
        # Read a setup file to get actual values
        values = self._read_setup_values(car_id)
        
        # Detect types
        types = {}
        
        # Springs
        spring_val = values.get("SPRING_RATE_LF") or values.get("SPRING_LF") or values.get("SPRING_0")
        if spring_val is not None:
            types["spring"] = "clicks" if spring_val < self.THRESHOLDS["spring"] else "absolute"
        
        # Dampers
        damp_val = values.get("DAMP_BUMP_LF") or values.get("BUMP_LF") or values.get("DAMPER_BUMP_LF")
        if damp_val is not None:
            types["damper"] = "clicks" if damp_val < self.THRESHOLDS["damper"] else "absolute"
        
        # ARB
        arb_val = values.get("ARB_FRONT") or values.get("FRONT_ARB")
        if arb_val is not None:
            types["arb"] = "clicks" if arb_val < self.THRESHOLDS["arb"] else "absolute"
        
        # Wing
        wing_val = values.get("WING_0") or values.get("WING_1") or values.get("REAR_WING")
        if wing_val is not None:
            types["wing"] = "clicks" if wing_val < self.THRESHOLDS["wing"] else "absolute"
        
        # These are typically always absolute
        types["ride_height"] = "absolute"  # mm
        types["pressure"] = "absolute"     # PSI
        types["diff"] = "absolute"         # percentage
        types["brake"] = "absolute"        # percentage
        types["camber"] = "absolute"       # degrees × 10
        types["toe"] = "absolute"          # degrees × 10 or × 100
        
        self._cache[car_id] = types
        
        print(f"[VALUE DETECTOR] {car_id}: spring={types.get('spring', 'unknown')}, "
              f"damper={types.get('damper', 'unknown')}, wing={types.get('wing', 'unknown')}")
        
        return types
    
    def _read_setup_values(self, car_id: str) -> Dict[str, int]:
        """Read actual values from a setup file."""
        values = {}
        
        if not self.setups_path:
            return values
        
        car_dir = self.setups_path / car_id
        if not car_dir.exists():
            return values
        
        # Find a setup file
        setup_file = None
        for ini in car_dir.rglob("*.ini"):
            setup_file = ini
            break
        
        if not setup_file:
            return values
        
        # Parse it
        try:
            content = setup_file.read_text(encoding="utf-8")
        except:
            return values
        
        current_section = None
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
            elif line.startswith("VALUE=") and current_section:
                try:
                    value = int(line.split("=")[1])
                    values[current_section] = value
                except:
                    pass
        
        return values
    
    def is_click_based(self, car_id: str, param_category: str) -> bool:
        """Check if a parameter category uses clicks for a car."""
        types = self.detect_value_types(car_id)
        return types.get(param_category, "absolute") == "clicks"
    
    def clear_cache(self):
        """Clear the detection cache."""
        self._cache.clear()
