"""
Slider Interdependencies V2.2 - Multi-parameter effects for each slider.
Each slider modifies multiple related parameters for a "wow" effect.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from models.setup import Setup


# ═══════════════════════════════════════════════════════════════════════════
# INTERDEPENDENCY DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SliderEffect:
    """Definition of a slider's effect on a parameter."""
    param_section: str      # Setup section (SUSPENSION, ALIGNMENT, etc.)
    param_key: str          # Parameter key
    effect_type: str        # "add", "multiply", "set"
    base_effect: float      # Effect at slider = 1.0
    description: str        # Human-readable description


# Slider definitions with interdependencies
SLIDER_INTERDEPENDENCIES = {
    # ═══════════════════════════════════════════════════════════════════════
    # AERO SLIDER (0.0 = low downforce, 1.0 = high downforce)
    # ═══════════════════════════════════════════════════════════════════════
    "aero": {
        "description": "Downforce level - affects wing, rake, and springs",
        "effects": [
            # Primary: Rear wing angle
            SliderEffect("AERO", "WING_REAR", "add", 8.0, 
                        "Rear wing: +8 clicks at max"),
            SliderEffect("AERO", "WING_FRONT", "add", 4.0,
                        "Front wing: +4 clicks at max (50% of rear for balance)"),
            
            # Secondary: Rake compensation (lower front, raise rear)
            SliderEffect("SUSPENSION", "RIDE_HEIGHT_LF", "add", -5.0,
                        "Front ride height: -5mm at max (increase rake)"),
            SliderEffect("SUSPENSION", "RIDE_HEIGHT_RF", "add", -5.0,
                        "Front ride height: -5mm at max"),
            SliderEffect("SUSPENSION", "RIDE_HEIGHT_LR", "add", 3.0,
                        "Rear ride height: +3mm at max (maintain rake)"),
            SliderEffect("SUSPENSION", "RIDE_HEIGHT_RR", "add", 3.0,
                        "Rear ride height: +3mm at max"),
            
            # Tertiary: Stiffer rear springs to support aero load
            SliderEffect("SUSPENSION", "SPRING_RATE_LR", "multiply", 0.15,
                        "Rear springs: +15% at max (support aero load)"),
            SliderEffect("SUSPENSION", "SPRING_RATE_RR", "multiply", 0.15,
                        "Rear springs: +15% at max"),
            
            # Quaternary: Slightly stiffer rear ARB
            SliderEffect("ARB", "REAR", "multiply", 0.10,
                        "Rear ARB: +10% at max (reduce roll with aero)"),
        ]
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # ROTATION SLIDER (0.0 = understeer, 1.0 = oversteer)
    # ═══════════════════════════════════════════════════════════════════════
    "rotation": {
        "description": "Turn-in behavior - affects toe, ARB, diff, and brake bias",
        "effects": [
            # Primary: Rear toe (toe-out = more rotation)
            SliderEffect("ALIGNMENT", "TOE_LR", "add", 0.4,
                        "Rear toe: +0.4° toe-out at max (more rotation)"),
            SliderEffect("ALIGNMENT", "TOE_RR", "add", 0.4,
                        "Rear toe: +0.4° toe-out at max"),
            
            # Secondary: ARB balance (stiffer rear = more rotation)
            SliderEffect("ARB", "REAR", "multiply", 0.30,
                        "Rear ARB: +30% at max (more rear roll stiffness)"),
            SliderEffect("ARB", "FRONT", "multiply", -0.15,
                        "Front ARB: -15% at max (less front roll stiffness)"),
            
            # Tertiary: Diff coast (less coast lock = more rotation)
            SliderEffect("DIFFERENTIAL", "COAST", "add", -15.0,
                        "Diff coast: -15% at max (less engine braking lock)"),
            
            # Quaternary: Brake bias (less front = more rotation on entry)
            SliderEffect("BRAKES", "FRONT_BIAS", "add", -3.0,
                        "Brake bias: -3% front at max (more rear braking)"),
            
            # Quinary: Slight rear camber reduction (less grip = more rotation)
            SliderEffect("ALIGNMENT", "CAMBER_LR", "add", 0.5,
                        "Rear camber: +0.5° (less negative) at max"),
            SliderEffect("ALIGNMENT", "CAMBER_RR", "add", 0.5,
                        "Rear camber: +0.5° (less negative) at max"),
        ]
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # SLIDE SLIDER (0.0 = grip, 1.0 = slide)
    # ═══════════════════════════════════════════════════════════════════════
    "slide": {
        "description": "Rear grip vs slide - affects camber, toe, diff, and pressure",
        "effects": [
            # Primary: Rear camber (less negative = less grip = more slide)
            SliderEffect("ALIGNMENT", "CAMBER_LR", "add", 1.5,
                        "Rear camber: +1.5° (less negative) at max"),
            SliderEffect("ALIGNMENT", "CAMBER_RR", "add", 1.5,
                        "Rear camber: +1.5° (less negative) at max"),
            
            # Secondary: Rear toe-out (more slide initiation)
            SliderEffect("ALIGNMENT", "TOE_LR", "add", 0.3,
                        "Rear toe: +0.3° toe-out at max"),
            SliderEffect("ALIGNMENT", "TOE_RR", "add", 0.3,
                        "Rear toe: +0.3° toe-out at max"),
            
            # Tertiary: Diff power (more lock = easier to break traction)
            SliderEffect("DIFFERENTIAL", "POWER", "add", 20.0,
                        "Diff power: +20% at max (easier power slide)"),
            
            # Quaternary: Rear pressure (higher = less grip)
            SliderEffect("TYRES", "PRESSURE_LR", "add", 2.0,
                        "Rear pressure: +2 PSI at max (less grip)"),
            SliderEffect("TYRES", "PRESSURE_RR", "add", 2.0,
                        "Rear pressure: +2 PSI at max"),
            
            # Quinary: Front camber (more negative = more front grip)
            SliderEffect("ALIGNMENT", "CAMBER_LF", "add", -0.5,
                        "Front camber: -0.5° (more negative) at max"),
            SliderEffect("ALIGNMENT", "CAMBER_RF", "add", -0.5,
                        "Front camber: -0.5° (more negative) at max"),
        ]
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # AGGRESSION SLIDER (0.0 = safe, 1.0 = aggressive)
    # ═══════════════════════════════════════════════════════════════════════
    "aggression": {
        "description": "Setup aggressiveness - affects ride height, springs, dampers, brakes",
        "effects": [
            # Primary: Lower ride height
            SliderEffect("SUSPENSION", "RIDE_HEIGHT_LF", "add", -8.0,
                        "Ride height: -8mm at max (lower = more aero)"),
            SliderEffect("SUSPENSION", "RIDE_HEIGHT_RF", "add", -8.0,
                        "Ride height: -8mm at max"),
            SliderEffect("SUSPENSION", "RIDE_HEIGHT_LR", "add", -6.0,
                        "Rear ride height: -6mm at max (maintain rake)"),
            SliderEffect("SUSPENSION", "RIDE_HEIGHT_RR", "add", -6.0,
                        "Rear ride height: -6mm at max"),
            
            # Secondary: Stiffer springs
            SliderEffect("SUSPENSION", "SPRING_RATE_LF", "multiply", 0.25,
                        "Springs: +25% at max (stiffer)"),
            SliderEffect("SUSPENSION", "SPRING_RATE_RF", "multiply", 0.25,
                        "Springs: +25% at max"),
            SliderEffect("SUSPENSION", "SPRING_RATE_LR", "multiply", 0.25,
                        "Springs: +25% at max"),
            SliderEffect("SUSPENSION", "SPRING_RATE_RR", "multiply", 0.25,
                        "Springs: +25% at max"),
            
            # Tertiary: Higher rebound/bump ratio (more responsive)
            SliderEffect("SUSPENSION", "DAMP_REBOUND_LF", "multiply", 0.30,
                        "Rebound damping: +30% at max"),
            SliderEffect("SUSPENSION", "DAMP_REBOUND_RF", "multiply", 0.30,
                        "Rebound damping: +30% at max"),
            SliderEffect("SUSPENSION", "DAMP_REBOUND_LR", "multiply", 0.30,
                        "Rebound damping: +30% at max"),
            SliderEffect("SUSPENSION", "DAMP_REBOUND_RR", "multiply", 0.30,
                        "Rebound damping: +30% at max"),
            SliderEffect("SUSPENSION", "DAMP_BUMP_LF", "multiply", 0.20,
                        "Bump damping: +20% at max"),
            SliderEffect("SUSPENSION", "DAMP_BUMP_RF", "multiply", 0.20,
                        "Bump damping: +20% at max"),
            SliderEffect("SUSPENSION", "DAMP_BUMP_LR", "multiply", 0.20,
                        "Bump damping: +20% at max"),
            SliderEffect("SUSPENSION", "DAMP_BUMP_RR", "multiply", 0.20,
                        "Bump damping: +20% at max"),
            
            # Quaternary: More brake power
            SliderEffect("BRAKES", "BRAKE_POWER_MULT", "multiply", 0.15,
                        "Brake power: +15% at max"),
        ]
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # DRIFT SLIDER (0.0 = grip, 1.0 = drift)
    # ═══════════════════════════════════════════════════════════════════════
    "drift": {
        "description": "Drift setup - affects diff, camber, toe, suspension",
        "effects": [
            # Primary: Very locked diff
            SliderEffect("DIFFERENTIAL", "POWER", "add", 40.0,
                        "Diff power: +40% at max (very locked)"),
            SliderEffect("DIFFERENTIAL", "COAST", "add", 30.0,
                        "Diff coast: +30% at max (locked on decel)"),
            SliderEffect("DIFFERENTIAL", "PRELOAD", "add", 30.0,
                        "Diff preload: +30 Nm at max"),
            
            # Secondary: Extreme rear camber reduction
            SliderEffect("ALIGNMENT", "CAMBER_LR", "add", 2.5,
                        "Rear camber: +2.5° (almost zero) at max"),
            SliderEffect("ALIGNMENT", "CAMBER_RR", "add", 2.5,
                        "Rear camber: +2.5° (almost zero) at max"),
            
            # Tertiary: Rear toe-out
            SliderEffect("ALIGNMENT", "TOE_LR", "add", 0.5,
                        "Rear toe: +0.5° toe-out at max"),
            SliderEffect("ALIGNMENT", "TOE_RR", "add", 0.5,
                        "Rear toe: +0.5° toe-out at max"),
            
            # Quaternary: Softer rear springs (easier to break loose)
            SliderEffect("SUSPENSION", "SPRING_RATE_LR", "multiply", -0.20,
                        "Rear springs: -20% at max (softer)"),
            SliderEffect("SUSPENSION", "SPRING_RATE_RR", "multiply", -0.20,
                        "Rear springs: -20% at max"),
            
            # Quinary: More front camber (more front grip)
            SliderEffect("ALIGNMENT", "CAMBER_LF", "add", -1.0,
                        "Front camber: -1.0° (more negative) at max"),
            SliderEffect("ALIGNMENT", "CAMBER_RF", "add", -1.0,
                        "Front camber: -1.0° (more negative) at max"),
            
            # Senary: Forward brake bias
            SliderEffect("BRAKES", "FRONT_BIAS", "add", 5.0,
                        "Brake bias: +5% front at max (initiate with brakes)"),
            
            # Septenary: Higher rear pressure
            SliderEffect("TYRES", "PRESSURE_LR", "add", 3.0,
                        "Rear pressure: +3 PSI at max"),
            SliderEffect("TYRES", "PRESSURE_RR", "add", 3.0,
                        "Rear pressure: +3 PSI at max"),
        ]
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # PERFORMANCE SLIDER (0.0 = comfort, 1.0 = performance)
    # ═══════════════════════════════════════════════════════════════════════
    "performance": {
        "description": "Performance vs comfort - affects dampers, ride height, pressure",
        "effects": [
            # Primary: Stiffer dampers
            SliderEffect("SUSPENSION", "DAMP_BUMP_LF", "multiply", 0.40,
                        "Bump damping: +40% at max"),
            SliderEffect("SUSPENSION", "DAMP_BUMP_RF", "multiply", 0.40,
                        "Bump damping: +40% at max"),
            SliderEffect("SUSPENSION", "DAMP_BUMP_LR", "multiply", 0.40,
                        "Bump damping: +40% at max"),
            SliderEffect("SUSPENSION", "DAMP_BUMP_RR", "multiply", 0.40,
                        "Bump damping: +40% at max"),
            SliderEffect("SUSPENSION", "DAMP_REBOUND_LF", "multiply", 0.40,
                        "Rebound damping: +40% at max"),
            SliderEffect("SUSPENSION", "DAMP_REBOUND_RF", "multiply", 0.40,
                        "Rebound damping: +40% at max"),
            SliderEffect("SUSPENSION", "DAMP_REBOUND_LR", "multiply", 0.40,
                        "Rebound damping: +40% at max"),
            SliderEffect("SUSPENSION", "DAMP_REBOUND_RR", "multiply", 0.40,
                        "Rebound damping: +40% at max"),
            
            # Secondary: Lower ride height
            SliderEffect("SUSPENSION", "RIDE_HEIGHT_LF", "add", -6.0,
                        "Ride height: -6mm at max"),
            SliderEffect("SUSPENSION", "RIDE_HEIGHT_RF", "add", -6.0,
                        "Ride height: -6mm at max"),
            SliderEffect("SUSPENSION", "RIDE_HEIGHT_LR", "add", -4.0,
                        "Rear ride height: -4mm at max"),
            SliderEffect("SUSPENSION", "RIDE_HEIGHT_RR", "add", -4.0,
                        "Rear ride height: -4mm at max"),
            
            # Tertiary: Optimal pressure (slightly lower for grip)
            SliderEffect("TYRES", "PRESSURE_LF", "add", -1.0,
                        "Front pressure: -1 PSI at max (more grip)"),
            SliderEffect("TYRES", "PRESSURE_RF", "add", -1.0,
                        "Front pressure: -1 PSI at max"),
            SliderEffect("TYRES", "PRESSURE_LR", "add", -0.5,
                        "Rear pressure: -0.5 PSI at max"),
            SliderEffect("TYRES", "PRESSURE_RR", "add", -0.5,
                        "Rear pressure: -0.5 PSI at max"),
        ]
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# SLIDER INTERDEPENDENCY ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class SliderInterdependencyEngine:
    """
    Applies slider interdependencies to a setup.
    
    Each slider affects multiple parameters for a noticeable "wow" effect.
    """
    
    def __init__(self):
        self.interdependencies = SLIDER_INTERDEPENDENCIES
    
    def apply_slider(
        self,
        setup: Setup,
        slider_name: str,
        slider_value: float,
        is_click_based: bool = False
    ) -> tuple[Setup, list[str]]:
        """
        Apply a slider's interdependent effects to a setup.
        
        Args:
            setup: Setup to modify
            slider_name: Name of slider (aero, rotation, slide, aggression, drift, performance)
            slider_value: Slider value (0.0 to 1.0)
            is_click_based: Whether this car uses click-based values
        
        Returns:
            Tuple of (modified_setup, list_of_changes)
        """
        if slider_name not in self.interdependencies:
            return setup, [f"Unknown slider: {slider_name}"]
        
        slider_def = self.interdependencies[slider_name]
        changes = []
        
        # Normalize slider value to -1.0 to +1.0 range (centered at 0.5)
        # For sliders like rotation: 0.0 = understeer, 0.5 = neutral, 1.0 = oversteer
        normalized = (slider_value - 0.5) * 2  # -1.0 to +1.0
        
        # For sliders that are 0-based (aero, aggression, drift, performance)
        # Use raw value (0.0 to 1.0)
        if slider_name in ["aero", "aggression", "drift", "performance"]:
            normalized = slider_value
        
        for effect in slider_def["effects"]:
            # Calculate effect magnitude
            magnitude = normalized * effect.base_effect
            
            # Get current value
            current = setup.get_value(effect.param_section, effect.param_key, None)
            
            if current is None:
                # Try alternative key names
                current = self._get_value_with_alternatives(setup, effect.param_section, effect.param_key)
            
            if current is None:
                changes.append(f"[SKIP] {effect.param_key}: Not found in setup")
                continue
            
            # Apply effect
            if effect.effect_type == "add":
                new_value = current + magnitude
                change_str = f"{effect.param_key}: {current:.2f} + {magnitude:+.2f} = {new_value:.2f}"
            elif effect.effect_type == "multiply":
                multiplier = 1.0 + magnitude
                new_value = current * multiplier
                change_str = f"{effect.param_key}: {current:.2f} × {multiplier:.2f} = {new_value:.2f}"
            elif effect.effect_type == "set":
                new_value = magnitude
                change_str = f"{effect.param_key}: {current:.2f} → {new_value:.2f}"
            else:
                continue
            
            # Scale adjustments for click-based setups
            if is_click_based and effect.param_section == "SUSPENSION":
                if "SPRING" in effect.param_key or "DAMP" in effect.param_key:
                    # For click-based, use smaller adjustments
                    if effect.effect_type == "add":
                        new_value = current + (magnitude * 0.1)  # 10% of normal
                    elif effect.effect_type == "multiply":
                        new_value = current * (1.0 + magnitude * 0.5)  # 50% of normal multiplier
            
            # Set the new value
            setup.set_value(effect.param_section, effect.param_key, new_value)
            changes.append(f"[{slider_name.upper()}] {change_str} ({effect.description})")
        
        return setup, changes
    
    def _get_value_with_alternatives(self, setup: Setup, section: str, key: str) -> Optional[float]:
        """Try to get value using alternative key names."""
        # Map of alternative names
        alternatives = {
            "WING_REAR": ["WING_1", "REAR_WING", "RWING", "WING"],
            "WING_FRONT": ["WING_0", "FRONT_WING", "FWING"],
            "FRONT_BIAS": ["BRAKE_BIAS", "BIAS"],
            "BRAKE_POWER_MULT": ["BRAKE_POWER"],
        }
        
        if key in alternatives:
            for alt in alternatives[key]:
                val = setup.get_value(section, alt, None)
                if val is not None:
                    return val
        
        return None
    
    def apply_all_sliders(
        self,
        setup: Setup,
        profile: dict,
        is_click_based: bool = False
    ) -> tuple[Setup, list[str]]:
        """
        Apply all sliders from a profile to a setup.
        
        Args:
            setup: Setup to modify
            profile: Dict with slider values (rotation, slide, aggression, drift, performance, aero)
            is_click_based: Whether this car uses click-based values
        
        Returns:
            Tuple of (modified_setup, list_of_all_changes)
        """
        all_changes = []
        
        # Apply each slider
        slider_mapping = {
            "rotation": profile.get("rotation", 0.5),
            "slide": profile.get("slide", 0.5),
            "aggression": profile.get("aggression", 0.5),
            "drift": profile.get("drift", 0.0),
            "performance": profile.get("performance", 0.5),
            "aero": profile.get("aero", 0.5),
        }
        
        for slider_name, slider_value in slider_mapping.items():
            # Skip neutral values (0.5 for centered sliders, 0.0 for 0-based)
            if slider_name in ["aero", "aggression", "drift", "performance"]:
                if slider_value == 0.0:
                    continue
            else:
                if slider_value == 0.5:
                    continue
            
            setup, changes = self.apply_slider(setup, slider_name, slider_value, is_click_based)
            all_changes.extend(changes)
        
        return setup, all_changes
    
    def get_slider_description(self, slider_name: str) -> str:
        """Get description of what a slider does."""
        if slider_name not in self.interdependencies:
            return f"Unknown slider: {slider_name}"
        
        slider_def = self.interdependencies[slider_name]
        lines = [
            f"=== {slider_name.upper()} SLIDER ===",
            slider_def["description"],
            "",
            "Effects:"
        ]
        
        for effect in slider_def["effects"]:
            lines.append(f"  • {effect.description}")
        
        return "\n".join(lines)
    
    def get_all_descriptions(self) -> str:
        """Get descriptions of all sliders."""
        lines = []
        for slider_name in self.interdependencies:
            lines.append(self.get_slider_description(slider_name))
            lines.append("")
        return "\n".join(lines)
