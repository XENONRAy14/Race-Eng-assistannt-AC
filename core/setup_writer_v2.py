"""
Setup Writer V2.2 - Enhanced setup writer with dynamic mapping and smart conversion.
Integrates all V2.2 systems for universal car support.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from models.setup import Setup, SetupSection
from core.dynamic_mapper import DynamicMapper, ValueTypeDetector
from core.clicks_converter import SmartConverter
from core.setup_debug_logger import SetupDebugLogger


class SetupWriterV2:
    """
    Enhanced setup writer with V2.2 features:
    - Dynamic parameter mapping (supports any car/mod)
    - Smart value conversion (clicks vs absolute)
    - Detailed debug logging
    - Proper clamping based on detected limits
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize V2.2 setup writer.
        
        Args:
            base_path: Base path for setups (Documents/Assetto Corsa/setups)
        """
        self.base_path = base_path
        
        # V2.2 components
        self.dynamic_mapper = DynamicMapper(base_path)
        self.value_detector = ValueTypeDetector(base_path)
        self.smart_converter = SmartConverter()
        
        # Debug logger (created per write operation)
        self.logger: Optional[SetupDebugLogger] = None
        self.enable_debug_logging = True
    
    def set_base_path(self, path: Path) -> None:
        """Set the base path for setup files."""
        self.base_path = path
        self.dynamic_mapper.set_setups_path(path)
        self.value_detector.set_setups_path(path)
    
    def write_setup(
        self,
        setup: Setup,
        car_id: str,
        track_id: str,
        category: str = "street",
        filename: Optional[str] = None,
        overwrite: bool = False
    ) -> Tuple[bool, str, Optional[Path]]:
        """
        Write a setup to disk using V2.2 systems.
        
        Args:
            setup: The Setup object to write
            car_id: Car identifier
            track_id: Track identifier
            category: Car category (gt, formula, street, drift, etc.)
            filename: Optional custom filename
            overwrite: Whether to overwrite existing files
        
        Returns:
            Tuple of (success, message, file_path)
        """
        if not self.base_path:
            return False, "Base path not set", None
        
        # Initialize debug logger
        if self.enable_debug_logging:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = self.base_path / car_id / f"debug_{timestamp}.log"
            self.logger = SetupDebugLogger(log_path)
            self.logger.set_metadata(car_id, track_id, setup.behavior or "custom", category)
        
        # Generate filename
        if not filename:
            filename = self._generate_filename(setup)
        if not filename.endswith(".ini"):
            filename += ".ini"
        
        # Step 1: Get dynamic mapping for this car
        print(f"[WRITER V2.2] Getting dynamic mapping for {car_id}...")
        car_mapping = self.dynamic_mapper.get_car_mapping(car_id)
        
        if self.logger:
            for internal, ac_name in car_mapping.items():
                self.logger.log_exported(internal, ac_name, f"Mapped: {internal} → {ac_name}")
        
        # Step 2: Detect value types (clicks vs absolute)
        print(f"[WRITER V2.2] Detecting value types...")
        value_types = self.value_detector.detect_value_types(car_id)
        
        # Step 3: Read existing setup for reference values
        existing_params = self._read_existing_setup(car_id)
        
        # Step 4: Convert our setup values to AC format
        print(f"[WRITER V2.2] Converting values...")
        final_params = self._convert_setup_to_ac(
            setup, car_id, category, car_mapping, existing_params
        )
        
        # Step 5: Build INI content
        ini_content = self._build_ini_content(final_params, car_id)
        
        # Step 6: Save to generic folder
        generic_dir = self.base_path / car_id / "generic"
        generic_path = None
        try:
            generic_dir.mkdir(parents=True, exist_ok=True)
            generic_path = generic_dir / filename
            with open(generic_path, "w", encoding="utf-8") as f:
                f.write(ini_content)
            print(f"[WRITER V2.2] Saved to generic: {generic_path}")
        except (PermissionError, OSError) as e:
            print(f"[WRITER V2.2] Warning: Could not save to generic: {e}")
        
        # Step 7: Save to track-specific folder
        setup_dir = self.base_path / car_id / track_id
        try:
            setup_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            if generic_path:
                return True, f"Setup saved to generic only: {generic_path}", generic_path
            return False, f"Cannot create directory: {e}", None
        
        file_path = setup_dir / filename
        
        if file_path.exists() and not overwrite:
            if generic_path:
                return True, f"Setup saved to generic: {generic_path}", generic_path
            return False, "File exists and overwrite=False", None
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(ini_content)
            print(f"[WRITER V2.2] Saved to track: {file_path}")
        except (PermissionError, OSError) as e:
            if generic_path:
                return True, f"Setup saved to generic only: {generic_path}", generic_path
            return False, f"Cannot write file: {e}", None
        
        # Step 8: Save debug log
        if self.logger and self.enable_debug_logging:
            self.logger.save(format="text")
            print(f"[WRITER V2.2] Debug log saved")
        
        return True, f"Setup saved: {file_path}", file_path
    
    def _convert_setup_to_ac(
        self,
        setup: Setup,
        car_id: str,
        category: str,
        car_mapping: Dict[str, str],
        existing_params: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Convert our internal setup values to AC format.
        
        Uses:
        - Dynamic mapping for parameter names
        - Smart converter for value conversion
        - Existing values for type detection
        """
        final_params = dict(existing_params)  # Start with existing as base
        
        # Internal name to section/key mapping
        internal_to_setup = {
            # Pressures
            "pressure_lf": ("TYRES", "PRESSURE_LF"),
            "pressure_rf": ("TYRES", "PRESSURE_RF"),
            "pressure_lr": ("TYRES", "PRESSURE_LR"),
            "pressure_rr": ("TYRES", "PRESSURE_RR"),
            
            # Camber
            "camber_lf": ("ALIGNMENT", "CAMBER_LF"),
            "camber_rf": ("ALIGNMENT", "CAMBER_RF"),
            "camber_lr": ("ALIGNMENT", "CAMBER_LR"),
            "camber_rr": ("ALIGNMENT", "CAMBER_RR"),
            
            # Toe
            "toe_lf": ("ALIGNMENT", "TOE_LF"),
            "toe_rf": ("ALIGNMENT", "TOE_RF"),
            "toe_lr": ("ALIGNMENT", "TOE_LR"),
            "toe_rr": ("ALIGNMENT", "TOE_RR"),
            
            # Springs
            "spring_lf": ("SUSPENSION", "SPRING_RATE_LF"),
            "spring_rf": ("SUSPENSION", "SPRING_RATE_RF"),
            "spring_lr": ("SUSPENSION", "SPRING_RATE_LR"),
            "spring_rr": ("SUSPENSION", "SPRING_RATE_RR"),
            
            # Ride height
            "ride_height_lf": ("SUSPENSION", "RIDE_HEIGHT_LF"),
            "ride_height_rf": ("SUSPENSION", "RIDE_HEIGHT_RF"),
            "ride_height_lr": ("SUSPENSION", "RIDE_HEIGHT_LR"),
            "ride_height_rr": ("SUSPENSION", "RIDE_HEIGHT_RR"),
            
            # Dampers
            "damp_bump_lf": ("SUSPENSION", "DAMP_BUMP_LF"),
            "damp_bump_rf": ("SUSPENSION", "DAMP_BUMP_RF"),
            "damp_bump_lr": ("SUSPENSION", "DAMP_BUMP_LR"),
            "damp_bump_rr": ("SUSPENSION", "DAMP_BUMP_RR"),
            "damp_rebound_lf": ("SUSPENSION", "DAMP_REBOUND_LF"),
            "damp_rebound_rf": ("SUSPENSION", "DAMP_REBOUND_RF"),
            "damp_rebound_lr": ("SUSPENSION", "DAMP_REBOUND_LR"),
            "damp_rebound_rr": ("SUSPENSION", "DAMP_REBOUND_RR"),
            "damp_fast_bump_lf": ("SUSPENSION", "DAMP_FAST_BUMP_LF"),
            "damp_fast_bump_rf": ("SUSPENSION", "DAMP_FAST_BUMP_RF"),
            "damp_fast_bump_lr": ("SUSPENSION", "DAMP_FAST_BUMP_LR"),
            "damp_fast_bump_rr": ("SUSPENSION", "DAMP_FAST_BUMP_RR"),
            "damp_fast_rebound_lf": ("SUSPENSION", "DAMP_FAST_REBOUND_LF"),
            "damp_fast_rebound_rf": ("SUSPENSION", "DAMP_FAST_REBOUND_RF"),
            "damp_fast_rebound_lr": ("SUSPENSION", "DAMP_FAST_REBOUND_LR"),
            "damp_fast_rebound_rr": ("SUSPENSION", "DAMP_FAST_REBOUND_RR"),
            
            # ARB
            "arb_front": ("ARB", "FRONT"),
            "arb_rear": ("ARB", "REAR"),
            
            # Differential
            "diff_power": ("DIFFERENTIAL", "POWER"),
            "diff_coast": ("DIFFERENTIAL", "COAST"),
            "diff_preload": ("DIFFERENTIAL", "PRELOAD"),
            
            # Brakes
            "brake_bias": ("BRAKES", "FRONT_BIAS"),
            "brake_power": ("BRAKES", "BRAKE_POWER_MULT"),
            
            # Aero
            "wing_front": ("AERO", "WING_FRONT"),
            "wing_rear": ("AERO", "WING_REAR"),
            
            # Fuel
            "fuel": ("FUEL", "FUEL"),
        }
        
        # Process each parameter
        for internal_name, ac_name in car_mapping.items():
            # Get our internal value
            if internal_name not in internal_to_setup:
                continue
            
            section, key = internal_to_setup[internal_name]
            our_value = setup.get_value(section, key, None)
            
            # Also try alternative keys
            if our_value is None:
                our_value = self._get_value_alternatives(setup, section, key)
            
            if our_value is None:
                if self.logger:
                    self.logger.log_ignored(ac_name, f"No value in setup for {section}/{key}")
                continue
            
            # Log calculation
            if self.logger:
                self.logger.log_calculation(ac_name, our_value, "internal", f"From setup {section}/{key}")
            
            # Get existing value for type detection
            existing_value = existing_params.get(ac_name)
            
            # Convert using smart converter
            converted, conversion_log = self.smart_converter.detect_and_convert(
                car_id=car_id,
                category=category,
                param_name=ac_name,
                physical_value=our_value,
                existing_value=existing_value
            )
            
            # Log conversion
            if self.logger:
                self.logger.log_conversion(ac_name, our_value, converted, conversion_log)
            
            # Store final value
            final_params[ac_name] = converted
            
            # Log export
            if self.logger:
                self.logger.log_exported(ac_name, converted, f"[{ac_name}]\nVALUE={converted}")
        
        return final_params
    
    def _get_value_alternatives(self, setup: Setup, section: str, key: str) -> Optional[float]:
        """Try alternative key names."""
        alternatives = {
            "FRONT_BIAS": ["BIAS", "BRAKE_BIAS"],
            "BRAKE_POWER_MULT": ["BRAKE_POWER"],
            "WING_FRONT": ["WING_0", "FWING"],
            "WING_REAR": ["WING_1", "RWING", "WING"],
        }
        
        if key in alternatives:
            for alt in alternatives[key]:
                val = setup.get_value(section, alt, None)
                if val is not None:
                    return val
        
        return None
    
    def _read_existing_setup(self, car_id: str) -> Dict[str, int]:
        """Read existing setup to get reference values."""
        params = {}
        
        if not self.base_path:
            return params
        
        car_dir = self.base_path / car_id
        if not car_dir.exists():
            return params
        
        # Find a setup file
        setup_file = None
        
        # Priority: generic/last.ini
        generic_last = car_dir / "generic" / "last.ini"
        if generic_last.exists():
            setup_file = generic_last
        else:
            # Any last.ini
            for track_dir in car_dir.iterdir():
                if track_dir.is_dir():
                    last_ini = track_dir / "last.ini"
                    if last_ini.exists():
                        setup_file = last_ini
                        break
        
        if not setup_file:
            # Any .ini file
            for ini in car_dir.rglob("*.ini"):
                setup_file = ini
                break
        
        if not setup_file:
            return params
        
        # Parse it
        try:
            content = setup_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = setup_file.read_text(encoding="utf-16")
            except:
                return params
        
        current_section = None
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
            elif line.startswith("VALUE=") and current_section:
                try:
                    value = int(line.split("=")[1])
                    params[current_section] = value
                except:
                    pass
        
        return params
    
    def _build_ini_content(self, params: Dict[str, int], car_id: str) -> str:
        """Build INI file content from parameters."""
        lines = []
        
        # Sort parameters alphabetically
        for param in sorted(params.keys()):
            if param.startswith("_"):
                continue
            value = params[param]
            lines.append(f"[{param}]")
            lines.append(f"VALUE={value}")
            lines.append("")
        
        # Add car model
        lines.append("[CAR]")
        lines.append(f"MODEL={car_id}")
        lines.append("")
        
        # Add CSP version
        lines.append("[__EXT_PATCH]")
        lines.append("VERSION=0.2.5-preview1")
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_filename(self, setup: Setup) -> str:
        """Generate filename for setup."""
        if setup.name:
            name_clean = "".join(c if c.isalnum() or c in "_ -" else "_" for c in setup.name)
            return name_clean.replace(" ", "_").replace("-", "_")
        
        behavior = setup.behavior or "custom"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"rea_v22_{behavior}_{timestamp}"
    
    def get_mapping_summary(self, car_id: str) -> str:
        """Get mapping summary for a car."""
        return self.dynamic_mapper.get_mapping_summary(car_id)
    
    def export_mapping(self, car_id: str, file_path: Path):
        """Export mapping to JSON for debugging."""
        self.dynamic_mapper.export_mapping(car_id, file_path)
