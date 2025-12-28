"""
Clicks Converter V2.2 - Convert physical values to AC click indices.
Uses linear interpolation based on car-specific data.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


# ═══════════════════════════════════════════════════════════════════════════
# DEFAULT RANGES - Used when car-specific data is not available
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ParameterRange:
    """Range definition for a parameter."""
    min_value: float      # Minimum physical value
    max_value: float      # Maximum physical value
    max_clicks: int       # Number of click positions (0 to max_clicks)
    unit: str             # Unit for display


# Default ranges by car category
DEFAULT_RANGES = {
    # GT3 / Race cars (click-based)
    "gt": {
        "spring_front": ParameterRange(80000, 200000, 15, "N/m"),
        "spring_rear": ParameterRange(80000, 200000, 15, "N/m"),
        "damper_bump": ParameterRange(1500, 6000, 15, "N/m/s"),
        "damper_rebound": ParameterRange(3000, 12000, 15, "N/m/s"),
        "damper_fast_bump": ParameterRange(1000, 4000, 15, "N/m/s"),
        "damper_fast_rebound": ParameterRange(2000, 8000, 15, "N/m/s"),
        "arb": ParameterRange(0, 10, 10, "clicks"),
        "wing": ParameterRange(0, 10, 10, "clicks"),
    },
    
    # Formula cars (click-based, stiffer)
    "formula": {
        "spring_front": ParameterRange(120000, 300000, 20, "N/m"),
        "spring_rear": ParameterRange(120000, 300000, 20, "N/m"),
        "damper_bump": ParameterRange(2000, 8000, 20, "N/m/s"),
        "damper_rebound": ParameterRange(4000, 16000, 20, "N/m/s"),
        "damper_fast_bump": ParameterRange(1500, 6000, 20, "N/m/s"),
        "damper_fast_rebound": ParameterRange(3000, 12000, 20, "N/m/s"),
        "arb": ParameterRange(0, 15, 15, "clicks"),
        "wing": ParameterRange(0, 20, 20, "clicks"),
    },
    
    # Prototype / LMP (click-based, very stiff)
    "prototype": {
        "spring_front": ParameterRange(150000, 350000, 20, "N/m"),
        "spring_rear": ParameterRange(150000, 350000, 20, "N/m"),
        "damper_bump": ParameterRange(2500, 10000, 20, "N/m/s"),
        "damper_rebound": ParameterRange(5000, 20000, 20, "N/m/s"),
        "damper_fast_bump": ParameterRange(2000, 8000, 20, "N/m/s"),
        "damper_fast_rebound": ParameterRange(4000, 16000, 20, "N/m/s"),
        "arb": ParameterRange(0, 15, 15, "clicks"),
        "wing": ParameterRange(0, 25, 25, "clicks"),
    },
    
    # Street cars (absolute values, softer)
    "street": {
        "spring_front": ParameterRange(25000, 80000, 0, "N/m"),  # 0 clicks = absolute
        "spring_rear": ParameterRange(25000, 80000, 0, "N/m"),
        "damper_bump": ParameterRange(1000, 4000, 0, "N/m/s"),
        "damper_rebound": ParameterRange(2000, 8000, 0, "N/m/s"),
        "arb": ParameterRange(0, 50000, 0, "N/mm"),
        "wing": ParameterRange(0, 5, 5, "clicks"),  # If available
    },
    
    # Drift cars (mixed)
    "drift": {
        "spring_front": ParameterRange(40000, 120000, 10, "N/m"),
        "spring_rear": ParameterRange(30000, 100000, 10, "N/m"),
        "damper_bump": ParameterRange(1200, 5000, 10, "N/m/s"),
        "damper_rebound": ParameterRange(2500, 10000, 10, "N/m/s"),
        "arb": ParameterRange(0, 8, 8, "clicks"),
        "wing": ParameterRange(0, 5, 5, "clicks"),
    },
    
    # Vintage cars (soft, often absolute)
    "vintage": {
        "spring_front": ParameterRange(20000, 60000, 0, "N/m"),
        "spring_rear": ParameterRange(20000, 60000, 0, "N/m"),
        "damper_bump": ParameterRange(800, 3000, 0, "N/m/s"),
        "damper_rebound": ParameterRange(1500, 6000, 0, "N/m/s"),
        "arb": ParameterRange(0, 5, 5, "clicks"),
        "wing": ParameterRange(0, 0, 0, "N/A"),  # No aero
    },
}


class ClicksConverter:
    """
    Converts physical values to AC click indices using linear interpolation.
    
    Formula: Click = (Value - Min) / Step_Size
    Where: Step_Size = (Max - Min) / Max_Clicks
    
    Example:
        Spring rate = 154,687 N/m
        Range: 80,000 - 200,000 N/m in 15 clicks
        Step size = (200,000 - 80,000) / 15 = 8,000 N/m per click
        Click = (154,687 - 80,000) / 8,000 = 9.34 → Click 9
    """
    
    def __init__(self):
        self._car_ranges: Dict[str, Dict[str, ParameterRange]] = {}
    
    def set_car_ranges(self, car_id: str, ranges: Dict[str, ParameterRange]):
        """Set custom ranges for a specific car."""
        self._car_ranges[car_id] = ranges
    
    def get_ranges(self, car_id: str, category: str) -> Dict[str, ParameterRange]:
        """
        Get parameter ranges for a car.
        
        Args:
            car_id: Car identifier
            category: Car category (gt, formula, street, etc.)
        
        Returns:
            Dict of parameter ranges
        """
        # Check for car-specific ranges first
        if car_id in self._car_ranges:
            return self._car_ranges[car_id]
        
        # Fall back to category defaults
        return DEFAULT_RANGES.get(category, DEFAULT_RANGES["street"])
    
    def convert_to_clicks(
        self,
        value: float,
        param_type: str,
        category: str,
        car_id: Optional[str] = None
    ) -> Tuple[int, bool, str]:
        """
        Convert a physical value to AC click index.
        
        Args:
            value: Physical value (N/m, N/m/s, etc.)
            param_type: Parameter type (spring_front, damper_bump, etc.)
            category: Car category (gt, formula, street, etc.)
            car_id: Optional car ID for car-specific ranges
        
        Returns:
            Tuple of (click_value, is_click_based, conversion_info)
        """
        ranges = self.get_ranges(car_id, category) if car_id else DEFAULT_RANGES.get(category, DEFAULT_RANGES["street"])
        
        if param_type not in ranges:
            # No range defined - return value as-is (rounded)
            return int(round(value)), False, "No range defined, using raw value"
        
        param_range = ranges[param_type]
        
        # Check if this is click-based (max_clicks > 0)
        if param_range.max_clicks == 0:
            # Absolute value - just clamp and return
            clamped = max(param_range.min_value, min(param_range.max_value, value))
            return int(round(clamped)), False, f"Absolute value, clamped to [{param_range.min_value}, {param_range.max_value}]"
        
        # Click-based - calculate click index
        step_size = (param_range.max_value - param_range.min_value) / param_range.max_clicks
        
        if step_size <= 0:
            return 0, True, "Invalid step size"
        
        # Calculate click
        click = (value - param_range.min_value) / step_size
        
        # Clamp to valid range
        click = max(0, min(param_range.max_clicks, click))
        
        # Round to nearest integer
        click_int = int(round(click))
        
        # Calculate actual value this click represents (for logging)
        actual_value = param_range.min_value + (click_int * step_size)
        
        info = (f"Interpolated: {value:.0f} {param_range.unit} → Click {click_int} "
                f"(actual: {actual_value:.0f} {param_range.unit}, "
                f"range: {param_range.min_value:.0f}-{param_range.max_value:.0f}, "
                f"step: {step_size:.0f})")
        
        return click_int, True, info
    
    def convert_spring(self, value_nm: float, position: str, category: str, car_id: Optional[str] = None) -> Tuple[int, bool, str]:
        """
        Convert spring rate from N/m to clicks.
        
        Args:
            value_nm: Spring rate in N/m
            position: "front" or "rear"
            category: Car category
            car_id: Optional car ID
        
        Returns:
            Tuple of (click_value, is_click_based, conversion_info)
        """
        param_type = f"spring_{position}"
        return self.convert_to_clicks(value_nm, param_type, category, car_id)
    
    def convert_damper(self, value_nms: float, damper_type: str, category: str, car_id: Optional[str] = None) -> Tuple[int, bool, str]:
        """
        Convert damper rate from N/m/s to clicks.
        
        Args:
            value_nms: Damper rate in N/m/s
            damper_type: "bump", "rebound", "fast_bump", "fast_rebound"
            category: Car category
            car_id: Optional car ID
        
        Returns:
            Tuple of (click_value, is_click_based, conversion_info)
        """
        param_type = f"damper_{damper_type}"
        return self.convert_to_clicks(value_nms, param_type, category, car_id)
    
    def convert_arb(self, value: float, category: str, car_id: Optional[str] = None) -> Tuple[int, bool, str]:
        """Convert ARB value to clicks."""
        return self.convert_to_clicks(value, "arb", category, car_id)
    
    def convert_wing(self, value: float, category: str, car_id: Optional[str] = None) -> Tuple[int, bool, str]:
        """Convert wing angle to clicks."""
        return self.convert_to_clicks(value, "wing", category, car_id)
    
    def convert_camber(self, degrees: float) -> int:
        """
        Convert camber from degrees to AC format (degrees × 10).
        
        Args:
            degrees: Camber in degrees (e.g., -3.5)
        
        Returns:
            AC value (e.g., -35)
        """
        return int(round(degrees * 10))
    
    def convert_toe(self, degrees: float, scale: int = 10) -> int:
        """
        Convert toe from degrees to AC format.
        
        Args:
            degrees: Toe in degrees (e.g., 0.15)
            scale: Multiplication factor (10 or 100 depending on car)
        
        Returns:
            AC value (e.g., 15 or 150)
        """
        return int(round(degrees * scale))
    
    def convert_pressure(self, psi: float) -> int:
        """
        Convert pressure from PSI to AC format (integer PSI).
        
        Args:
            psi: Pressure in PSI (e.g., 26.5)
        
        Returns:
            AC value (e.g., 26 or 27)
        """
        return int(round(psi))
    
    def convert_diff(self, percentage: float) -> int:
        """
        Convert differential percentage to AC format.
        
        Args:
            percentage: Diff lock percentage (e.g., 65.5)
        
        Returns:
            AC value (e.g., 66)
        """
        return int(round(percentage))
    
    def convert_brake_bias(self, percentage: float) -> int:
        """
        Convert brake bias percentage to AC format.
        
        Args:
            percentage: Front brake bias (e.g., 58.5)
        
        Returns:
            AC value (e.g., 58 or 59)
        """
        return int(round(percentage))


# ═══════════════════════════════════════════════════════════════════════════
# SMART CONVERTER - Combines detection and conversion
# ═══════════════════════════════════════════════════════════════════════════

class SmartConverter:
    """
    Smart converter that automatically detects value types and converts appropriately.
    
    Combines:
    - Value type detection (clicks vs absolute)
    - Linear interpolation for clicks
    - Proper unit conversion for absolute values
    """
    
    def __init__(self):
        self.clicks_converter = ClicksConverter()
        self._detected_types: Dict[str, Dict[str, str]] = {}  # car_id -> {param: type}
    
    def detect_and_convert(
        self,
        car_id: str,
        category: str,
        param_name: str,
        physical_value: float,
        existing_value: Optional[int] = None
    ) -> Tuple[int, str]:
        """
        Detect value type and convert appropriately.
        
        Args:
            car_id: Car identifier
            category: Car category (gt, formula, street, etc.)
            param_name: Parameter name (e.g., "SPRING_RATE_LF")
            physical_value: Our calculated physical value
            existing_value: Existing value from car's setup (for detection)
        
        Returns:
            Tuple of (converted_value, conversion_log)
        """
        # Determine parameter type
        param_type = self._get_param_type(param_name)
        
        if param_type is None:
            # Unknown parameter - return as-is
            return int(round(physical_value)), f"Unknown param type, raw value: {physical_value}"
        
        # Special handling for always-absolute parameters
        if param_type in ["pressure", "diff", "brake_bias"]:
            if param_type == "pressure":
                result = self.clicks_converter.convert_pressure(physical_value)
                return result, f"Pressure: {physical_value:.1f} PSI → {result}"
            elif param_type == "diff":
                result = self.clicks_converter.convert_diff(physical_value)
                return result, f"Diff: {physical_value:.1f}% → {result}"
            elif param_type == "brake_bias":
                result = self.clicks_converter.convert_brake_bias(physical_value)
                return result, f"Brake bias: {physical_value:.1f}% → {result}"
        
        # Camber and Toe - always multiply
        if param_type == "camber":
            result = self.clicks_converter.convert_camber(physical_value)
            return result, f"Camber: {physical_value:.2f}° × 10 → {result}"
        
        if param_type == "toe":
            # Detect scale from existing value
            scale = 100 if existing_value and abs(existing_value) > 50 else 10
            result = self.clicks_converter.convert_toe(physical_value, scale)
            return result, f"Toe: {physical_value:.3f}° × {scale} → {result}"
        
        # Springs and dampers - use interpolation if click-based
        if param_type.startswith("spring"):
            position = "front" if "LF" in param_name or "RF" in param_name or "FL" in param_name or "FR" in param_name else "rear"
            
            # Detect if click-based
            is_clicks = existing_value is not None and existing_value < 1000
            
            if is_clicks:
                result, _, info = self.clicks_converter.convert_spring(physical_value, position, category, car_id)
                return result, info
            else:
                # Absolute value
                result = int(round(physical_value))
                return result, f"Spring (absolute): {physical_value:.0f} N/m → {result}"
        
        if param_type.startswith("damper"):
            # Extract damper type
            if "FAST_BUMP" in param_name:
                damper_type = "fast_bump"
            elif "FAST_REBOUND" in param_name:
                damper_type = "fast_rebound"
            elif "BUMP" in param_name:
                damper_type = "bump"
            else:
                damper_type = "rebound"
            
            # Detect if click-based
            is_clicks = existing_value is not None and existing_value < 100
            
            if is_clicks:
                result, _, info = self.clicks_converter.convert_damper(physical_value, damper_type, category, car_id)
                return result, info
            else:
                # Absolute value
                result = int(round(physical_value))
                return result, f"Damper (absolute): {physical_value:.0f} N/m/s → {result}"
        
        if param_type == "arb":
            is_clicks = existing_value is not None and existing_value < 50
            
            if is_clicks:
                result, _, info = self.clicks_converter.convert_arb(physical_value, category, car_id)
                return result, info
            else:
                result = int(round(physical_value))
                return result, f"ARB (absolute): {physical_value:.0f} → {result}"
        
        if param_type == "wing":
            is_clicks = existing_value is not None and existing_value < 50
            
            if is_clicks:
                result, _, info = self.clicks_converter.convert_wing(physical_value, category, car_id)
                return result, info
            else:
                result = int(round(physical_value))
                return result, f"Wing (absolute): {physical_value:.0f} → {result}"
        
        if param_type == "ride_height":
            # Always mm (absolute)
            result = int(round(physical_value))
            return result, f"Ride height: {physical_value:.0f} mm → {result}"
        
        # Default - return as-is
        return int(round(physical_value)), f"Default conversion: {physical_value} → {int(round(physical_value))}"
    
    def _get_param_type(self, param_name: str) -> Optional[str]:
        """Determine parameter type from name."""
        param_upper = param_name.upper()
        
        if "PRESSURE" in param_upper:
            return "pressure"
        if "CAMBER" in param_upper:
            return "camber"
        if "TOE" in param_upper:
            return "toe"
        if "SPRING" in param_upper or "ROD_LENGTH" in param_upper:
            return "spring"
        if "FAST_BUMP" in param_upper:
            return "damper_fast_bump"
        if "FAST_REBOUND" in param_upper:
            return "damper_fast_rebound"
        if "BUMP" in param_upper:
            return "damper_bump"
        if "REBOUND" in param_upper:
            return "damper_rebound"
        if "ARB" in param_upper or "ANTIROLL" in param_upper or "SWAY" in param_upper:
            return "arb"
        if "WING" in param_upper or "AERO" in param_upper or "SPLITTER" in param_upper or "SPOILER" in param_upper:
            return "wing"
        if "HEIGHT" in param_upper or "PACKER" in param_upper:
            return "ride_height"
        if "POWER" in param_upper and "BRAKE" not in param_upper:
            return "diff"
        if "COAST" in param_upper:
            return "diff"
        if "PRELOAD" in param_upper:
            return "diff"
        if "BIAS" in param_upper or "BALANCE" in param_upper:
            return "brake_bias"
        if "BRAKE" in param_upper:
            return "brake_bias"
        
        return None
