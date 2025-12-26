"""
Setup Engine V2 - Physics-Based Expert System
Complete rewrite with granular classification, dynamic tire pressure, and accurate physics calculations.
"""

from typing import Optional, Dict, Tuple
from pathlib import Path
import configparser
import math
from dataclasses import dataclass
from models.setup import Setup, SetupSection
from models.driver_profile import DriverProfile
from models.car import Car
from models.track import Track
from core.behavior_engine import BehaviorEngine, Behavior
from core.rules_engine import RulesEngine
from core.scoring_engine import ScoringEngine, ScoreBreakdown


# ═══════════════════════════════════════════════════════════════════════════
# PHYSICAL CONSTANTS & TARGETS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class PhysicalTargets:
    """Physical targets for a car category."""
    
    # Tire pressure targets (PSI)
    hot_pressure_front: float  # Target pressure after 3 laps
    hot_pressure_rear: float
    pressure_gain_per_lap: float  # PSI gained per lap
    
    # Suspension frequency targets (Hz)
    front_frequency: float  # Natural frequency front
    rear_frequency: float   # Natural frequency rear
    
    # Damping ratios
    bump_rebound_ratio: float  # Rebound/Bump ratio (typically 2:1 to 3:1)
    fast_slow_ratio: float     # Fast/Slow damping ratio
    
    # Aero & Rake
    rake_angle: float          # Degrees (front lower than rear)
    front_ride_height: float   # mm
    rear_ride_height: float    # mm
    aero_balance: float        # 0.0-1.0 (0=understeer, 1=oversteer)
    
    # Alignment
    camber_front: float        # Degrees (negative)
    camber_rear: float
    toe_front: float           # Degrees (per wheel)
    toe_rear: float
    caster: float              # Degrees
    
    # Differential (%)
    diff_power: float
    diff_coast: float
    diff_preload: float
    
    # ARB stiffness (relative 0-10)
    arb_front: float
    arb_rear: float
    
    # Brake bias (% front)
    brake_bias: float


# ═══════════════════════════════════════════════════════════════════════════
# CAR CATEGORY DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

