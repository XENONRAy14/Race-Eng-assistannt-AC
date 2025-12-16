"""
Rules Engine V2 - Professional-grade rule-based AI for setup adjustments.
Based on real racing engineering principles and sim racing best practices.

Key principles:
- Balance is about weight transfer management
- Understeer/Oversteer is controlled by relative grip front vs rear
- Suspension geometry affects tire contact patch and grip
- Differential settings control power delivery and rotation
"""

from dataclasses import dataclass
from typing import Callable, Optional, Any
from models.driver_profile import DriverProfile
from models.car import Car
from models.track import Track
from core.behavior_engine import Behavior


@dataclass
class Rule:
    """Represents a single setup adjustment rule."""
    
    rule_id: str
    name: str
    description: str
    
    condition: Callable[[DriverProfile, Optional[Car], Optional[Track], Behavior], bool]
    
    section: str
    parameter: str
    adjustment_type: str  # "absolute", "relative", "multiply"
    value: Any
    
    priority: int = 50
    weight: float = 1.0


class RulesEngine:
    """
    Professional racing engineering rules for setup generation.
    
    ENGINEERING PRINCIPLES:
    
    1. UNDERSTEER FIXES:
       - Soften front springs/ARB
       - Stiffen rear springs/ARB  
       - More front negative camber
       - Reduce front toe-out
       - Lower front ride height
       - Reduce rear downforce (if applicable)
       - Lower front tire pressure
       - Reduce diff preload
    
    2. OVERSTEER FIXES:
       - Stiffen front springs/ARB
       - Soften rear springs/ARB
       - More rear negative camber
       - Add rear toe-in
       - Raise front ride height
       - Increase rear downforce
       - Lower rear tire pressure
       - Reduce diff coast locking
    
    3. TRACTION IMPROVEMENTS:
       - Softer rear springs
       - Lower diff power locking (for low-power exits)
       - Higher diff power locking (for maintaining slides)
       - Lower rear tire pressure
       - More rear negative camber
    
    4. BRAKING STABILITY:
       - More front brake bias = safer but less rotation
       - Less front brake bias = more rotation but risk of spin
       - Stiffer front = less dive, more consistent
    
    5. TOUGE SPECIFIC:
       - Need compliance for bumpy mountain roads
       - Quick direction changes require responsive setup
       - Elevation changes affect weight transfer
       - Tight hairpins need good rotation
    """
    
    def __init__(self):
        """Initialize with professional rules."""
        self._rules: list[Rule] = []
        self._initialize_professional_rules()
    
    def _initialize_professional_rules(self) -> None:
        """Create professional-grade rules based on real racing engineering."""
        
        # ═══════════════════════════════════════════════════════════════════
        # SECTION 1: DIFFERENTIAL TUNING
        # The diff is the most important setting for car behavior
        # ═══════════════════════════════════════════════════════════════════
        
        # POWER (acceleration) - Higher = more locked = more traction but less agile
        # For stability-focused drivers: lower power lock prevents snap oversteer
        self._rules.append(Rule(
            rule_id="diff_power_stability",
            name="Diff Power: Stability Focus",
            description="Lower power lock prevents snap oversteer on corner exit",
            condition=lambda p, c, t, b: p.stability_factor > 0.65,
            section="DIFFERENTIAL",
            parameter="POWER",
            adjustment_type="absolute",
            value=35.0,  # Lower lock for predictable exits
            priority=40
        ))
        
        # For rotation-focused: moderate power for controlled slides
        self._rules.append(Rule(
            rule_id="diff_power_rotation",
            name="Diff Power: Rotation Focus",
            description="Moderate power lock for controllable rotation",
            condition=lambda p, c, t, b: p.rotation_factor > 0.6 and p.drift_factor < 0.5,
            section="DIFFERENTIAL",
            parameter="POWER",
            adjustment_type="absolute",
            value=50.0,
            priority=45
        ))
        
        # For drift: high power lock to maintain slides
        self._rules.append(Rule(
            rule_id="diff_power_drift",
            name="Diff Power: Drift Setup",
            description="High power lock to maintain and control drifts",
            condition=lambda p, c, t, b: p.drift_factor > 0.5 or b.behavior_id == "drift",
            section="DIFFERENTIAL",
            parameter="POWER",
            adjustment_type="absolute",
            value=70.0,  # High lock for drift maintenance
            priority=55
        ))
        
        # COAST (deceleration/lift-off) - Higher = more locked = more stable on lift
        # Low coast = car rotates on lift-off (trail braking technique)
        self._rules.append(Rule(
            rule_id="diff_coast_stability",
            name="Diff Coast: Stability Focus",
            description="Higher coast lock prevents lift-off oversteer",
            condition=lambda p, c, t, b: p.stability_factor > 0.65,
            section="DIFFERENTIAL",
            parameter="COAST",
            adjustment_type="absolute",
            value=45.0,
            priority=40
        ))
        
        # For rotation: lower coast allows trail braking rotation
        self._rules.append(Rule(
            rule_id="diff_coast_rotation",
            name="Diff Coast: Trail Braking",
            description="Lower coast allows rotation on deceleration",
            condition=lambda p, c, t, b: p.rotation_factor > 0.6,
            section="DIFFERENTIAL",
            parameter="COAST",
            adjustment_type="absolute",
            value=25.0,  # Low for trail braking rotation
            priority=45
        ))
        
        # For drift: moderate coast for initiation control
        self._rules.append(Rule(
            rule_id="diff_coast_drift",
            name="Diff Coast: Drift Initiation",
            description="Moderate coast for controlled drift initiation",
            condition=lambda p, c, t, b: p.drift_factor > 0.5 or b.behavior_id == "drift",
            section="DIFFERENTIAL",
            parameter="COAST",
            adjustment_type="absolute",
            value=55.0,
            priority=55
        ))
        
        # PRELOAD - Initial locking torque
        # Higher = more connected feel, quicker response
        # Lower = smoother, more forgiving
        self._rules.append(Rule(
            rule_id="diff_preload_smooth",
            name="Diff Preload: Smooth Response",
            description="Lower preload for smoother, more forgiving behavior",
            condition=lambda p, c, t, b: p.safety_factor > 0.6 or p.comfort_factor > 0.6,
            section="DIFFERENTIAL",
            parameter="PRELOAD",
            adjustment_type="absolute",
            value=15.0,
            priority=40
        ))
        
        self._rules.append(Rule(
            rule_id="diff_preload_responsive",
            name="Diff Preload: Quick Response",
            description="Higher preload for quicker, more connected response",
            condition=lambda p, c, t, b: p.aggression_factor > 0.6 or p.performance_factor > 0.7,
            section="DIFFERENTIAL",
            parameter="PRELOAD",
            adjustment_type="absolute",
            value=40.0,
            priority=45
        ))
        
        # ═══════════════════════════════════════════════════════════════════
        # SECTION 2: SUSPENSION - SPRINGS
        # Softer = more grip but slower response
        # Stiffer = less grip but quicker response and less body roll
        # ═══════════════════════════════════════════════════════════════════
        
        # Front springs - affect turn-in and front grip
        self._rules.append(Rule(
            rule_id="spring_front_grip",
            name="Front Springs: Grip Focus",
            description="Softer front springs for better turn-in grip",
            condition=lambda p, c, t, b: p.grip_factor > 0.65,
            section="SUSPENSION",
            parameter="SPRING_RATE_LF",
            adjustment_type="multiply",
            value=0.92,  # 8% softer
            priority=40
        ))
        
        self._rules.append(Rule(
            rule_id="spring_front_grip_rf",
            name="Front Springs RF: Grip Focus",
            description="Softer front springs for better turn-in grip",
            condition=lambda p, c, t, b: p.grip_factor > 0.65,
            section="SUSPENSION",
            parameter="SPRING_RATE_RF",
            adjustment_type="multiply",
            value=0.92,
            priority=40
        ))
        
        # Stiffer front for quick response (attack/aggressive)
        self._rules.append(Rule(
            rule_id="spring_front_response",
            name="Front Springs: Quick Response",
            description="Stiffer front for immediate turn-in response",
            condition=lambda p, c, t, b: p.aggression_factor > 0.7 or b.behavior_id == "attack",
            section="SUSPENSION",
            parameter="SPRING_RATE_LF",
            adjustment_type="multiply",
            value=1.10,  # 10% stiffer
            priority=50
        ))
        
        self._rules.append(Rule(
            rule_id="spring_front_response_rf",
            name="Front Springs RF: Quick Response",
            description="Stiffer front for immediate turn-in response",
            condition=lambda p, c, t, b: p.aggression_factor > 0.7 or b.behavior_id == "attack",
            section="SUSPENSION",
            parameter="SPRING_RATE_RF",
            adjustment_type="multiply",
            value=1.10,
            priority=50
        ))
        
        # Rear springs - affect traction and rear stability
        # Softer rear = more traction, more stable
        self._rules.append(Rule(
            rule_id="spring_rear_traction",
            name="Rear Springs: Traction Focus",
            description="Softer rear springs for better traction",
            condition=lambda p, c, t, b: p.stability_factor > 0.6 or p.grip_factor > 0.65,
            section="SUSPENSION",
            parameter="SPRING_RATE_LR",
            adjustment_type="multiply",
            value=0.90,  # 10% softer
            priority=40
        ))
        
        self._rules.append(Rule(
            rule_id="spring_rear_traction_rr",
            name="Rear Springs RR: Traction Focus",
            description="Softer rear springs for better traction",
            condition=lambda p, c, t, b: p.stability_factor > 0.6 or p.grip_factor > 0.65,
            section="SUSPENSION",
            parameter="SPRING_RATE_RR",
            adjustment_type="multiply",
            value=0.90,
            priority=40
        ))
        
        # Stiffer rear for rotation (helps oversteer)
        self._rules.append(Rule(
            rule_id="spring_rear_rotation",
            name="Rear Springs: Rotation Focus",
            description="Stiffer rear promotes rotation and oversteer",
            condition=lambda p, c, t, b: p.rotation_factor > 0.65 or p.drift_factor > 0.5,
            section="SUSPENSION",
            parameter="SPRING_RATE_LR",
            adjustment_type="multiply",
            value=1.08,
            priority=45
        ))
        
        self._rules.append(Rule(
            rule_id="spring_rear_rotation_rr",
            name="Rear Springs RR: Rotation Focus",
            description="Stiffer rear promotes rotation and oversteer",
            condition=lambda p, c, t, b: p.rotation_factor > 0.65 or p.drift_factor > 0.5,
            section="SUSPENSION",
            parameter="SPRING_RATE_RR",
            adjustment_type="multiply",
            value=1.08,
            priority=45
        ))
        
        # ═══════════════════════════════════════════════════════════════════
        # SECTION 3: DAMPERS (BUMP & REBOUND)
        # Bump = compression (hitting bumps, weight transfer TO that corner)
        # Rebound = extension (weight transfer AWAY from that corner)
        # ═══════════════════════════════════════════════════════════════════
        
        # Softer bump = better bump absorption, more grip on rough roads
        self._rules.append(Rule(
            rule_id="damp_bump_comfort",
            name="Bump Damping: Comfort/Grip",
            description="Softer bump for better bump absorption on touge roads",
            condition=lambda p, c, t, b: p.comfort_factor > 0.5 or b.behavior_id == "safe",
            section="SUSPENSION",
            parameter="DAMP_BUMP_LF",
            adjustment_type="multiply",
            value=0.85,
            priority=35
        ))
        
        self._rules.append(Rule(
            rule_id="damp_bump_comfort_rf",
            name="Bump Damping RF: Comfort/Grip",
            description="Softer bump for better bump absorption",
            condition=lambda p, c, t, b: p.comfort_factor > 0.5 or b.behavior_id == "safe",
            section="SUSPENSION",
            parameter="DAMP_BUMP_RF",
            adjustment_type="multiply",
            value=0.85,
            priority=35
        ))
        
        self._rules.append(Rule(
            rule_id="damp_bump_comfort_lr",
            name="Bump Damping LR: Comfort/Grip",
            description="Softer rear bump for traction on bumps",
            condition=lambda p, c, t, b: p.comfort_factor > 0.5 or b.behavior_id == "safe",
            section="SUSPENSION",
            parameter="DAMP_BUMP_LR",
            adjustment_type="multiply",
            value=0.85,
            priority=35
        ))
        
        self._rules.append(Rule(
            rule_id="damp_bump_comfort_rr",
            name="Bump Damping RR: Comfort/Grip",
            description="Softer rear bump for traction on bumps",
            condition=lambda p, c, t, b: p.comfort_factor > 0.5 or b.behavior_id == "safe",
            section="SUSPENSION",
            parameter="DAMP_BUMP_RR",
            adjustment_type="multiply",
            value=0.85,
            priority=35
        ))
        
        # Stiffer rebound = quicker weight transfer = more responsive
        self._rules.append(Rule(
            rule_id="damp_rebound_response",
            name="Rebound Damping: Quick Response",
            description="Stiffer rebound for quicker weight transfer response",
            condition=lambda p, c, t, b: p.aggression_factor > 0.6 or p.performance_factor > 0.65,
            section="SUSPENSION",
            parameter="DAMP_REBOUND_LF",
            adjustment_type="multiply",
            value=1.12,
            priority=45
        ))
        
        self._rules.append(Rule(
            rule_id="damp_rebound_response_rf",
            name="Rebound Damping RF: Quick Response",
            description="Stiffer rebound for quicker weight transfer response",
            condition=lambda p, c, t, b: p.aggression_factor > 0.6 or p.performance_factor > 0.65,
            section="SUSPENSION",
            parameter="DAMP_REBOUND_RF",
            adjustment_type="multiply",
            value=1.12,
            priority=45
        ))
        
        self._rules.append(Rule(
            rule_id="damp_rebound_response_lr",
            name="Rebound Damping LR: Quick Response",
            description="Stiffer rear rebound for stability on exit",
            condition=lambda p, c, t, b: p.aggression_factor > 0.6 or p.performance_factor > 0.65,
            section="SUSPENSION",
            parameter="DAMP_REBOUND_LR",
            adjustment_type="multiply",
            value=1.10,
            priority=45
        ))
        
        self._rules.append(Rule(
            rule_id="damp_rebound_response_rr",
            name="Rebound Damping RR: Quick Response",
            description="Stiffer rear rebound for stability on exit",
            condition=lambda p, c, t, b: p.aggression_factor > 0.6 or p.performance_factor > 0.65,
            section="SUSPENSION",
            parameter="DAMP_REBOUND_RR",
            adjustment_type="multiply",
            value=1.10,
            priority=45
        ))
        
        # ═══════════════════════════════════════════════════════════════════
        # SECTION 4: ANTI-ROLL BARS (ARB)
        # Stiffer = less body roll, but less grip on that axle
        # Front stiffer than rear = understeer tendency
        # Rear stiffer than front = oversteer tendency
        # ═══════════════════════════════════════════════════════════════════
        
        # For understeer (stability): stiffer rear, softer front
        self._rules.append(Rule(
            rule_id="arb_understeer_front",
            name="ARB Front: Understeer Setup",
            description="Softer front ARB reduces understeer",
            condition=lambda p, c, t, b: p.stability_factor > 0.7 and p.rotation_factor < 0.4,
            section="ARB",
            parameter="FRONT",
            adjustment_type="absolute",
            value=3,  # Softer
            priority=40
        ))
        
        self._rules.append(Rule(
            rule_id="arb_understeer_rear",
            name="ARB Rear: Understeer Setup",
            description="Stiffer rear ARB adds understeer for stability",
            condition=lambda p, c, t, b: p.stability_factor > 0.7 and p.rotation_factor < 0.4,
            section="ARB",
            parameter="REAR",
            adjustment_type="absolute",
            value=6,  # Stiffer
            priority=40
        ))
        
        # For oversteer/rotation: stiffer front, softer rear
        self._rules.append(Rule(
            rule_id="arb_oversteer_front",
            name="ARB Front: Oversteer Setup",
            description="Stiffer front ARB promotes rotation",
            condition=lambda p, c, t, b: p.rotation_factor > 0.65 or p.drift_factor > 0.5,
            section="ARB",
            parameter="FRONT",
            adjustment_type="absolute",
            value=7,  # Stiffer
            priority=45
        ))
        
        self._rules.append(Rule(
            rule_id="arb_oversteer_rear",
            name="ARB Rear: Oversteer Setup",
            description="Softer rear ARB promotes rotation",
            condition=lambda p, c, t, b: p.rotation_factor > 0.65 or p.drift_factor > 0.5,
            section="ARB",
            parameter="REAR",
            adjustment_type="absolute",
            value=2,  # Softer
            priority=45
        ))
        
        # Balanced setup
        self._rules.append(Rule(
            rule_id="arb_balanced_front",
            name="ARB Front: Balanced",
            description="Balanced front ARB for neutral handling",
            condition=lambda p, c, t, b: 0.4 <= p.rotation_factor <= 0.6 and 0.4 <= p.stability_factor <= 0.6,
            section="ARB",
            parameter="FRONT",
            adjustment_type="absolute",
            value=5,
            priority=35
        ))
        
        self._rules.append(Rule(
            rule_id="arb_balanced_rear",
            name="ARB Rear: Balanced",
            description="Balanced rear ARB for neutral handling",
            condition=lambda p, c, t, b: 0.4 <= p.rotation_factor <= 0.6 and 0.4 <= p.stability_factor <= 0.6,
            section="ARB",
            parameter="REAR",
            adjustment_type="absolute",
            value=4,
            priority=35
        ))
        
        # ═══════════════════════════════════════════════════════════════════
        # SECTION 5: ALIGNMENT - CAMBER
        # More negative = more grip in corners, less on straights
        # Front camber affects turn-in and mid-corner grip
        # Rear camber affects traction and stability
        # ═══════════════════════════════════════════════════════════════════
        
        # High grip demand = more negative camber
        self._rules.append(Rule(
            rule_id="camber_front_grip",
            name="Front Camber: High Grip",
            description="More negative front camber for maximum cornering grip",
            condition=lambda p, c, t, b: p.grip_factor > 0.7,
            section="ALIGNMENT",
            parameter="CAMBER_LF",
            adjustment_type="absolute",
            value=-3.8,  # Degrees
            priority=45
        ))
        
        self._rules.append(Rule(
            rule_id="camber_front_grip_rf",
            name="Front Camber RF: High Grip",
            description="More negative front camber for maximum cornering grip",
            condition=lambda p, c, t, b: p.grip_factor > 0.7,
            section="ALIGNMENT",
            parameter="CAMBER_RF",
            adjustment_type="absolute",
            value=-3.8,
            priority=45
        ))
        
        # Conservative camber for stability
        self._rules.append(Rule(
            rule_id="camber_front_stable",
            name="Front Camber: Stable",
            description="Moderate front camber for predictable behavior",
            condition=lambda p, c, t, b: p.stability_factor > 0.7 or b.behavior_id == "safe",
            section="ALIGNMENT",
            parameter="CAMBER_LF",
            adjustment_type="absolute",
            value=-2.5,
            priority=40
        ))
        
        self._rules.append(Rule(
            rule_id="camber_front_stable_rf",
            name="Front Camber RF: Stable",
            description="Moderate front camber for predictable behavior",
            condition=lambda p, c, t, b: p.stability_factor > 0.7 or b.behavior_id == "safe",
            section="ALIGNMENT",
            parameter="CAMBER_RF",
            adjustment_type="absolute",
            value=-2.5,
            priority=40
        ))
        
        # Rear camber for traction
        self._rules.append(Rule(
            rule_id="camber_rear_traction",
            name="Rear Camber: Traction Focus",
            description="Moderate rear camber for good traction",
            condition=lambda p, c, t, b: p.stability_factor > 0.6 or p.grip_factor > 0.6,
            section="ALIGNMENT",
            parameter="CAMBER_LR",
            adjustment_type="absolute",
            value=-2.2,
            priority=40
        ))
        
        self._rules.append(Rule(
            rule_id="camber_rear_traction_rr",
            name="Rear Camber RR: Traction Focus",
            description="Moderate rear camber for good traction",
            condition=lambda p, c, t, b: p.stability_factor > 0.6 or p.grip_factor > 0.6,
            section="ALIGNMENT",
            parameter="CAMBER_RR",
            adjustment_type="absolute",
            value=-2.2,
            priority=40
        ))
        
        # Less rear camber for drift (easier to break traction)
        self._rules.append(Rule(
            rule_id="camber_rear_drift",
            name="Rear Camber: Drift Setup",
            description="Less rear camber for easier drift initiation",
            condition=lambda p, c, t, b: p.drift_factor > 0.5 or b.behavior_id == "drift",
            section="ALIGNMENT",
            parameter="CAMBER_LR",
            adjustment_type="absolute",
            value=-1.0,
            priority=55
        ))
        
        self._rules.append(Rule(
            rule_id="camber_rear_drift_rr",
            name="Rear Camber RR: Drift Setup",
            description="Less rear camber for easier drift initiation",
            condition=lambda p, c, t, b: p.drift_factor > 0.5 or b.behavior_id == "drift",
            section="ALIGNMENT",
            parameter="CAMBER_RR",
            adjustment_type="absolute",
            value=-1.0,
            priority=55
        ))
        
        # ═══════════════════════════════════════════════════════════════════
        # SECTION 6: ALIGNMENT - TOE
        # Front toe-out = quicker turn-in, less stable on straights
        # Front toe-in = more stable, slower turn-in
        # Rear toe-in = more stable, prevents oversteer
        # Rear toe-out = more rotation, less stable (rarely used)
        # ═══════════════════════════════════════════════════════════════════
        
        # Quick turn-in: slight front toe-out
        self._rules.append(Rule(
            rule_id="toe_front_turnin",
            name="Front Toe: Quick Turn-in",
            description="Slight toe-out for sharper turn-in response",
            condition=lambda p, c, t, b: p.rotation_factor > 0.6 or p.aggression_factor > 0.65,
            section="ALIGNMENT",
            parameter="TOE_LF",
            adjustment_type="absolute",
            value=-0.08,  # Toe-out (negative)
            priority=45
        ))
        
        self._rules.append(Rule(
            rule_id="toe_front_turnin_rf",
            name="Front Toe RF: Quick Turn-in",
            description="Slight toe-out for sharper turn-in response",
            condition=lambda p, c, t, b: p.rotation_factor > 0.6 or p.aggression_factor > 0.65,
            section="ALIGNMENT",
            parameter="TOE_RF",
            adjustment_type="absolute",
            value=-0.08,
            priority=45
        ))
        
        # Stability: neutral to slight toe-in front
        self._rules.append(Rule(
            rule_id="toe_front_stable",
            name="Front Toe: Stability",
            description="Neutral front toe for stable straight-line behavior",
            condition=lambda p, c, t, b: p.stability_factor > 0.7,
            section="ALIGNMENT",
            parameter="TOE_LF",
            adjustment_type="absolute",
            value=0.02,  # Very slight toe-in
            priority=40
        ))
        
        self._rules.append(Rule(
            rule_id="toe_front_stable_rf",
            name="Front Toe RF: Stability",
            description="Neutral front toe for stable straight-line behavior",
            condition=lambda p, c, t, b: p.stability_factor > 0.7,
            section="ALIGNMENT",
            parameter="TOE_RF",
            adjustment_type="absolute",
            value=0.02,
            priority=40
        ))
        
        # Rear toe-in for stability (ALWAYS some toe-in on rear)
        self._rules.append(Rule(
            rule_id="toe_rear_stable",
            name="Rear Toe: High Stability",
            description="More rear toe-in for maximum stability",
            condition=lambda p, c, t, b: p.stability_factor > 0.7 or b.behavior_id == "safe",
            section="ALIGNMENT",
            parameter="TOE_LR",
            adjustment_type="absolute",
            value=0.20,  # More toe-in
            priority=45
        ))
        
        self._rules.append(Rule(
            rule_id="toe_rear_stable_rr",
            name="Rear Toe RR: High Stability",
            description="More rear toe-in for maximum stability",
            condition=lambda p, c, t, b: p.stability_factor > 0.7 or b.behavior_id == "safe",
            section="ALIGNMENT",
            parameter="TOE_RR",
            adjustment_type="absolute",
            value=0.20,
            priority=45
        ))
        
        # Less rear toe for rotation
        self._rules.append(Rule(
            rule_id="toe_rear_rotation",
            name="Rear Toe: Rotation Focus",
            description="Less rear toe-in for more rotation",
            condition=lambda p, c, t, b: p.rotation_factor > 0.65,
            section="ALIGNMENT",
            parameter="TOE_LR",
            adjustment_type="absolute",
            value=0.05,  # Minimal toe-in
            priority=50
        ))
        
        self._rules.append(Rule(
            rule_id="toe_rear_rotation_rr",
            name="Rear Toe RR: Rotation Focus",
            description="Less rear toe-in for more rotation",
            condition=lambda p, c, t, b: p.rotation_factor > 0.65,
            section="ALIGNMENT",
            parameter="TOE_RR",
            adjustment_type="absolute",
            value=0.05,
            priority=50
        ))
        
        # ═══════════════════════════════════════════════════════════════════
        # SECTION 7: BRAKES
        # Higher bias = more front braking = safer but less rotation
        # Lower bias = more rear braking = more rotation but risk of lockup
        # ═══════════════════════════════════════════════════════════════════
        
        # Safe braking: more front bias
        self._rules.append(Rule(
            rule_id="brake_bias_safe",
            name="Brake Bias: Safe",
            description="More front bias for predictable, safe braking",
            condition=lambda p, c, t, b: p.safety_factor > 0.7 or b.behavior_id == "safe",
            section="BRAKES",
            parameter="BIAS",
            adjustment_type="absolute",
            value=62.0,  # More front
            priority=45
        ))
        
        self._rules.append(Rule(
            rule_id="brake_bias_safe_fb",
            name="Brake Bias FB: Safe",
            description="More front bias for predictable, safe braking",
            condition=lambda p, c, t, b: p.safety_factor > 0.7 or b.behavior_id == "safe",
            section="BRAKES",
            parameter="FRONT_BIAS",
            adjustment_type="absolute",
            value=62.0,
            priority=45
        ))
        
        # Aggressive braking: less front bias for trail braking rotation
        self._rules.append(Rule(
            rule_id="brake_bias_aggressive",
            name="Brake Bias: Aggressive",
            description="Less front bias for trail braking rotation",
            condition=lambda p, c, t, b: p.rotation_factor > 0.65 or p.aggression_factor > 0.7,
            section="BRAKES",
            parameter="BIAS",
            adjustment_type="absolute",
            value=54.0,  # More rear
            priority=50
        ))
        
        self._rules.append(Rule(
            rule_id="brake_bias_aggressive_fb",
            name="Brake Bias FB: Aggressive",
            description="Less front bias for trail braking rotation",
            condition=lambda p, c, t, b: p.rotation_factor > 0.65 or p.aggression_factor > 0.7,
            section="BRAKES",
            parameter="FRONT_BIAS",
            adjustment_type="absolute",
            value=54.0,
            priority=50
        ))
        
        # Drift: rear-biased for easier lock-up initiation
        self._rules.append(Rule(
            rule_id="brake_bias_drift",
            name="Brake Bias: Drift",
            description="Rear-biased brakes for drift initiation",
            condition=lambda p, c, t, b: p.drift_factor > 0.6 or b.behavior_id == "drift",
            section="BRAKES",
            parameter="BIAS",
            adjustment_type="absolute",
            value=50.0,  # Very rear-biased
            priority=55
        ))
        
        self._rules.append(Rule(
            rule_id="brake_bias_drift_fb",
            name="Brake Bias FB: Drift",
            description="Rear-biased brakes for drift initiation",
            condition=lambda p, c, t, b: p.drift_factor > 0.6 or b.behavior_id == "drift",
            section="BRAKES",
            parameter="FRONT_BIAS",
            adjustment_type="absolute",
            value=50.0,
            priority=55
        ))
        
        # ═══════════════════════════════════════════════════════════════════
        # SECTION 8: TYRE PRESSURES
        # Lower = more grip, more heat buildup, less responsive
        # Higher = less grip, cooler, more responsive
        # Front vs Rear balance affects handling
        # ═══════════════════════════════════════════════════════════════════
        
        # Grip focus: lower pressures
        self._rules.append(Rule(
            rule_id="pressure_grip_lf",
            name="Tyre Pressure LF: Grip",
            description="Lower front pressure for more grip",
            condition=lambda p, c, t, b: p.grip_factor > 0.65,
            section="TYRES",
            parameter="PRESSURE_LF",
            adjustment_type="absolute",
            value=25.5,
            priority=40
        ))
        
        self._rules.append(Rule(
            rule_id="pressure_grip_rf",
            name="Tyre Pressure RF: Grip",
            description="Lower front pressure for more grip",
            condition=lambda p, c, t, b: p.grip_factor > 0.65,
            section="TYRES",
            parameter="PRESSURE_RF",
            adjustment_type="absolute",
            value=25.5,
            priority=40
        ))
        
        self._rules.append(Rule(
            rule_id="pressure_grip_lr",
            name="Tyre Pressure LR: Grip",
            description="Lower rear pressure for more traction",
            condition=lambda p, c, t, b: p.grip_factor > 0.65 or p.stability_factor > 0.65,
            section="TYRES",
            parameter="PRESSURE_LR",
            adjustment_type="absolute",
            value=25.0,
            priority=40
        ))
        
        self._rules.append(Rule(
            rule_id="pressure_grip_rr",
            name="Tyre Pressure RR: Grip",
            description="Lower rear pressure for more traction",
            condition=lambda p, c, t, b: p.grip_factor > 0.65 or p.stability_factor > 0.65,
            section="TYRES",
            parameter="PRESSURE_RR",
            adjustment_type="absolute",
            value=25.0,
            priority=40
        ))
        
        # Drift: higher rear pressure for easier breakaway
        self._rules.append(Rule(
            rule_id="pressure_drift_lr",
            name="Tyre Pressure LR: Drift",
            description="Higher rear pressure for easier slide initiation",
            condition=lambda p, c, t, b: p.drift_factor > 0.5 or b.behavior_id == "drift",
            section="TYRES",
            parameter="PRESSURE_LR",
            adjustment_type="absolute",
            value=28.0,
            priority=50
        ))
        
        self._rules.append(Rule(
            rule_id="pressure_drift_rr",
            name="Tyre Pressure RR: Drift",
            description="Higher rear pressure for easier slide initiation",
            condition=lambda p, c, t, b: p.drift_factor > 0.5 or b.behavior_id == "drift",
            section="TYRES",
            parameter="PRESSURE_RR",
            adjustment_type="absolute",
            value=28.0,
            priority=50
        ))
        
        # ═══════════════════════════════════════════════════════════════════
        # SECTION 9: RIDE HEIGHT
        # Lower = better aero, lower CoG, but risk of bottoming
        # Higher = more suspension travel, better for bumpy roads
        # Front lower than rear = more front grip
        # Rear lower than front = more rear grip
        # ═══════════════════════════════════════════════════════════════════
        
        # Performance: lower ride height
        self._rules.append(Rule(
            rule_id="ride_height_performance_lf",
            name="Ride Height LF: Performance",
            description="Lower front for better handling",
            condition=lambda p, c, t, b: p.performance_factor > 0.65 or b.behavior_id == "attack",
            section="SUSPENSION",
            parameter="RIDE_HEIGHT_LF",
            adjustment_type="absolute",
            value=45,
            priority=45
        ))
        
        self._rules.append(Rule(
            rule_id="ride_height_performance_rf",
            name="Ride Height RF: Performance",
            description="Lower front for better handling",
            condition=lambda p, c, t, b: p.performance_factor > 0.65 or b.behavior_id == "attack",
            section="SUSPENSION",
            parameter="RIDE_HEIGHT_RF",
            adjustment_type="absolute",
            value=45,
            priority=45
        ))
        
        self._rules.append(Rule(
            rule_id="ride_height_performance_lr",
            name="Ride Height LR: Performance",
            description="Lower rear for better traction",
            condition=lambda p, c, t, b: p.performance_factor > 0.65 or b.behavior_id == "attack",
            section="SUSPENSION",
            parameter="RIDE_HEIGHT_LR",
            adjustment_type="absolute",
            value=50,
            priority=45
        ))
        
        self._rules.append(Rule(
            rule_id="ride_height_performance_rr",
            name="Ride Height RR: Performance",
            description="Lower rear for better traction",
            condition=lambda p, c, t, b: p.performance_factor > 0.65 or b.behavior_id == "attack",
            section="SUSPENSION",
            parameter="RIDE_HEIGHT_RR",
            adjustment_type="absolute",
            value=50,
            priority=45
        ))
        
        # Comfort/Safe: higher ride height for bumpy touge roads
        self._rules.append(Rule(
            rule_id="ride_height_comfort_lf",
            name="Ride Height LF: Comfort",
            description="Higher front for bump absorption",
            condition=lambda p, c, t, b: p.comfort_factor > 0.6 or b.behavior_id == "safe",
            section="SUSPENSION",
            parameter="RIDE_HEIGHT_LF",
            adjustment_type="absolute",
            value=55,
            priority=40
        ))
        
        self._rules.append(Rule(
            rule_id="ride_height_comfort_rf",
            name="Ride Height RF: Comfort",
            description="Higher front for bump absorption",
            condition=lambda p, c, t, b: p.comfort_factor > 0.6 or b.behavior_id == "safe",
            section="SUSPENSION",
            parameter="RIDE_HEIGHT_RF",
            adjustment_type="absolute",
            value=55,
            priority=40
        ))
        
        self._rules.append(Rule(
            rule_id="ride_height_comfort_lr",
            name="Ride Height LR: Comfort",
            description="Higher rear for bump absorption",
            condition=lambda p, c, t, b: p.comfort_factor > 0.6 or b.behavior_id == "safe",
            section="SUSPENSION",
            parameter="RIDE_HEIGHT_LR",
            adjustment_type="absolute",
            value=60,
            priority=40
        ))
        
        self._rules.append(Rule(
            rule_id="ride_height_comfort_rr",
            name="Ride Height RR: Comfort",
            description="Higher rear for bump absorption",
            condition=lambda p, c, t, b: p.comfort_factor > 0.6 or b.behavior_id == "safe",
            section="SUSPENSION",
            parameter="RIDE_HEIGHT_RR",
            adjustment_type="absolute",
            value=60,
            priority=40
        ))
        
        # Sort rules by priority
        self._rules.sort(key=lambda r: r.priority)
    
    def evaluate_rules(
        self,
        profile: DriverProfile,
        car: Optional[Car],
        track: Optional[Track],
        behavior: Behavior
    ) -> list[tuple[Rule, bool]]:
        """Evaluate all rules and return list of (rule, matched) tuples."""
        results = []
        for rule in self._rules:
            try:
                matched = rule.condition(profile, car, track, behavior)
                results.append((rule, matched))
            except Exception:
                results.append((rule, False))
        return results
    
    def get_applicable_rules(
        self,
        profile: DriverProfile,
        car: Optional[Car],
        track: Optional[Track],
        behavior: Behavior
    ) -> list[Rule]:
        """Get list of rules that apply to the current context."""
        applicable = []
        for rule, matched in self.evaluate_rules(profile, car, track, behavior):
            if matched:
                applicable.append(rule)
        return applicable
    
    def get_adjustments(
        self,
        profile: DriverProfile,
        car: Optional[Car],
        track: Optional[Track],
        behavior: Behavior
    ) -> dict[str, dict[str, tuple[str, Any]]]:
        """
        Get all adjustments to apply based on matched rules.
        Returns: {section: {parameter: (adjustment_type, value)}}
        """
        adjustments: dict[str, dict[str, tuple[str, Any]]] = {}
        
        for rule in self.get_applicable_rules(profile, car, track, behavior):
            if rule.section not in adjustments:
                adjustments[rule.section] = {}
            
            adjustments[rule.section][rule.parameter] = (
                rule.adjustment_type,
                rule.value
            )
        
        return adjustments
    
    def add_rule(self, rule: Rule) -> None:
        """Add a custom rule."""
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority)
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID."""
        for i, rule in enumerate(self._rules):
            if rule.rule_id == rule_id:
                self._rules.pop(i)
                return True
        return False
    
    def get_all_rules(self) -> list[Rule]:
        """Get all rules."""
        return self._rules.copy()
