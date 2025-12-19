"""
Setup Writer - Writes setup files to Assetto Corsa.
Converts Setup objects to INI format and saves to disk.
"""

from pathlib import Path
from typing import Optional
from datetime import datetime
import configparser
import shutil

from models.setup import Setup


class SetupWriter:
    """
    Writes car setups to Assetto Corsa setup files.
    Handles INI format conversion and file management.
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize setup writer.
        
        Args:
            base_path: Base path for setups (Documents/Assetto Corsa/setups)
        """
        self.base_path = base_path
    
    def set_base_path(self, path: Path) -> None:
        """Set the base path for setup files."""
        self.base_path = path
    
    def write_setup(
        self,
        setup: Setup,
        car_id: str,
        track_id: str,
        filename: Optional[str] = None,
        overwrite: bool = False
    ) -> tuple[bool, str, Optional[Path]]:
        """
        Write a setup to disk.
        
        This method reads the existing setup for the car first, then only modifies
        parameters that exist for that specific car. This ensures compatibility
        with all cars regardless of their available setup options.
        
        Args:
            setup: The Setup object to write
            car_id: Car identifier
            track_id: Track identifier (can include config like "track/layout")
            filename: Optional custom filename (without extension)
            overwrite: Whether to overwrite existing files
        
        Returns:
            Tuple of (success, message, file_path)
        """
        if not self.base_path:
            return False, "Base path not set", None
        
        # Generate filename
        if not filename:
            filename = self._generate_filename(setup)
        
        # Ensure .ini extension
        if not filename.endswith(".ini"):
            filename += ".ini"
        
        # Read existing setup for this car to get available parameters
        existing_params = self._read_existing_car_setup(car_id)
        
        # Convert setup to INI content, respecting available parameters
        ini_content = self._setup_to_ini_with_base(setup, car_id, existing_params)
        
        # Save to generic folder (always visible in AC)
        generic_dir = self.base_path / car_id / "generic"
        generic_path = None
        try:
            generic_dir.mkdir(parents=True, exist_ok=True)
            generic_path = generic_dir / filename
            with open(generic_path, "w", encoding="utf-8") as f:
                f.write(ini_content)
        except (PermissionError, OSError):
            pass  # Non-critical, continue with track-specific save
        
        # Also save to track-specific folder
        setup_dir = self.base_path / car_id / track_id
        try:
            setup_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            return False, f"Cannot create directory: {e}", None
        
        file_path = setup_dir / filename
        
        # Check for existing file
        if file_path.exists() and not overwrite:
            # Still return success since we saved to generic
            if generic_path:
                return True, f"Setup saved to generic: {generic_path}", generic_path
            return False, "File exists and overwrite=False", None
        
        # Write file
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(ini_content)
            
            return True, f"Setup saved: {file_path}", file_path
        
        except (PermissionError, OSError) as e:
            return False, f"Cannot write file: {e}", None
    
    def _read_existing_car_setup(self, car_id: str) -> dict:
        """
        Read existing setup for a car to determine available parameters.
        
        Looks for last.ini or any existing setup in the car's generic folder.
        Returns a dict of {param_name: current_value} for all available params.
        """
        if not self.base_path:
            return {}
        
        existing_params = {}
        
        # Try to find an existing setup for this car
        generic_dir = self.base_path / car_id / "generic"
        
        # Priority: last.ini first, then any other .ini file
        search_paths = []
        if generic_dir.exists():
            last_ini = generic_dir / "last.ini"
            if last_ini.exists():
                search_paths.append(last_ini)
            # Also check for any other ini files
            search_paths.extend([f for f in generic_dir.glob("*.ini") if f.name != "last.ini"])
        
        # Also check track-specific folders
        car_dir = self.base_path / car_id
        if car_dir.exists():
            for track_dir in car_dir.iterdir():
                if track_dir.is_dir() and track_dir.name != "generic":
                    last_ini = track_dir / "last.ini"
                    if last_ini.exists():
                        search_paths.append(last_ini)
                        break  # One is enough
        
        # Read the first available setup
        for setup_path in search_paths:
            try:
                params = self._parse_ac_setup_file(setup_path)
                if params:
                    existing_params = params
                    break
            except Exception:
                continue
        
        return existing_params
    
    def _parse_ac_setup_file(self, file_path: Path) -> dict:
        """
        Parse an AC setup file and return all parameters with their values.
        
        AC format: [PARAM_NAME]\\nVALUE=<int>
        Returns: {param_name: value}
        """
        params = {}
        
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.strip().split("\n")
            
            current_section = None
            for line in lines:
                line = line.strip()
                if line.startswith("[") and line.endswith("]"):
                    current_section = line[1:-1]
                elif line.startswith("VALUE=") and current_section:
                    try:
                        value = int(line.split("=", 1)[1])
                        params[current_section] = value
                    except (ValueError, IndexError):
                        pass
                elif "=" in line and current_section:
                    # Handle other key=value pairs (like MODEL= in [CAR])
                    key, val = line.split("=", 1)
                    if current_section == "CAR" and key == "MODEL":
                        params["_CAR_MODEL"] = val
        except Exception:
            pass
        
        return params
    
    def _generate_filename(self, setup: Setup) -> str:
        """Generate a filename for the setup."""
        # Use setup name if available, otherwise behavior
        if setup.name:
            # Clean name for filename (remove special chars)
            name_clean = "".join(c if c.isalnum() or c in "_ -" else "_" for c in setup.name)
            name_clean = name_clean.replace(" ", "_").replace("-", "_")
            return name_clean
        
        # Fallback: use behavior and timestamp
        behavior = setup.behavior or "custom"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        behavior_clean = str(behavior).replace(" ", "_").lower()
        
        return f"rea_{behavior_clean}_{timestamp}"
    
    def _setup_to_ini_with_base(self, setup: Setup, car_id: str, existing_params: dict) -> str:
        """Convert a Setup object to AC INI format, using existing car setup as base.
        
        This method only modifies parameters that exist for the specific car.
        If no existing setup is found, it creates a minimal setup with common parameters.
        
        Args:
            setup: Our internal Setup object with desired values
            car_id: The car identifier
            existing_params: Dict of existing parameters from the car's setup
        """
        # Mapping from our internal format to AC parameter names
        param_mapping = {
            # Tyres
            ("TYRES", "PRESSURE_LF"): "PRESSURE_LF",
            ("TYRES", "PRESSURE_RF"): "PRESSURE_RF",
            ("TYRES", "PRESSURE_LR"): "PRESSURE_LR",
            ("TYRES", "PRESSURE_RR"): "PRESSURE_RR",
            # Brakes
            ("BRAKES", "BIAS"): "FRONT_BIAS",
            ("BRAKES", "FRONT_BIAS"): "FRONT_BIAS",
            ("BRAKES", "BRAKE_POWER_MULT"): "BRAKE_POWER_MULT",
            # Suspension
            ("SUSPENSION", "RIDE_HEIGHT_LF"): "ROD_LENGTH_LF",
            ("SUSPENSION", "RIDE_HEIGHT_RF"): "ROD_LENGTH_RF",
            ("SUSPENSION", "RIDE_HEIGHT_LR"): "ROD_LENGTH_LR",
            ("SUSPENSION", "RIDE_HEIGHT_RR"): "ROD_LENGTH_RR",
            ("SUSPENSION", "DAMP_BUMP_LF"): "DAMP_BUMP_LF",
            ("SUSPENSION", "DAMP_BUMP_RF"): "DAMP_BUMP_RF",
            ("SUSPENSION", "DAMP_BUMP_LR"): "DAMP_BUMP_LR",
            ("SUSPENSION", "DAMP_BUMP_RR"): "DAMP_BUMP_RR",
            ("SUSPENSION", "DAMP_REBOUND_LF"): "DAMP_REBOUND_LF",
            ("SUSPENSION", "DAMP_REBOUND_RF"): "DAMP_REBOUND_RF",
            ("SUSPENSION", "DAMP_REBOUND_LR"): "DAMP_REBOUND_LR",
            ("SUSPENSION", "DAMP_REBOUND_RR"): "DAMP_REBOUND_RR",
            # Alignment
            ("ALIGNMENT", "CAMBER_LF"): "CAMBER_LF",
            ("ALIGNMENT", "CAMBER_RF"): "CAMBER_RF",
            ("ALIGNMENT", "CAMBER_LR"): "CAMBER_LR",
            ("ALIGNMENT", "CAMBER_RR"): "CAMBER_RR",
            ("ALIGNMENT", "TOE_LF"): "TOE_OUT_LF",
            ("ALIGNMENT", "TOE_RF"): "TOE_OUT_RF",
            ("ALIGNMENT", "TOE_LR"): "TOE_OUT_LR",
            ("ALIGNMENT", "TOE_RR"): "TOE_OUT_RR",
            # ARB
            ("ARB", "FRONT"): "ARB_FRONT",
            ("ARB", "REAR"): "ARB_REAR",
            # Fuel
            ("FUEL", "FUEL"): "FUEL",
        }
        
        # Build a map of our desired values (AC param name -> our value)
        our_values = {}
        for section_name, section in setup.sections.items():
            for key, value in section.values.items():
                ac_param = param_mapping.get((section_name, key), key)
                our_values[ac_param] = value
        
        # Start with existing params as base, then apply our modifications
        # Only modify params that exist in the car's setup
        final_params = dict(existing_params)
        
        # Apply our values only to parameters that exist for this car
        for ac_param, our_value in our_values.items():
            if ac_param in existing_params:
                # This parameter exists for this car - apply our value
                converted = self._convert_value_for_ac(ac_param, our_value, existing_params.get(ac_param, 0))
                final_params[ac_param] = converted
        
        # If no existing params found, use a minimal common set
        if not existing_params:
            # Common parameters that most cars have
            common_params = [
                "PRESSURE_LF", "PRESSURE_RF", "PRESSURE_LR", "PRESSURE_RR",
                "CAMBER_LF", "CAMBER_RF", "CAMBER_LR", "CAMBER_RR",
                "TOE_OUT_LF", "TOE_OUT_RF", "TOE_OUT_LR", "TOE_OUT_RR",
                "FRONT_BIAS", "BRAKE_POWER_MULT", "FUEL", "TYRES"
            ]
            for param in common_params:
                if param in our_values:
                    final_params[param] = self._convert_value_for_ac(param, our_values[param], 0)
                else:
                    # Use sensible defaults
                    defaults = {
                        "PRESSURE_LF": 26, "PRESSURE_RF": 26, "PRESSURE_LR": 26, "PRESSURE_RR": 26,
                        "CAMBER_LF": -30, "CAMBER_RF": -30, "CAMBER_LR": -20, "CAMBER_RR": -20,
                        "TOE_OUT_LF": 0, "TOE_OUT_RF": 0, "TOE_OUT_LR": 0, "TOE_OUT_RR": 0,
                        "FRONT_BIAS": 60, "BRAKE_POWER_MULT": 100, "FUEL": 30, "TYRES": 0
                    }
                    if param in defaults:
                        final_params[param] = defaults[param]
        
        # Build INI content
        lines = []
        
        # Write parameters in alphabetical order (AC convention)
        for param in sorted(final_params.keys()):
            if param.startswith("_"):  # Skip internal keys like _CAR_MODEL
                continue
            value = final_params[param]
            lines.append(f"[{param}]")
            lines.append(f"VALUE={value}")
            lines.append("")
        
        # Add car model section
        lines.append("[CAR]")
        lines.append(f"MODEL={car_id}")
        lines.append("")
        
        # Add CSP/patch version for compatibility
        lines.append("[__EXT_PATCH]")
        lines.append("VERSION=0.2.5-preview1")
        lines.append("")
        
        return "\n".join(lines)
    
    def _convert_value_for_ac(self, param_name: str, our_value: float, existing_value: int) -> int:
        """Convert our internal value to AC slider index.
        
        Uses the existing value as a reference to understand the scale.
        """
        # Pressure: our value is already in psi (e.g., 26.0)
        if "PRESSURE" in param_name:
            return int(round(our_value))
        
        # Camber: our value is in degrees (e.g., -3.0), AC uses degrees * 10
        if "CAMBER" in param_name:
            return int(round(our_value * 10))
        
        # Toe: our value is in degrees (e.g., 0.1), AC uses degrees * 100 or direct
        if "TOE" in param_name:
            # Check if existing value suggests a different scale
            if abs(existing_value) > 50:
                # Probably using larger scale (degrees * 100)
                return int(round(our_value * 100))
            else:
                return int(round(our_value * 10))
        
        # Dampers: keep relative to existing if possible
        if "DAMP" in param_name:
            # Our value might be in N/m/s, AC uses click indices
            if our_value > 100:
                return int(round(our_value / 500))
            return int(round(our_value))
        
        # ARB: can be in N/mm or as index
        if "ARB" in param_name:
            if existing_value > 1000:
                # Car uses N/mm values
                return int(round(our_value * 1000)) if our_value < 100 else int(round(our_value))
            return int(round(our_value))
        
        # Rod length / ride height: direct mm value
        if "ROD_LENGTH" in param_name or "RIDE_HEIGHT" in param_name:
            return int(round(our_value))
        
        # Brake bias: percentage
        if "BIAS" in param_name or "FRONT_BIAS" in param_name:
            return int(round(our_value))
        
        # Brake power: percentage
        if "BRAKE_POWER" in param_name:
            return int(round(our_value))
        
        # Fuel: liters or percentage
        if "FUEL" in param_name:
            return int(round(our_value))
        
        # Default: round to int
        if isinstance(our_value, float):
            return int(round(our_value))
        return int(our_value)
    
    def _format_value(self, value) -> str:
        """Format a value for INI file."""
        if isinstance(value, float):
            # Use appropriate precision
            if value == int(value):
                return str(int(value))
            return f"{value:.2f}"
        elif isinstance(value, bool):
            return "1" if value else "0"
        else:
            return str(value)
    
    def read_setup(self, file_path: Path) -> Optional[Setup]:
        """
        Read a setup from an INI file.
        
        Args:
            file_path: Path to the setup file
        
        Returns:
            Setup object or None if reading fails
        """
        if not file_path.exists():
            return None
        
        try:
            config = configparser.ConfigParser()
            config.read(file_path, encoding="utf-8")
            
            setup = Setup(name=file_path.stem)
            
            for section_name in config.sections():
                section_values = {}
                
                for key, value in config.items(section_name):
                    # Try to parse as number
                    parsed_value = self._parse_value(value)
                    section_values[key.upper()] = parsed_value
                
                from models.setup import SetupSection
                setup.sections[section_name] = SetupSection(section_name, section_values)
            
            return setup
        
        except (configparser.Error, IOError):
            return None
    
    def _parse_value(self, value: str):
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
        
        # Return as string
        return value
    
    def list_setups(self, car_id: str, track_id: str) -> list[dict]:
        """
        List existing setups for a car/track combination.
        
        Returns:
            List of setup info dictionaries
        """
        if not self.base_path:
            return []
        
        setup_dir = self.base_path / car_id / track_id
        
        if not setup_dir.exists():
            return []
        
        setups = []
        for file_path in setup_dir.glob("*.ini"):
            try:
                stat = file_path.stat()
                setups.append({
                    "filename": file_path.name,
                    "path": file_path,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime),
                    "is_rea": file_path.name.startswith("rea_")
                })
            except OSError:
                continue
        
        # Sort by modification time, newest first
        setups.sort(key=lambda x: x["modified"], reverse=True)
        
        return setups
    
    def delete_setup(self, file_path: Path) -> tuple[bool, str]:
        """
        Delete a setup file.
        
        Returns:
            Tuple of (success, message)
        """
        if not file_path.exists():
            return False, "File does not exist"
        
        try:
            file_path.unlink()
            return True, f"Deleted: {file_path}"
        except (PermissionError, OSError) as e:
            return False, f"Cannot delete file: {e}"
    
    def backup_setup(self, file_path: Path) -> tuple[bool, str, Optional[Path]]:
        """
        Create a backup of a setup file.
        
        Returns:
            Tuple of (success, message, backup_path)
        """
        if not file_path.exists():
            return False, "File does not exist", None
        
        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
        backup_path = file_path.parent / backup_name
        
        try:
            shutil.copy2(file_path, backup_path)
            return True, f"Backup created: {backup_path}", backup_path
        except (PermissionError, OSError) as e:
            return False, f"Cannot create backup: {e}", None
    
    def get_generic_setup_path(self, car_id: str) -> Path:
        """
        Get the path for generic (non-track-specific) setups.
        These are stored in a 'generic' subdirectory.
        """
        if not self.base_path:
            raise ValueError("Base path not set")
        
        return self.base_path / car_id / "generic"
    
    def write_generic_setup(
        self,
        setup: Setup,
        car_id: str,
        filename: Optional[str] = None,
        overwrite: bool = False
    ) -> tuple[bool, str, Optional[Path]]:
        """
        Write a generic (non-track-specific) setup.
        """
        return self.write_setup(
            setup=setup,
            car_id=car_id,
            track_id="generic",
            filename=filename,
            overwrite=overwrite
        )
