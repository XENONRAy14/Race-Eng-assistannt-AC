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
        
        # Convert setup to INI content
        ini_content = self._setup_to_ini(setup)
        
        # Save to generic folder (always visible in AC)
        generic_dir = self.base_path / car_id / "generic"
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
            return True, f"Setup saved to generic: {generic_path}", generic_path
        
        # Write file
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(ini_content)
            
            return True, f"Setup saved: {file_path}", file_path
        
        except (PermissionError, OSError) as e:
            return False, f"Cannot write file: {e}", None
    
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
        behavior_clean = behavior.replace(" ", "_").lower()
        
        return f"rea_{behavior_clean}_{timestamp}"
    
    def _setup_to_ini(self, setup: Setup) -> str:
        """Convert a Setup object to AC INI format string."""
        # AC format: each parameter is its own section with VALUE=
        lines = []
        
        # Mapping from our internal format to AC format
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
            ("SUSPENSION", "SPRING_RATE_LF"): "SPRING_RATE_LF",
            ("SUSPENSION", "SPRING_RATE_RF"): "SPRING_RATE_RF",
            ("SUSPENSION", "SPRING_RATE_LR"): "SPRING_RATE_LR",
            ("SUSPENSION", "SPRING_RATE_RR"): "SPRING_RATE_RR",
            ("SUSPENSION", "DAMP_BUMP_LF"): "DAMP_BUMP_LF",
            ("SUSPENSION", "DAMP_BUMP_RF"): "DAMP_BUMP_RF",
            ("SUSPENSION", "DAMP_BUMP_LR"): "DAMP_BUMP_LR",
            ("SUSPENSION", "DAMP_BUMP_RR"): "DAMP_BUMP_RR",
            ("SUSPENSION", "DAMP_REBOUND_LF"): "DAMP_REBOUND_LF",
            ("SUSPENSION", "DAMP_REBOUND_RF"): "DAMP_REBOUND_RF",
            ("SUSPENSION", "DAMP_REBOUND_LR"): "DAMP_REBOUND_LR",
            ("SUSPENSION", "DAMP_REBOUND_RR"): "DAMP_REBOUND_RR",
            ("SUSPENSION", "RIDE_HEIGHT_LF"): "ROD_LENGTH_LF",
            ("SUSPENSION", "RIDE_HEIGHT_RF"): "ROD_LENGTH_RF",
            ("SUSPENSION", "RIDE_HEIGHT_LR"): "ROD_LENGTH_LR",
            ("SUSPENSION", "RIDE_HEIGHT_RR"): "ROD_LENGTH_RR",
            # Differential
            ("DIFFERENTIAL", "POWER"): "DIFF_POWER",
            ("DIFFERENTIAL", "COAST"): "DIFF_COAST",
            ("DIFFERENTIAL", "PRELOAD"): "DIFF_PRELOAD",
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
        
        written_params = set()
        
        # Write each parameter as its own section
        for section_name, section in setup.sections.items():
            for key, value in section.values.items():
                # Get AC parameter name
                ac_param = param_mapping.get((section_name, key))
                if not ac_param:
                    # Try direct key name
                    ac_param = key
                
                if ac_param in written_params:
                    continue
                written_params.add(ac_param)
                
                # Format value - AC uses integers for most values
                if isinstance(value, float):
                    # Convert to int for AC (it uses slider indices, not actual values)
                    formatted_value = str(int(round(value)))
                else:
                    formatted_value = str(value)
                
                lines.append(f"[{ac_param}]")
                lines.append(f"VALUE={formatted_value}")
                lines.append("")
        
        # Add car model section
        if setup.car_id:
            lines.append("[CAR]")
            lines.append(f"MODEL={setup.car_id}")
            lines.append("")
        
        return "\n".join(lines)
    
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
