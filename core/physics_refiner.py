"""
Physics Refiner Module - V2.1 Safety and Accuracy Layer
Acts as a post-processing filter after setup generation to ensure physical accuracy.

This module corrects:
1. Motion Ratio errors in spring rate calculations
2. Anti-bottoming for high-downforce cars
3. Fast damping limits for bumpy circuits
"""

from typing import Dict, Optional
import math
from models.setup import Setup
from models.car import Car
from models.track import Track


# ═══════════════════════════════════════════════════════════════════════════
# MOTION RATIO DATABASE
# ═══════════════════════════════════════════════════════════════════════════

# Motion Ratio (MR) = Wheel Travel / Spring Travel
# Lower MR = Spring moves less than wheel (more mechanical advantage)
# Higher MR = Spring moves more than wheel (less mechanical advantage)
#
# Formula: k_spring = k_wheel / MR²
# 
# Example: If MR = 0.8 (wheel moves 10mm, spring moves 8mm)
#          k_spring = k_wheel / 0.64 = k_wheel × 1.56 (stiffer spring needed)

MOTION_RATIOS = {
    # Formula cars: Direct linkage, MR ≈ 1.0
    "formula": {
        "front": 1.0,   # Push-rod, nearly 1:1
        "rear": 1.0
    },
    
    # Prototypes: Similar to Formula
    "prototype": {
        "front": 0.95,  # Slightly less direct
        "rear": 0.95
    },
    
    # GT3: More complex geometry
    "gt": {
        "front": 0.9,   # Double wishbone
        "rear": 0.8     # Multi-link, more mechanical advantage
    },
    
    # Street Sport: Road car geometry
    "street_sport": {
        "front": 0.85,  # MacPherson strut typical
        "rear": 0.75    # Multi-link or trailing arm
    },
    
    # Street: Standard road car
    "street": {
        "front": 0.8,   # MacPherson strut
        "rear": 0.7     # Torsion beam or multi-link
    },
    
    # Vintage: Long travel, low MR
    "vintage": {
        "front": 0.75,  # Soft, long travel
        "rear": 0.65    # Even softer rear
    },
    
    # Drift: Modified geometry
    "drift": {
        "front": 0.85,  # Stiffer front
        "rear": 0.7     # Softer rear for angle
    }
}


# ═══════════════════════════════════════════════════════════════════════════
# PHYSICS REFINER CLASS
# ═══════════════════════════════════════════════════════════════════════════