CATEGORY_TARGETS = {
    
    # ─────────────────────────────────────────────────────────────────────
    # FORMULA CARS (F1, F3, RSS)
    # ─────────────────────────────────────────────────────────────────────
    "formula": PhysicalTargets(
        # Tires: Very high pressure, sensitive to temperature
        hot_pressure_front=24.0,
        hot_pressure_rear=23.0,
        pressure_gain_per_lap=1.2,  # Slicks heat up fast
        
        # Suspension: Ultra-stiff, high frequency
        front_frequency=3.5,  # Hz (very stiff)
        rear_frequency=3.8,
        
        # Damping: High rebound control
        bump_rebound_ratio=3.0,  # 3:1 ratio
        fast_slow_ratio=2.5,
        
        # Aero: Maximum rake, very low ride height
        rake_angle=1.5,  # 1.5° rake
        front_ride_height=35,  # mm (very low)
        rear_ride_height=50,
        aero_balance=0.45,  # Slight understeer for stability
        
        # Alignment: Aggressive camber, minimal toe
        camber_front=-3.5,
        camber_rear=-2.0,
        toe_front=-0.05,  # Slight toe-out
        toe_rear=0.10,    # Slight toe-in
        caster=7.0,
        
        # Differential: Medium locking
        diff_power=50.0,
        diff_coast=40.0,
        diff_preload=30.0,
        
        # ARB: Stiff for flat cornering
        arb_front=8.0,
        arb_rear=7.0,
        
        # Brakes: Forward bias
        brake_bias=62.0
    ),
    
    # ─────────────────────────────────────────────────────────────────────
    # PROTOTYPES (LMP1, LMP2, LMP3)
    # ─────────────────────────────────────────────────────────────────────
    "prototype": PhysicalTargets(
        # Tires: High pressure for endurance
        hot_pressure_front=26.0,
        hot_pressure_rear=25.5,
        pressure_gain_per_lap=1.0,
        
        # Suspension: Very stiff but more compliant than F1
        front_frequency=3.2,
        rear_frequency=3.5,
        
        # Damping: Balanced for long stints
        bump_rebound_ratio=2.8,
        fast_slow_ratio=2.2,
        
        # Aero: High rake for diffuser efficiency
        rake_angle=1.8,  # Higher rake than F1
        front_ride_height=40,
        rear_ride_height=58,
        aero_balance=0.48,
        
        # Alignment: Moderate camber
        camber_front=-3.8,
        camber_rear=-2.5,
        toe_front=-0.03,
        toe_rear=0.12,
        caster=6.5,
        
        # Differential: High locking for traction
        diff_power=65.0,
        diff_coast=55.0,
        diff_preload=40.0,
        
        # ARB: Stiff front for turn-in
        arb_front=7.5,
        arb_rear=6.5,
        
        # Brakes: Forward bias
        brake_bias=60.0
    ),
    
    # ─────────────────────────────────────────────────────────────────────
    # GT3 / GTE / GT4
    # ─────────────────────────────────────────────────────────────────────
    "gt": PhysicalTargets(
        # Tires: Standard GT3 hot pressure
        hot_pressure_front=27.5,
        hot_pressure_rear=27.0,
        pressure_gain_per_lap=0.8,
        
        # Suspension: Stiff but road-compliant
        front_frequency=2.8,
        rear_frequency=3.0,
        
        # Damping: Balanced 2:1 ratio
        bump_rebound_ratio=2.5,
        fast_slow_ratio=2.0,
        
        # Aero: Moderate rake
        rake_angle=0.8,
        front_ride_height=50,
        rear_ride_height=58,
        aero_balance=0.50,  # Neutral
        
        # Alignment: Aggressive GT camber
        camber_front=-4.0,
        camber_rear=-3.0,
        toe_front=-0.05,
        toe_rear=0.15,
        caster=6.0,
        
        # Differential: Medium-high locking
        diff_power=65.0,
        diff_coast=50.0,
        diff_preload=30.0,
        
        # ARB: Balanced
        arb_front=6.0,
        arb_rear=5.0,
        
        # Brakes: Forward bias
        brake_bias=62.0
    ),
    
    # ─────────────────────────────────────────────────────────────────────
    # STREET SPORT (911, M4, Cayman GT4)
    # ─────────────────────────────────────────────────────────────────────
    "street_sport": PhysicalTargets(
        # Tires: Road-friendly pressure
        hot_pressure_front=30.0,
        hot_pressure_rear=28.0,
        pressure_gain_per_lap=0.6,
        
        # Suspension: Moderate stiffness
        front_frequency=2.2,
        rear_frequency=2.4,
        
        # Damping: Comfort-oriented
        bump_rebound_ratio=2.2,
        fast_slow_ratio=1.8,
        
        # Aero: Minimal rake
        rake_angle=0.3,
        front_ride_height=90,
        rear_ride_height=95,
        aero_balance=0.52,  # Slight oversteer
        
        # Alignment: Moderate camber
        camber_front=-2.8,
        camber_rear=-2.2,
        toe_front=0.05,   # Slight toe-in for stability
        toe_rear=0.15,
        caster=5.5,
        
        # Differential: Low locking
        diff_power=45.0,
        diff_coast=35.0,
        diff_preload=25.0,
        
        # ARB: Moderate
        arb_front=5.5,
        arb_rear=4.5,
        
        # Brakes: Neutral
        brake_bias=58.0
    ),
    
    # ─────────────────────────────────────────────────────────────────────
    # STREET TOUGE (Skyline, AE86, S2000)
    # ─────────────────────────────────────────────────────────────────────
    "street": PhysicalTargets(
        # Tires: Standard road pressure
        hot_pressure_front=32.0,
        hot_pressure_rear=30.0,
        pressure_gain_per_lap=0.5,
        
        # Suspension: Soft for bumpy roads
        front_frequency=1.8,
        rear_frequency=2.0,
        
        # Damping: Soft for comfort
        bump_rebound_ratio=2.0,
        fast_slow_ratio=1.5,
        
        # Aero: No rake (street car)
        rake_angle=0.0,
        front_ride_height=100,
        rear_ride_height=105,
        aero_balance=0.55,  # Oversteer-friendly
        
        # Alignment: Mild camber
        camber_front=-2.5,
        camber_rear=-2.0,
        toe_front=0.05,
        toe_rear=0.15,
        caster=5.0,
        
        # Differential: Low locking
        diff_power=40.0,
        diff_coast=30.0,
        diff_preload=20.0,
        
        # ARB: Soft
        arb_front=5.0,
        arb_rear=4.0,
        
        # Brakes: Neutral
        brake_bias=58.0
    ),
    
    # ─────────────────────────────────────────────────────────────────────
    # VINTAGE (60s-70s)
    # ─────────────────────────────────────────────────────────────────────
    "vintage": PhysicalTargets(
        # Tires: Low pressure for bias-ply tires
        hot_pressure_front=28.0,
        hot_pressure_rear=26.0,
        pressure_gain_per_lap=0.4,  # Bias-ply heats slowly
        
        # Suspension: Very soft, low frequency
        front_frequency=1.5,
        rear_frequency=1.6,
        
        # Damping: Minimal damping (old tech)
        bump_rebound_ratio=1.8,
        fast_slow_ratio=1.3,
        
        # Aero: No aero, high ride height
        rake_angle=0.0,
        front_ride_height=120,
        rear_ride_height=125,
        aero_balance=0.50,
        
        # Alignment: Minimal camber (old suspension)
        camber_front=-1.5,
        camber_rear=-1.0,
        toe_front=0.10,  # Toe-in for stability
        toe_rear=0.20,
        caster=3.0,  # Low caster
        
        # Differential: Open or spool
        diff_power=30.0,
        diff_coast=20.0,
        diff_preload=10.0,
        
        # ARB: Very soft or none
        arb_front=3.0,
        arb_rear=2.5,
        
        # Brakes: Rear bias (old tech)
        brake_bias=52.0
    ),
    
    # ─────────────────────────────────────────────────────────────────────
    # DRIFT SPEC
    # ─────────────────────────────────────────────────────────────────────
    "drift": PhysicalTargets(
        # Tires: High rear pressure for slide
        hot_pressure_front=32.0,
        hot_pressure_rear=36.0,  # High for less grip
        pressure_gain_per_lap=0.7,
        
        # Suspension: Stiff front, soft rear
        front_frequency=2.5,
        rear_frequency=1.8,  # Soft for slide
        
        # Damping: Low rear damping
        bump_rebound_ratio=2.0,
        fast_slow_ratio=1.6,
        
        # Aero: No aero
        rake_angle=0.2,
        front_ride_height=110,
        rear_ride_height=120,
        aero_balance=0.70,  # Oversteer
        
        # Alignment: Low rear camber, toe-out
        camber_front=-3.5,
        camber_rear=-1.0,  # Low for slide
        toe_front=-0.05,
        toe_rear=-0.15,  # Toe-out for instability
        caster=6.5,  # High for angle
        
        # Differential: Maximum locking
        diff_power=85.0,
        diff_coast=65.0,
        diff_preload=50.0,
        
        # ARB: Stiff front, soft rear
        arb_front=7.0,
        arb_rear=3.0,
        
        # Brakes: Rear bias for initiation
        brake_bias=54.0
    ),
}


