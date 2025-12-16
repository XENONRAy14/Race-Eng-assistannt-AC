"""
Scoring Engine - Scores and validates setup configurations.
Uses weighted scoring based on driver profile and behavior priorities.
"""

from dataclasses import dataclass
from typing import Optional
from models.setup import Setup
from models.driver_profile import DriverProfile
from models.car import Car
from models.track import Track
from core.behavior_engine import Behavior


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of a setup score."""
    
    total_score: float
    confidence: float
    
    # Component scores (0-100)
    stability_score: float = 0.0
    rotation_score: float = 0.0
    grip_score: float = 0.0
    predictability_score: float = 0.0
    balance_score: float = 0.0
    
    # Penalty scores
    extreme_values_penalty: float = 0.0
    incompatibility_penalty: float = 0.0
    
    # Explanations
    notes: list[str] = None
    
    def __post_init__(self):
        if self.notes is None:
            self.notes = []
    
    def to_dict(self) -> dict:
        return {
            "total_score": self.total_score,
            "confidence": self.confidence,
            "stability_score": self.stability_score,
            "rotation_score": self.rotation_score,
            "grip_score": self.grip_score,
            "predictability_score": self.predictability_score,
            "balance_score": self.balance_score,
            "extreme_values_penalty": self.extreme_values_penalty,
            "incompatibility_penalty": self.incompatibility_penalty,
            "notes": self.notes
        }


class ScoringEngine:
    """
    Engine for scoring setup configurations.
    Evaluates how well a setup matches driver preferences and behavior goals.
    """
    
    # Value ranges for setup parameters (min, max, optimal_center)
    VALUE_RANGES = {
        "DIFFERENTIAL": {
            "POWER": (0, 100, 50),
            "COAST": (0, 100, 40),
            "PRELOAD": (0, 200, 30)
        },
        "BRAKES": {
            "BIAS": (40, 80, 58),
            "FRONT_BIAS": (40, 80, 58)
        },
        "ALIGNMENT": {
            "CAMBER_LF": (-5, 0, -2.5),
            "CAMBER_RF": (-5, 0, -2.5),
            "CAMBER_LR": (-4, 0, -1.5),
            "CAMBER_RR": (-4, 0, -1.5),
            "TOE_LF": (-0.5, 0.5, 0),
            "TOE_RF": (-0.5, 0.5, 0),
            "TOE_LR": (-0.3, 0.5, 0.1),
            "TOE_RR": (-0.3, 0.5, 0.1)
        },
        "TYRES": {
            "PRESSURE_LF": (20, 35, 26),
            "PRESSURE_RF": (20, 35, 26),
            "PRESSURE_LR": (20, 35, 26),
            "PRESSURE_RR": (20, 35, 26)
        },
        "ARB": {
            "FRONT": (0, 10, 5),
            "REAR": (0, 10, 4)
        }
    }
    
    def __init__(self):
        """Initialize scoring engine."""
        pass
    
    def score_setup(
        self,
        setup: Setup,
        profile: DriverProfile,
        behavior: Behavior,
        car: Optional[Car] = None,
        track: Optional[Track] = None
    ) -> ScoreBreakdown:
        """
        Score a setup configuration.
        Returns a detailed score breakdown.
        """
        breakdown = ScoreBreakdown(
            total_score=0.0,
            confidence=0.0
        )
        
        # Calculate component scores
        breakdown.stability_score = self._score_stability(setup, profile, behavior)
        breakdown.rotation_score = self._score_rotation(setup, profile, behavior)
        breakdown.grip_score = self._score_grip(setup, profile, behavior)
        breakdown.predictability_score = self._score_predictability(setup, profile, behavior)
        breakdown.balance_score = self._score_balance(setup)
        
        # Calculate penalties
        breakdown.extreme_values_penalty = self._calculate_extreme_penalty(setup)
        breakdown.incompatibility_penalty = self._calculate_incompatibility_penalty(setup, car)
        
        # Get behavior priorities for weighted average
        priorities = behavior.priorities
        
        # Calculate weighted total score
        weighted_sum = (
            breakdown.stability_score * priorities.get("stability", 0.5) +
            breakdown.rotation_score * priorities.get("rotation", 0.5) +
            breakdown.grip_score * priorities.get("grip", 0.5) +
            breakdown.predictability_score * priorities.get("predictability", 0.5)
        )
        
        total_weight = sum([
            priorities.get("stability", 0.5),
            priorities.get("rotation", 0.5),
            priorities.get("grip", 0.5),
            priorities.get("predictability", 0.5)
        ])
        
        base_score = weighted_sum / total_weight if total_weight > 0 else 50.0
        
        # Add balance bonus
        base_score += breakdown.balance_score * 0.1
        
        # Apply penalties
        base_score -= breakdown.extreme_values_penalty
        base_score -= breakdown.incompatibility_penalty
        
        # Clamp final score
        breakdown.total_score = max(0.0, min(100.0, base_score))
        
        # Calculate confidence based on how many parameters we could evaluate
        breakdown.confidence = self._calculate_confidence(setup, car, track)
        
        # Add notes
        self._add_scoring_notes(breakdown, setup, profile, behavior)
        
        return breakdown
    
    def _score_stability(
        self, 
        setup: Setup, 
        profile: DriverProfile, 
        behavior: Behavior
    ) -> float:
        """Score setup for stability characteristics."""
        score = 50.0
        
        # Differential - lower power = more stability
        diff_power = setup.get_value("DIFFERENTIAL", "POWER", 50)
        if profile.wants_stability:
            # Reward lower diff power for stability seekers
            score += (50 - diff_power) * 0.3
        
        # Rear toe-in adds stability
        toe_lr = setup.get_value("ALIGNMENT", "TOE_LR", 0)
        toe_rr = setup.get_value("ALIGNMENT", "TOE_RR", 0)
        avg_rear_toe = (toe_lr + toe_rr) / 2
        if avg_rear_toe > 0:
            score += avg_rear_toe * 30  # Positive toe = toe-in = stability
        
        # Softer suspension = more stability on bumpy touge
        # (This is simplified - real physics is more complex)
        
        return max(0.0, min(100.0, score))
    
    def _score_rotation(
        self, 
        setup: Setup, 
        profile: DriverProfile, 
        behavior: Behavior
    ) -> float:
        """Score setup for rotation/turn-in characteristics."""
        score = 50.0
        
        # Higher diff power = more rotation on power
        diff_power = setup.get_value("DIFFERENTIAL", "POWER", 50)
        score += (diff_power - 50) * 0.2
        
        # Front ARB stiffer than rear = more rotation
        arb_front = setup.get_value("ARB", "FRONT", 5)
        arb_rear = setup.get_value("ARB", "REAR", 4)
        arb_diff = arb_front - arb_rear
        score += arb_diff * 5
        
        # Rear brake bias = more rotation on braking
        brake_bias = setup.get_value("BRAKES", "BIAS", 58)
        if brake_bias < 55:
            score += (55 - brake_bias) * 2
        
        # Negative front toe (toe-out) = sharper turn-in
        toe_lf = setup.get_value("ALIGNMENT", "TOE_LF", 0)
        toe_rf = setup.get_value("ALIGNMENT", "TOE_RF", 0)
        avg_front_toe = (toe_lf + toe_rf) / 2
        if avg_front_toe < 0:
            score += abs(avg_front_toe) * 20
        
        return max(0.0, min(100.0, score))
    
    def _score_grip(
        self, 
        setup: Setup, 
        profile: DriverProfile, 
        behavior: Behavior
    ) -> float:
        """Score setup for mechanical grip."""
        score = 50.0
        
        # Optimal camber = more grip
        camber_lf = abs(setup.get_value("ALIGNMENT", "CAMBER_LF", -3))
        camber_rf = abs(setup.get_value("ALIGNMENT", "CAMBER_RF", -3))
        avg_front_camber = (camber_lf + camber_rf) / 2
        
        # Optimal front camber around 2.5-3.5 degrees
        if 2.5 <= avg_front_camber <= 3.5:
            score += 15
        elif 2.0 <= avg_front_camber <= 4.0:
            score += 8
        
        # Optimal tyre pressure
        pressure_lf = setup.get_value("TYRES", "PRESSURE_LF", 26)
        if 25 <= pressure_lf <= 27:
            score += 10
        
        # Lower diff preload can help traction
        preload = setup.get_value("DIFFERENTIAL", "PRELOAD", 30)
        if preload < 40:
            score += 5
        
        return max(0.0, min(100.0, score))
    
    def _score_predictability(
        self, 
        setup: Setup, 
        profile: DriverProfile, 
        behavior: Behavior
    ) -> float:
        """Score setup for predictable behavior."""
        score = 50.0
        
        # Moderate values = more predictable
        diff_power = setup.get_value("DIFFERENTIAL", "POWER", 50)
        if 30 <= diff_power <= 60:
            score += 15
        
        # Balanced brake bias = predictable
        brake_bias = setup.get_value("BRAKES", "BIAS", 58)
        if 55 <= brake_bias <= 62:
            score += 10
        
        # Symmetric setup = predictable
        camber_lf = setup.get_value("ALIGNMENT", "CAMBER_LF", -3)
        camber_rf = setup.get_value("ALIGNMENT", "CAMBER_RF", -3)
        if abs(camber_lf - camber_rf) < 0.2:
            score += 5
        
        return max(0.0, min(100.0, score))
    
    def _score_balance(self, setup: Setup) -> float:
        """Score overall setup balance (front/rear)."""
        score = 50.0
        
        # Check ARB balance
        arb_front = setup.get_value("ARB", "FRONT", 5)
        arb_rear = setup.get_value("ARB", "REAR", 4)
        arb_ratio = arb_front / arb_rear if arb_rear > 0 else 1.0
        
        # Ideal ratio around 1.2-1.4 for slight understeer bias
        if 1.1 <= arb_ratio <= 1.5:
            score += 10
        
        # Check camber balance
        front_camber = abs(setup.get_value("ALIGNMENT", "CAMBER_LF", -3))
        rear_camber = abs(setup.get_value("ALIGNMENT", "CAMBER_LR", -2))
        
        # Front should have more camber than rear
        if front_camber > rear_camber:
            score += 5
        
        return max(0.0, min(100.0, score))
    
    def _calculate_extreme_penalty(self, setup: Setup) -> float:
        """Calculate penalty for extreme/unrealistic values."""
        penalty = 0.0
        
        for section_name, params in self.VALUE_RANGES.items():
            section = setup.get_section(section_name)
            if not section:
                continue
            
            for param, (min_val, max_val, _) in params.items():
                value = section.get(param)
                if value is None:
                    continue
                
                # Penalty for values outside range
                if value < min_val:
                    penalty += (min_val - value) * 2
                elif value > max_val:
                    penalty += (value - max_val) * 2
        
        return min(30.0, penalty)  # Cap penalty at 30
    
    def _calculate_incompatibility_penalty(
        self, 
        setup: Setup, 
        car: Optional[Car]
    ) -> float:
        """Calculate penalty for car-incompatible settings."""
        if not car:
            return 0.0
        
        penalty = 0.0
        
        # FWD cars shouldn't have high rear diff settings
        if car.drivetrain == "FWD":
            diff_power = setup.get_value("DIFFERENTIAL", "POWER", 0)
            if diff_power > 50:
                penalty += 10
        
        # Heavy cars need stiffer suspension
        # (This would need actual spring rate values to evaluate)
        
        return min(20.0, penalty)
    
    def _calculate_confidence(
        self, 
        setup: Setup, 
        car: Optional[Car], 
        track: Optional[Track]
    ) -> float:
        """Calculate confidence in the score."""
        confidence = 0.5  # Base confidence
        
        # More sections = higher confidence
        if len(setup.sections) >= 6:
            confidence += 0.2
        elif len(setup.sections) >= 4:
            confidence += 0.1
        
        # Known car = higher confidence
        if car:
            confidence += 0.15
        
        # Known track = higher confidence
        if track:
            confidence += 0.15
        
        return min(1.0, confidence)
    
    def _add_scoring_notes(
        self,
        breakdown: ScoreBreakdown,
        setup: Setup,
        profile: DriverProfile,
        behavior: Behavior
    ) -> None:
        """Add explanatory notes to the score breakdown."""
        
        if breakdown.stability_score > 70:
            breakdown.notes.append("High stability configuration")
        elif breakdown.stability_score < 40:
            breakdown.notes.append("Low stability - may be challenging")
        
        if breakdown.rotation_score > 70:
            breakdown.notes.append("Good rotation/turn-in characteristics")
        
        if breakdown.grip_score > 70:
            breakdown.notes.append("Optimized for mechanical grip")
        
        if breakdown.extreme_values_penalty > 10:
            breakdown.notes.append("Warning: Some values are extreme")
        
        if breakdown.total_score >= 80:
            breakdown.notes.append("Excellent match for your preferences")
        elif breakdown.total_score >= 60:
            breakdown.notes.append("Good match for your preferences")
        elif breakdown.total_score < 40:
            breakdown.notes.append("Consider adjusting preferences or behavior")
    
    def compare_setups(
        self,
        setup1: Setup,
        setup2: Setup,
        profile: DriverProfile,
        behavior: Behavior
    ) -> dict:
        """Compare two setups and return differences."""
        score1 = self.score_setup(setup1, profile, behavior)
        score2 = self.score_setup(setup2, profile, behavior)
        
        return {
            "setup1_score": score1.total_score,
            "setup2_score": score2.total_score,
            "difference": score2.total_score - score1.total_score,
            "better_setup": 2 if score2.total_score > score1.total_score else 1,
            "score1_breakdown": score1.to_dict(),
            "score2_breakdown": score2.to_dict()
        }