class PhysicsRefiner:
    """
    Post-processing module to refine setup values for physical accuracy.
    Applies corrections that require knowledge of car-specific geometry.
    """
    
    def __init__(self):
        self.motion_ratios = MOTION_RATIOS
    
    # ═══════════════════════════════════════════════════════════════════════
    # 1. MOTION RATIO CORRECTION
    # ═══════════════════════════════════════════════════════════════════════
    
    def correct_motion_ratio(
        self,
        setup: Setup,
        category: str,
        car_data: Optional[Dict] = None
    ) -> Setup:
        """
        Correct spring rates for motion ratio.
        
        Theory:
        ------
        The SetupEngineV2 calculates k_wheel (spring rate at wheel) using:
            k_wheel = (2πf)² × m
        
        But the actual spring rate needed is:
            k_spring = k_wheel / MR²
        
        Where MR = Motion Ratio (wheel travel / spring travel)
        
        Example:
        --------
        GT3 rear: MR = 0.8
        k_wheel = 99,000 N/m (calculated from frequency)
        k_spring = 99,000 / 0.8² = 99,000 / 0.64 = 154,687 N/m
        
        The spring must be 56% stiffer to achieve the same wheel rate!
        
        Args:
            setup: Setup object with initial spring rates
            category: Car category ("formula", "gt", etc.)
            car_data: Optional dict with custom motion ratios
        
        Returns:
            Setup with corrected spring rates
        """
        # Get motion ratios for this category
        if car_data and "motion_ratio_front" in car_data:
            # Use car-specific values if available
            mr_front = car_data["motion_ratio_front"]
            mr_rear = car_data["motion_ratio_rear"]
        else:
            # Use category defaults
            ratios = self.motion_ratios.get(category, self.motion_ratios["street"])
            mr_front = ratios["front"]
            mr_rear = ratios["rear"]
        
        print(f"[REFINER] Motion Ratio correction: F={mr_front}, R={mr_rear}")
        
        # Calculate correction factors
        # k_spring = k_wheel / MR²
        correction_front = 1.0 / (mr_front ** 2)
        correction_rear = 1.0 / (mr_rear ** 2)
        
        print(f"[REFINER] Spring correction factors: F={correction_front:.3f}x, R={correction_rear:.3f}x")
        
        # Apply corrections to front springs
        for key in ["SPRING_RATE_LF", "SPRING_RATE_RF"]:
            if setup.has_value("SUSPENSION", key):
                original = setup.get_value("SUSPENSION", key, 70000)
                corrected = int(original * correction_front)
                setup.set_value("SUSPENSION", key, corrected)
                print(f"[REFINER] {key}: {original} → {corrected} N/m")
        
        # Apply corrections to rear springs
        for key in ["SPRING_RATE_LR", "SPRING_RATE_RR"]:
            if setup.has_value("SUSPENSION", key):
                original = setup.get_value("SUSPENSION", key, 70000)
                corrected = int(original * correction_rear)
                setup.set_value("SUSPENSION", key, corrected)
                print(f"[REFINER] {key}: {original} → {corrected} N/m")
        
        return setup
    
    # ═══════════════════════════════════════════════════════════════════════
    # 2. ANTI-BOTTOMING SAFETY
    # ═══════════════════════════════════════════════════════════════════════
    
    def apply_anti_bottoming(
        self,
        setup: Setup,
        category: str,
        rake_angle: float
    ) -> Setup:
        """
        Prevent chassis bottoming for high-downforce cars with aggressive rake.
        
        Theory:
        ------
        High-downforce cars (Formula, LMP) generate massive vertical loads in corners.
        With aggressive rake (low front ride height), the front can bottom out.
        
        Bottoming occurs when:
            Suspension compression > Available travel
        
        Solution: Increase spring rate to limit compression under aero load.
        
        Rule of thumb:
        - If rake > 1.0° AND category is high-downforce → +15% spring rate
        - This reduces max compression by ~13% (spring force increases)
        
        Physics:
        --------
        F = k × x  (Hooke's Law)
        If k increases by 15%, then for same force F:
        x_new = F / (1.15k) = x_old / 1.15 = 0.87 × x_old
        
        Compression reduced by 13%, preventing bottoming.
        
        Args:
            setup: Setup object
            category: Car category
            rake_angle: Rake angle in degrees
        
        Returns:
            Setup with increased spring rates if needed
        """
        # Only apply to high-downforce categories
        high_downforce_categories = ["formula", "prototype"]
        
        if category not in high_downforce_categories:
            return setup  # No change needed
        
        # Check if rake is aggressive (>1.0°)
        if rake_angle <= 1.0:
            return setup  # Rake is safe
        
        print(f"[REFINER] Anti-bottoming: Rake {rake_angle:.1f}° is aggressive for {category}")
        print(f"[REFINER] Increasing spring rates by 15% to prevent bottoming")
        
        # Increase all spring rates by 15%
        spring_multiplier = 1.15
        
        for key in ["SPRING_RATE_LF", "SPRING_RATE_RF", "SPRING_RATE_LR", "SPRING_RATE_RR"]:
            if setup.has_value("SUSPENSION", key):
                original = setup.get_value("SUSPENSION", key, 70000)
                increased = int(original * spring_multiplier)
                setup.set_value("SUSPENSION", key, increased)
                print(f"[REFINER] {key}: {original} → {increased} N/m (+15%)")
        
        # Also increase damping proportionally to maintain damping ratio
        # If springs are stiffer, dampers must be stiffer too
        damp_multiplier = math.sqrt(spring_multiplier)  # √1.15 ≈ 1.07 (+7%)
        
        for key in ["DAMP_BUMP_LF", "DAMP_BUMP_RF", "DAMP_BUMP_LR", "DAMP_BUMP_RR",
                    "DAMP_REBOUND_LF", "DAMP_REBOUND_RF", "DAMP_REBOUND_LR", "DAMP_REBOUND_RR"]:
            if setup.has_value("SUSPENSION", key):
                original = setup.get_value("SUSPENSION", key, 3000)
                increased = int(original * damp_multiplier)
                setup.set_value("SUSPENSION", key, increased)
        
        print(f"[REFINER] Damping increased by {(damp_multiplier-1)*100:.1f}% to match springs")
        
        return setup
    
    # ═══════════════════════════════════════════════════════════════════════
    # 3. FAST DAMPING CAP (TOUGE SAFETY)
    # ═══════════════════════════════════════════════════════════════════════
    
    def cap_fast_damping(
        self,
        setup: Setup,
        track_type: str = "circuit"
    ) -> Setup:
        """
        Limit fast damping for bumpy circuits to prevent harsh rebounds.
        
        Theory:
        ------
        Dampers have two stages:
        - SLOW (Bump/Rebound): Low-speed compression/extension (body roll, pitch)
        - FAST (Fast Bump/Rebound): High-speed impacts (bumps, curbs)
        
        On smooth circuits: Fast damping can be high (2-3x slow)
        On bumpy Touge: Fast damping must be limited to absorb shocks
        
        Problem with excessive fast damping:
        - Wheel hits bump → Fast compression
        - If fast bump is too stiff → Wheel bounces back violently
        - Car loses contact with road → Loss of grip
        
        Solution: Cap fast bump at 50% of slow bump
        
        Example:
        --------
        Slow bump = 3000
        Fast bump = 6000 (2x ratio)
        
        For Touge:
        Fast bump capped at 3000 × 0.5 = 1500
        
        This allows wheel to absorb bumps without bouncing.
        
        Args:
            setup: Setup object
            track_type: "circuit", "touge", or "street"
        
        Returns:
            Setup with capped fast damping if needed
        """
        # Only apply to bumpy track types
        if track_type not in ["touge", "street"]:
            return setup  # Smooth circuit, no cap needed
        
        print(f"[REFINER] Fast damping cap for {track_type} track")
        
        # Cap fast bump at 50% of slow bump
        max_ratio = 0.5
        
        # Front left
        if setup.has_value("SUSPENSION", "DAMP_BUMP_LF"):
            slow_bump = setup.get_value("SUSPENSION", "DAMP_BUMP_LF", 3000)
            fast_bump = setup.get_value("SUSPENSION", "DAMP_FAST_BUMP_LF", 6000)
            max_fast = int(slow_bump * max_ratio)
            
            if fast_bump > max_fast:
                setup.set_value("SUSPENSION", "DAMP_FAST_BUMP_LF", max_fast)
                print(f"[REFINER] DAMP_FAST_BUMP_LF: {fast_bump} → {max_fast} (capped at 50%)")
        
        # Front right
        if setup.has_value("SUSPENSION", "DAMP_BUMP_RF"):
            slow_bump = setup.get_value("SUSPENSION", "DAMP_BUMP_RF", 3000)
            fast_bump = setup.get_value("SUSPENSION", "DAMP_FAST_BUMP_RF", 6000)
            max_fast = int(slow_bump * max_ratio)
            
            if fast_bump > max_fast:
                setup.set_value("SUSPENSION", "DAMP_FAST_BUMP_RF", max_fast)
                print(f"[REFINER] DAMP_FAST_BUMP_RF: {fast_bump} → {max_fast} (capped at 50%)")
        
        # Rear left
        if setup.has_value("SUSPENSION", "DAMP_BUMP_LR"):
            slow_bump = setup.get_value("SUSPENSION", "DAMP_BUMP_LR", 3000)
            fast_bump = setup.get_value("SUSPENSION", "DAMP_FAST_BUMP_LR", 6000)
            max_fast = int(slow_bump * max_ratio)
            
            if fast_bump > max_fast:
                setup.set_value("SUSPENSION", "DAMP_FAST_BUMP_LR", max_fast)
                print(f"[REFINER] DAMP_FAST_BUMP_LR: {fast_bump} → {max_fast} (capped at 50%)")
        
        # Rear right
        if setup.has_value("SUSPENSION", "DAMP_BUMP_RR"):
            slow_bump = setup.get_value("SUSPENSION", "DAMP_BUMP_RR", 3000)
            fast_bump = setup.get_value("SUSPENSION", "DAMP_FAST_BUMP_RR", 6000)
            max_fast = int(slow_bump * max_ratio)
            
            if fast_bump > max_fast:
                setup.set_value("SUSPENSION", "DAMP_FAST_BUMP_RR", max_fast)
                print(f"[REFINER] DAMP_FAST_BUMP_RR: {fast_bump} → {max_fast} (capped at 50%)")
        
        # Also cap fast rebound (less critical but for consistency)
        # Front left
        if setup.has_value("SUSPENSION", "DAMP_REBOUND_LF"):
            slow_rebound = setup.get_value("SUSPENSION", "DAMP_REBOUND_LF", 5000)
            fast_rebound = setup.get_value("SUSPENSION", "DAMP_FAST_REBOUND_LF", 10000)
            max_fast = int(slow_rebound * max_ratio)
            
            if fast_rebound > max_fast:
                setup.set_value("SUSPENSION", "DAMP_FAST_REBOUND_LF", max_fast)
        
        # Front right
        if setup.has_value("SUSPENSION", "DAMP_REBOUND_RF"):
            slow_rebound = setup.get_value("SUSPENSION", "DAMP_REBOUND_RF", 5000)
            fast_rebound = setup.get_value("SUSPENSION", "DAMP_FAST_REBOUND_RF", 10000)
            max_fast = int(slow_rebound * max_ratio)
            
            if fast_rebound > max_fast:
                setup.set_value("SUSPENSION", "DAMP_FAST_REBOUND_RF", max_fast)
        
        # Rear left
        if setup.has_value("SUSPENSION", "DAMP_REBOUND_LR"):
            slow_rebound = setup.get_value("SUSPENSION", "DAMP_REBOUND_LR", 5000)
            fast_rebound = setup.get_value("SUSPENSION", "DAMP_FAST_REBOUND_LR", 10000)
            max_fast = int(slow_rebound * max_ratio)
            
            if fast_rebound > max_fast:
                setup.set_value("SUSPENSION", "DAMP_FAST_REBOUND_LR", max_fast)
        
        # Rear right
        if setup.has_value("SUSPENSION", "DAMP_REBOUND_RR"):
            slow_rebound = setup.get_value("SUSPENSION", "DAMP_REBOUND_RR", 5000)
            fast_rebound = setup.get_value("SUSPENSION", "DAMP_FAST_REBOUND_RR", 10000)
            max_fast = int(slow_rebound * max_ratio)
            
            if fast_rebound > max_fast:
                setup.set_value("SUSPENSION", "DAMP_FAST_REBOUND_RR", max_fast)
        
        print(f"[REFINER] Fast damping capped at 50% of slow for bump absorption")
        
        return setup
    
    # ═══════════════════════════════════════════════════════════════════════
    # 4. MAIN REFINE METHOD
    # ═══════════════════════════════════════════════════════════════════════
    
    def refine(
        self,
        setup: Setup,
        category: str,
        rake_angle: float = 0.0,
        track_type: str = "circuit",
        car_data: Optional[Dict] = None
    ) -> Setup:
        """
        Apply all refinement steps to a setup.
        
        Order of operations:
        1. Motion ratio correction (affects spring rates)
        2. Anti-bottoming safety (may increase spring rates further)
        3. Fast damping cap (for bumpy tracks)
        
        Args:
            setup: Setup object from SetupEngineV2
            category: Car category
            rake_angle: Rake angle in degrees
            track_type: "circuit", "touge", or "street"
            car_data: Optional dict with car-specific data
        
        Returns:
            Refined setup ready for export
        """
        print("\n" + "="*70)
        print("PHYSICS REFINER V2.1 - POST-PROCESSING")
        print("="*70)
        
        # Step 1: Motion ratio correction
        print("\n[STEP 1] Motion Ratio Correction")
        print("-" * 70)
        setup = self.correct_motion_ratio(setup, category, car_data)
        
        # Step 2: Anti-bottoming safety
        print("\n[STEP 2] Anti-Bottoming Safety Check")
        print("-" * 70)
        setup = self.apply_anti_bottoming(setup, category, rake_angle)
        
        # Step 3: Fast damping cap
        print("\n[STEP 3] Fast Damping Cap (Track Type: {})".format(track_type))
        print("-" * 70)
        setup = self.cap_fast_damping(setup, track_type)
        
        print("\n" + "="*70)
        print("REFINEMENT COMPLETE")
        print("="*70 + "\n")
        
        return setup


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_motion_ratio(category: str, position: str = "front") -> float:
    """
    Get motion ratio for a category and position.
    
    Args:
        category: Car category
        position: "front" or "rear"
    
    Returns:
        Motion ratio value
    """
    ratios = MOTION_RATIOS.get(category, MOTION_RATIOS["street"])
    return ratios.get(position, 0.8)


def calculate_spring_correction(motion_ratio: float) -> float:
    """
    Calculate spring rate correction factor from motion ratio.
    
    Formula: correction = 1 / MR²
    
    Args:
        motion_ratio: Motion ratio (0.6 to 1.0 typical)
    
    Returns:
        Correction factor (1.0 to 2.78)
    
    Examples:
        MR = 1.0 → correction = 1.00 (no change)
        MR = 0.9 → correction = 1.23 (+23%)
        MR = 0.8 → correction = 1.56 (+56%)
        MR = 0.7 → correction = 2.04 (+104%)
        MR = 0.6 → correction = 2.78 (+178%)
    """
    if motion_ratio <= 0:
        raise ValueError("Motion ratio must be positive")
    
    return 1.0 / (motion_ratio ** 2)