# ═══════════════════════════════════════════════════════════════════════════
# MAIN SETUP ENGINE V2
# ═══════════════════════════════════════════════════════════════════════════

class SetupEngineV2:
    """
    Physics-based expert system for setup generation.
    Uses granular classification, dynamic calculations, and real-world physics.
    """
    
    def __init__(self):
        self.behavior_engine = BehaviorEngine()
        self.rules_engine = RulesEngine()
        self.scoring_engine = ScoringEngine()
    
    # ═══════════════════════════════════════════════════════════════════════
    # 1. GRANULAR CAR CLASSIFICATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def classify_car(self, car: Car) -> str:
        """
        Classify car into one of 7 granular categories.
        Returns: "formula", "prototype", "gt", "street_sport", "street", "vintage", "drift"
        """
        if not car:
            return "street"
        
        car_id = car.car_id.lower()
        car_name = car.name.lower() if car.name else ""
        car_class = car.car_class.lower() if car.car_class else ""
        
        # 1. DRIFT (highest priority)
        if car.is_drift_car() or "drift" in car_id or "drift" in car_name:
            return "drift"
        
        # 2. FORMULA
        formula_patterns = ["formula", "f1", "f2", "f3", "f4", "rss_formula", "fia_f"]
        if any(p in car_id or p in car_name or p in car_class for p in formula_patterns):
            return "formula"
        
        # 3. PROTOTYPE
        proto_patterns = ["lmp", "lmp1", "lmp2", "lmp3", "prototype", "p1", "p2"]
        if any(p in car_id or p in car_name or p in car_class for p in proto_patterns):
            return "prototype"
        
        # 4. GT (GT3, GTE, GT4)
        gt_patterns = ["gt3", "gt2", "gt4", "gte", "gtc", "gt1", "dtm", "tcr"]
        if any(p in car_id or p in car_name or p in car_class for p in gt_patterns):
            return "gt"
        
        # 5. VINTAGE (check year or classic patterns)
        vintage_patterns = ["vintage", "classic", "historic", "1960", "1970", "60s", "70s"]
        if any(p in car_id or p in car_name for p in vintage_patterns):
            return "vintage"
        
        # Check power/weight for vintage (low power, heavy)
        if car.power_hp > 0 and car.weight_kg > 0:
            power_to_weight = car.power_hp / car.weight_kg
            if power_to_weight < 0.15 and car.power_hp < 250:  # <150hp/ton, <250hp
                return "vintage"
        
        # 6. STREET SPORT (high-performance street cars)
        sport_patterns = ["gt4", "m3", "m4", "m5", "rs", "gtr", "911", "cayman", "boxster", 
                         "corvette", "viper", "amg", "type_r", "sti", "evo"]
        if any(p in car_id or p in car_name for p in sport_patterns):
            # Check if it's a proper sport car (>250hp, <1500kg)
            if car.power_hp > 250 and car.weight_kg < 1500:
                return "street_sport"
        
        # Check power/weight for street sport (250-400hp/ton)
        if car.power_hp > 0 and car.weight_kg > 0:
            power_to_weight = car.power_hp / car.weight_kg
            if 0.25 <= power_to_weight <= 0.45:
                return "street_sport"
        
        # 7. STREET (default for Touge/normal cars)
        return "street"
    
    # ═══════════════════════════════════════════════════════════════════════
    # 2. DYNAMIC TIRE PRESSURE MODULE
    # ═══════════════════════════════════════════════════════════════════════
    
    def calculate_cold_pressure(
        self, 
        hot_target: float, 
        ambient_temp: float, 
        road_temp: float,
        pressure_gain_per_lap: float,
        laps_to_optimal: int = 3
    ) -> float:
        """
        Calculate cold (starting) tire pressure to reach hot target after N laps.
        
        Physics:
        - Tire pressure increases with temperature (Gay-Lussac's Law)
        - Typical gain: 0.5-1.5 PSI per lap depending on tire type
        - Ambient and road temperature affect heat buildup rate
        
        Args:
            hot_target: Target hot pressure (PSI)
            ambient_temp: Ambient air temperature (°C)
            road_temp: Road surface temperature (°C)
            pressure_gain_per_lap: Expected PSI gain per lap
            laps_to_optimal: Number of laps to reach optimal temp (default 3)
        
        Returns:
            Cold starting pressure (PSI)
        """
        # Base calculation: subtract expected gain
        total_gain = pressure_gain_per_lap * laps_to_optimal
        cold_pressure = hot_target - total_gain
        
        # Temperature compensation
        # If road is cold (<20°C), tires heat slower → need higher starting pressure
        if road_temp < 20:
            temp_deficit = 20 - road_temp
            cold_pressure += temp_deficit * 0.075  # +0.075 PSI per °C below 20°C
        
        # If road is hot (>35°C), tires heat faster → need lower starting pressure
        elif road_temp > 35:
            temp_excess = road_temp - 35
            cold_pressure -= temp_excess * 0.05  # -0.05 PSI per °C above 35°C
        
        # Ambient temperature also affects (less impact than road)
        if ambient_temp < 15:
            cold_pressure += (15 - ambient_temp) * 0.03
        elif ambient_temp > 30:
            cold_pressure -= (ambient_temp - 30) * 0.02
        
        # Clamp to reasonable range (18-35 PSI)
        cold_pressure = max(18.0, min(35.0, cold_pressure))
        
        return round(cold_pressure, 1)
    
    def calculate_tire_pressures(
        self,
        category: str,
        ambient_temp: float = 25.0,
        road_temp: float = 30.0
    ) -> Dict[str, float]:
        """
        Calculate all four tire pressures (cold) based on category and conditions.
        
        Returns:
            Dict with keys: PRESSURE_LF, PRESSURE_RF, PRESSURE_LR, PRESSURE_RR
        """
        targets = CATEGORY_TARGETS[category]
        
        # Calculate cold pressures
        cold_front = self.calculate_cold_pressure(
            targets.hot_pressure_front,
            ambient_temp,
            road_temp,
            targets.pressure_gain_per_lap
        )
        
        cold_rear = self.calculate_cold_pressure(
            targets.hot_pressure_rear,
            ambient_temp,
            road_temp,
            targets.pressure_gain_per_lap
        )
        
        return {
            "PRESSURE_LF": cold_front,
            "PRESSURE_RF": cold_front,
            "PRESSURE_LR": cold_rear,
            "PRESSURE_RR": cold_rear
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # 3. SUSPENSION PHYSICS CALCULATIONS
    # ═══════════════════════════════════════════════════════════════════════
    
    def calculate_spring_rate(
        self,
        target_frequency: float,
        corner_weight_kg: float,
        motion_ratio: float = 1.0
    ) -> float:
        """
        Calculate spring rate to achieve target natural frequency.
        
        Formula: f = (1/2π) * sqrt(k/m)
        Where: f = frequency (Hz), k = spring rate (N/m), m = mass (kg)
        
        Rearranged: k = (2πf)² * m
        
        Args:
            target_frequency: Desired natural frequency (Hz)
            corner_weight_kg: Weight on that corner (kg)
            motion_ratio: Wheel motion / spring motion (typically 0.8-1.2)
        
        Returns:
            Spring rate in N/m
        """
        # Convert frequency to angular frequency
        omega = 2 * math.pi * target_frequency
        
        # Calculate spring rate at wheel
        k_wheel = (omega ** 2) * corner_weight_kg
        
        # Convert to spring rate (accounting for motion ratio)
        # k_spring = k_wheel * (motion_ratio)²
        k_spring = k_wheel * (motion_ratio ** 2)
        
        return k_spring
    
    def calculate_damping(
        self,
        spring_rate: float,
        corner_weight_kg: float,
        bump_rebound_ratio: float,
        fast_slow_ratio: float
    ) -> Dict[str, int]:
        """
        Calculate damping values based on spring rate and ratios.
        
        Returns:
            Dict with DAMP_BUMP, DAMP_REBOUND, DAMP_FAST_BUMP, DAMP_FAST_REBOUND
        """
        # Critical damping coefficient
        # c_critical = 2 * sqrt(k * m)
        c_critical = 2 * math.sqrt(spring_rate * corner_weight_kg)
        
        # Use 70% of critical damping as baseline (typical for race cars)
        damping_coefficient = 0.7 * c_critical
        
        # Split into bump and rebound based on ratio
        # If ratio is 2.5:1, then rebound = 2.5 * bump
        # Total = bump + rebound = bump * (1 + ratio)
        # So: bump = total / (1 + ratio)
        bump = damping_coefficient / (1 + bump_rebound_ratio)
        rebound = bump * bump_rebound_ratio
        
        # Fast damping is higher than slow
        fast_bump = bump * fast_slow_ratio
        fast_rebound = rebound * fast_slow_ratio
        
        # Convert to AC units (approximate scaling)
        # AC uses arbitrary units, scale to typical range
        scale_factor = 0.01  # Adjust based on testing
        
        return {
            "DAMP_BUMP": int(bump * scale_factor),
            "DAMP_REBOUND": int(rebound * scale_factor),
            "DAMP_FAST_BUMP": int(fast_bump * scale_factor),
            "DAMP_FAST_REBOUND": int(fast_rebound * scale_factor)
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # 4. AERO & RAKE CALCULATIONS
    # ═══════════════════════════════════════════════════════════════════════
    
    def calculate_ride_heights(
        self,
        category: str,
        track_type: str = "circuit"  # "circuit", "touge", "street"
    ) -> Dict[str, int]:
        """
        Calculate ride heights to achieve target rake angle.
        Adjust based on track type (bumpy touge needs higher).
        
        Returns:
            Dict with RIDE_HEIGHT_LF, RF, LR, RR (mm)
        """
        targets = CATEGORY_TARGETS[category]
        
        front = targets.front_ride_height
        rear = targets.rear_ride_height
        
        # Adjust for track type
        if track_type == "touge":
            # Raise for bumpy mountain roads
            front += 15
            rear += 15
        elif track_type == "street":
            # Raise for street imperfections
            front += 10
            rear += 10
        
        # Ensure rake angle is maintained
        # Rake = (rear - front) / wheelbase
        # We keep the difference constant
        
        return {
            "RIDE_HEIGHT_LF": int(front),
            "RIDE_HEIGHT_RF": int(front),
            "RIDE_HEIGHT_LR": int(rear),
            "RIDE_HEIGHT_RR": int(rear)
        }
    
    def calculate_aero_settings(
        self,
        category: str,
        track_avg_speed: float = 150.0  # km/h
    ) -> Dict[str, int]:
        """
        Calculate aero settings based on track speed.
        
        Returns:
            Dict with WING_FRONT, WING_REAR, etc.
        """
        targets = CATEGORY_TARGETS[category]
        
        # Base aero from category
        # Adjust based on track speed
        # High speed → less wing (less drag)
        # Low speed → more wing (more downforce)
        
        if track_avg_speed > 180:  # Fast track
            wing_multiplier = 0.7
        elif track_avg_speed < 120:  # Slow track
            wing_multiplier = 1.3
        else:  # Medium
            wing_multiplier = 1.0
        
        # Calculate wing levels (0-5 scale in AC)
        # Use aero_balance to split front/rear
        total_wing = 5 * wing_multiplier
        front_wing = int(total_wing * (1 - targets.aero_balance))
        rear_wing = int(total_wing * targets.aero_balance)
        
        # Clamp to 0-5
        front_wing = max(0, min(5, front_wing))
        rear_wing = max(0, min(5, rear_wing))
        
        return {
            "WING_FRONT": front_wing,
            "WING_REAR": rear_wing,
            "SPLITTER": front_wing,
            "REAR_WING": rear_wing
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # 5. DIFFERENTIAL CALCULATIONS (DRIVETRAIN-AWARE)
    # ═══════════════════════════════════════════════════════════════════════
    
    def calculate_differential(
        self,
        category: str,
        drivetrain: str,  # "RWD", "FWD", "AWD"
        torque_nm: float = 400.0
    ) -> Dict[str, float]:
        """
        Calculate differential settings based on drivetrain and torque.
        
        High torque RWD → More locking needed
        FWD → Less locking (avoid understeer)
        AWD → Balanced
        
        Returns:
            Dict with POWER, COAST, PRELOAD
        """
        targets = CATEGORY_TARGETS[category]
        
        # Base values from category
        power = targets.diff_power
        coast = targets.diff_coast
        preload = targets.diff_preload
        
        # Adjust for drivetrain
        if drivetrain == "RWD":
            # High torque RWD needs more locking
            if torque_nm > 600:
                power += 10
                coast += 5
                preload += 5
            elif torque_nm > 400:
                power += 5
                coast += 3
        
        elif drivetrain == "FWD":
            # FWD needs less locking to avoid understeer
            power -= 15
            coast -= 10
            preload -= 10
        
        elif drivetrain == "AWD":
            # AWD can handle more locking
            power += 5
            coast += 5
        
        # Clamp to 0-100%
        power = max(0, min(100, power))
        coast = max(0, min(100, coast))
        preload = max(0, min(100, preload))
        
        return {
            "POWER": power,
            "COAST": coast,
            "PRELOAD": preload
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # 6. ALIGNMENT CALCULATIONS (WHEELBASE-AWARE)
    # ═══════════════════════════════════════════════════════════════════════
    
    def calculate_toe(
        self,
        base_toe: float,
        wheelbase_mm: float = 2600.0
    ) -> float:
        """
        Calculate toe angle accounting for wheelbase.
        
        Longer wheelbase → Less toe needed for same effect
        Shorter wheelbase → More toe needed
        
        Args:
            base_toe: Base toe angle (degrees)
            wheelbase_mm: Wheelbase in mm
        
        Returns:
            Adjusted toe angle (degrees)
        """
        # Reference wheelbase: 2600mm (typical GT3)
        reference_wheelbase = 2600.0
        
        # Scale factor: shorter wheelbase needs more toe
        scale = reference_wheelbase / wheelbase_mm
        
        adjusted_toe = base_toe * scale
        
        # Clamp to reasonable range (-0.5° to +0.5°)
        adjusted_toe = max(-0.5, min(0.5, adjusted_toe))
        
        return round(adjusted_toe, 2)
    
    def calculate_alignment(
        self,
        category: str,
        wheelbase_mm: float = 2600.0
    ) -> Dict[str, float]:
        """
        Calculate all alignment settings.
        
        Returns:
            Dict with CAMBER_LF/RF/LR/RR, TOE_LF/RF/LR/RR, CASTER_LF/RF
        """
        targets = CATEGORY_TARGETS[category]
        
        # Toe adjusted for wheelbase
        toe_front = self.calculate_toe(targets.toe_front, wheelbase_mm)
        toe_rear = self.calculate_toe(targets.toe_rear, wheelbase_mm)
        
        return {
            "CAMBER_LF": targets.camber_front,
            "CAMBER_RF": targets.camber_front,
            "CAMBER_LR": targets.camber_rear,
            "CAMBER_RR": targets.camber_rear,
            "TOE_LF": toe_front,
            "TOE_RF": toe_front,
            "TOE_LR": toe_rear,
            "TOE_RR": toe_rear,
            "CASTER_LF": targets.caster,
            "CASTER_RF": targets.caster
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # 7. BEHAVIOR PARAMETER CHAINS
    # ═══════════════════════════════════════════════════════════════════════
    
    def apply_rotation_chain(
        self,
        setup_values: Dict,
        rotation_factor: float  # 0.0 to 1.0
    ) -> Dict:
        """
        Apply rotation parameter chain.
        More rotation = Rear toe-out + Stiffer rear ARB + Higher diff coast
        
        Args:
            setup_values: Current setup values
            rotation_factor: 0=stable, 1=rotational
        
        Returns:
            Modified setup values
        """
        if rotation_factor <= 0.5:
            return setup_values  # No change for stable
        
        # Calculate adjustment strength (0 to 0.5 → 0 to 1.0)
        strength = (rotation_factor - 0.5) * 2.0
        
        # 1. Increase rear toe-out
        toe_adjustment = strength * 0.3  # Up to +0.3°
        setup_values["TOE_LR"] += toe_adjustment
        setup_values["TOE_RR"] += toe_adjustment
        
        # 2. Stiffen rear ARB (more rotation)
        arb_mult = 1.0 + (strength * 0.3)  # Up to +30%
        setup_values["ARB_REAR"] = int(setup_values["ARB_REAR"] * arb_mult)
        
        # 3. Increase diff coast (helps rotation on entry)
        coast_add = strength * 15  # Up to +15%
        setup_values["DIFF_COAST"] = min(100, setup_values["DIFF_COAST"] + coast_add)
        
        # 4. Reduce rear camber slightly (less mechanical grip)
        camber_mult = 1.0 - (strength * 0.15)  # Up to -15%
        setup_values["CAMBER_LR"] *= camber_mult
        setup_values["CAMBER_RR"] *= camber_mult
        
        return setup_values
    
    def apply_aggression_chain(
        self,
        setup_values: Dict,
        aggression_factor: float  # 0.0 to 1.0
    ) -> Dict:
        """
        Apply aggression parameter chain.
        More aggression = Stiffer springs + Lower ride height + More brake power
        
        Args:
            setup_values: Current setup values
            aggression_factor: 0=safe, 1=aggressive
        
        Returns:
            Modified setup values
        """
        if aggression_factor <= 0.5:
            return setup_values  # No change for safe
        
        # Calculate adjustment strength
        strength = (aggression_factor - 0.5) * 2.0
        
        # 1. Increase spring rates (higher frequency)
        spring_mult = 1.0 + (strength * 0.25)  # Up to +25%
        for key in ["SPRING_RATE_LF", "SPRING_RATE_RF", "SPRING_RATE_LR", "SPRING_RATE_RR"]:
            if key in setup_values:
                setup_values[key] = int(setup_values[key] * spring_mult)
        
        # 2. Lower ride height (lower CG)
        height_reduction = strength * 10  # Up to -10mm
        for key in ["RIDE_HEIGHT_LF", "RIDE_HEIGHT_RF", "RIDE_HEIGHT_LR", "RIDE_HEIGHT_RR"]:
            if key in setup_values:
                setup_values[key] = max(30, setup_values[key] - int(height_reduction))
        
        # 3. Increase brake power
        if "BRAKE_POWER_MULT" in setup_values:
            brake_mult = 1.0 + (strength * 0.2)  # Up to +20%
            setup_values["BRAKE_POWER_MULT"] = min(1.5, setup_values["BRAKE_POWER_MULT"] * brake_mult)
        
        # 4. Increase damping (more control)
        damp_mult = 1.0 + (strength * 0.3)  # Up to +30%
        for key in ["DAMP_BUMP_LF", "DAMP_BUMP_RF", "DAMP_BUMP_LR", "DAMP_BUMP_RR",
                    "DAMP_REBOUND_LF", "DAMP_REBOUND_RF", "DAMP_REBOUND_LR", "DAMP_REBOUND_RR"]:
            if key in setup_values:
                setup_values[key] = int(setup_values[key] * damp_mult)
        
        # 5. Increase diff power (more traction)
        power_add = strength * 10  # Up to +10%
        setup_values["DIFF_POWER"] = min(100, setup_values["DIFF_POWER"] + power_add)
        
        return setup_values
    
    # ═══════════════════════════════════════════════════════════════════════
    # 8. MAIN SETUP GENERATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def generate_setup(
        self,
        car: Car,
        track: Track,
        behavior_id: str = "balanced",
        profile: Optional[DriverProfile] = None,
        ambient_temp: float = 25.0,
        road_temp: float = 30.0
    ) -> Setup:
        """
        Generate complete physics-based setup.
        
        Args:
            car: Car object
            track: Track object
            behavior_id: Behavior preset ID
            profile: Driver profile with preferences
            ambient_temp: Ambient temperature (°C)
            road_temp: Road temperature (°C)
        
        Returns:
            Complete Setup object
        """
        # 1. Classify car
        category = self.classify_car(car)
        print(f"[SETUP V2] Car classified as: {category}")
        
        # 2. Get physical targets
        targets = CATEGORY_TARGETS[category]
        
        # 3. Initialize setup
        setup = Setup(
            name=f"{car.name} - {track.name} - {behavior_id}",
            car_id=car.car_id,
            track_id=track.full_id if track else "",
            behavior=behavior_id
        )
        
        # 4. Calculate tire pressures (dynamic)
        pressures = self.calculate_tire_pressures(category, ambient_temp, road_temp)
        
        # 5. Calculate suspension (physics-based)
        # Estimate corner weights (assume 50/50 distribution for now)
        total_weight = car.weight_kg if car.weight_kg > 0 else 1200
        corner_weight = total_weight / 4
        
        # Front suspension
        spring_rate_front = self.calculate_spring_rate(
            targets.front_frequency,
            corner_weight
        )
        damping_front = self.calculate_damping(
            spring_rate_front,
            corner_weight,
            targets.bump_rebound_ratio,
            targets.fast_slow_ratio
        )
        
        # Rear suspension
        spring_rate_rear = self.calculate_spring_rate(
            targets.rear_frequency,
            corner_weight
        )
        damping_rear = self.calculate_damping(
            spring_rate_rear,
            corner_weight,
            targets.bump_rebound_ratio,
            targets.fast_slow_ratio
        )
        
        # 6. Calculate ride heights & aero
        ride_heights = self.calculate_ride_heights(category, "circuit")
        aero = self.calculate_aero_settings(category, 150.0)
        
        # 7. Calculate differential
        torque = (car.power_hp * 1.36) if car.power_hp > 0 else 400  # Rough estimate
        differential = self.calculate_differential(category, car.drivetrain, torque)
        
        # 8. Calculate alignment
        alignment = self.calculate_alignment(category, 2600.0)
        
        # 9. Assemble setup values
        setup_values = {
            # Tires
            **pressures,
            "COMPOUND": 2,
            
            # Suspension
            "SPRING_RATE_LF": int(spring_rate_front),
            "SPRING_RATE_RF": int(spring_rate_front),
            "SPRING_RATE_LR": int(spring_rate_rear),
            "SPRING_RATE_RR": int(spring_rate_rear),
            
            "DAMP_BUMP_LF": damping_front["DAMP_BUMP"],
            "DAMP_BUMP_RF": damping_front["DAMP_BUMP"],
            "DAMP_BUMP_LR": damping_rear["DAMP_BUMP"],
            "DAMP_BUMP_RR": damping_rear["DAMP_BUMP"],
            
            "DAMP_REBOUND_LF": damping_front["DAMP_REBOUND"],
            "DAMP_REBOUND_RF": damping_front["DAMP_REBOUND"],
            "DAMP_REBOUND_LR": damping_rear["DAMP_REBOUND"],
            "DAMP_REBOUND_RR": damping_rear["DAMP_REBOUND"],
            
            "DAMP_FAST_BUMP_LF": damping_front["DAMP_FAST_BUMP"],
            "DAMP_FAST_BUMP_RF": damping_front["DAMP_FAST_BUMP"],
            "DAMP_FAST_BUMP_LR": damping_rear["DAMP_FAST_BUMP"],
            "DAMP_FAST_BUMP_RR": damping_rear["DAMP_FAST_BUMP"],
            
            "DAMP_FAST_REBOUND_LF": damping_front["DAMP_FAST_REBOUND"],
            "DAMP_FAST_REBOUND_RF": damping_front["DAMP_FAST_REBOUND"],
            "DAMP_FAST_REBOUND_LR": damping_rear["DAMP_FAST_REBOUND"],
            "DAMP_FAST_REBOUND_RR": damping_rear["DAMP_FAST_REBOUND"],
            
            **ride_heights,
            
            # Alignment
            **alignment,
            
            # Differential
            "DIFF_POWER": differential["POWER"],
            "DIFF_COAST": differential["COAST"],
            "DIFF_PRELOAD": differential["PRELOAD"],
            
            # ARB
            "ARB_FRONT": int(targets.arb_front),
            "ARB_REAR": int(targets.arb_rear),
            
            # Brakes
            "BRAKE_BIAS": targets.brake_bias,
            "FRONT_BIAS": targets.brake_bias,
            "BRAKE_POWER_MULT": 1.0,
            
            # Aero
            **aero,
            
            # Fuel
            "FUEL": 30
        }
        
        # 10. Apply behavior parameter chains
        if profile:
            factors = profile.get_all_factors()
            
            # Rotation chain
            if "rotation" in factors:
                setup_values = self.apply_rotation_chain(setup_values, factors["rotation"])
            
            # Aggression chain
            if "aggression" in factors:
                setup_values = self.apply_aggression_chain(setup_values, factors["aggression"])
        
        # 11. Organize into sections
        setup.sections["TYRES"] = SetupSection("TYRES", {
            k: v for k, v in setup_values.items() 
            if k.startswith("PRESSURE") or k == "COMPOUND"
        })
        
        setup.sections["SUSPENSION"] = SetupSection("SUSPENSION", {
            k: v for k, v in setup_values.items()
            if k.startswith(("SPRING", "DAMP", "RIDE_HEIGHT", "PACKER"))
        })
        
        setup.sections["ALIGNMENT"] = SetupSection("ALIGNMENT", {
            k: v for k, v in setup_values.items()
            if k.startswith(("CAMBER", "TOE", "CASTER"))
        })
        
        setup.sections["DIFFERENTIAL"] = SetupSection("DIFFERENTIAL", {
            k: v for k, v in setup_values.items()
            if k.startswith("DIFF")
        })
        
        setup.sections["ARB"] = SetupSection("ARB", {
            "FRONT": setup_values["ARB_FRONT"],
            "REAR": setup_values["ARB_REAR"]
        })
        
        setup.sections["BRAKES"] = SetupSection("BRAKES", {
            k: v for k, v in setup_values.items()
            if k.startswith("BRAKE") or k.endswith("BIAS")
        })
        
        setup.sections["AERO"] = SetupSection("AERO", {
            k: v for k, v in setup_values.items()
            if k.startswith(("WING", "SPLITTER")) or k == "REAR_WING"
        })
        
        setup.sections["FUEL"] = SetupSection("FUEL", {
            "FUEL": setup_values["FUEL"]
        })
        
        print(f"[SETUP V2] Generated setup for {category} car")
        print(f"[SETUP V2] Cold pressures: F={pressures['PRESSURE_LF']}, R={pressures['PRESSURE_LR']}")
        print(f"[SETUP V2] Target hot: F={targets.hot_pressure_front}, R={targets.hot_pressure_rear}")
        
        return setup
