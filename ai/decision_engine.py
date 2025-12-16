"""
Decision Engine - AI decision-making for setup recommendations.
Uses weighted scoring and rule-based logic to make setup decisions.
"""

from dataclasses import dataclass, field
from typing import Optional
from models.driver_profile import DriverProfile
from models.car import Car
from models.track import Track
from models.setup import Setup
from core.setup_engine import SetupEngine
from core.scoring_engine import ScoreBreakdown


@dataclass
class Decision:
    """Represents an AI decision with reasoning."""
    
    decision_type: str  # "behavior", "adjustment", "recommendation"
    value: str
    confidence: float  # 0.0 to 1.0
    reasoning: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "decision_type": self.decision_type,
            "value": self.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "alternatives": self.alternatives
        }


@dataclass
class SetupRecommendation:
    """Complete setup recommendation with analysis."""
    
    recommended_behavior: str
    setup: Setup
    score: ScoreBreakdown
    decisions: list[Decision]
    summary: str
    
    def to_dict(self) -> dict:
        return {
            "recommended_behavior": self.recommended_behavior,
            "setup": self.setup.to_dict(),
            "score": self.score.to_dict(),
            "decisions": [d.to_dict() for d in self.decisions],
            "summary": self.summary
        }


class DecisionEngine:
    """
    AI engine for making setup decisions.
    Analyzes driver profile, car, and track to recommend optimal setups.
    """
    
    # Weight factors for behavior selection
    BEHAVIOR_WEIGHTS = {
        "safe": {
            "stability": 0.9,
            "safety": 0.9,
            "grip": 0.7,
            "comfort": 0.6
        },
        "balanced": {
            "stability": 0.5,
            "safety": 0.5,
            "grip": 0.6,
            "rotation": 0.5
        },
        "attack": {
            "aggression": 0.8,
            "rotation": 0.7,
            "performance": 0.8,
            "grip": 0.9
        },
        "drift": {
            "slide": 0.9,
            "drift": 0.9,
            "rotation": 0.8,
            "aggression": 0.6
        }
    }
    
    def __init__(self, setup_engine: Optional[SetupEngine] = None):
        """Initialize decision engine."""
        self.setup_engine = setup_engine or SetupEngine()
    
    def recommend_setup(
        self,
        profile: DriverProfile,
        car: Optional[Car] = None,
        track: Optional[Track] = None,
        preferred_behavior: Optional[str] = None
    ) -> SetupRecommendation:
        """
        Generate a complete setup recommendation.
        Analyzes inputs and returns optimal setup with reasoning.
        """
        decisions = []
        
        # Decide on behavior
        if preferred_behavior:
            behavior_id = preferred_behavior
            decisions.append(Decision(
                decision_type="behavior",
                value=behavior_id,
                confidence=0.9,
                reasoning=["User selected behavior preference"]
            ))
        else:
            behavior_decision = self._decide_behavior(profile, car, track)
            behavior_id = behavior_decision.value
            decisions.append(behavior_decision)
        
        # Generate setup
        setup, score = self.setup_engine.generate_setup(
            profile=profile,
            behavior_id=behavior_id,
            car=car,
            track=track,
            setup_name=f"{behavior_id.title()} Touge Setup"
        )
        
        # Analyze and add adjustment decisions
        adjustment_decisions = self._analyze_adjustments(setup, profile, car, track)
        decisions.extend(adjustment_decisions)
        
        # Generate summary
        summary = self._generate_summary(behavior_id, score, decisions, profile)
        
        return SetupRecommendation(
            recommended_behavior=behavior_id,
            setup=setup,
            score=score,
            decisions=decisions,
            summary=summary
        )
    
    def _decide_behavior(
        self,
        profile: DriverProfile,
        car: Optional[Car],
        track: Optional[Track]
    ) -> Decision:
        """Decide the best behavior based on profile and context."""
        factors = profile.get_all_factors()
        scores = {}
        
        # Score each behavior
        for behavior_id, weights in self.BEHAVIOR_WEIGHTS.items():
            score = 0.0
            total_weight = 0.0
            
            for factor_name, weight in weights.items():
                if factor_name in factors:
                    score += factors[factor_name] * weight
                    total_weight += weight
            
            if total_weight > 0:
                scores[behavior_id] = score / total_weight
            else:
                scores[behavior_id] = 0.5
        
        # Apply car-specific adjustments
        if car:
            if car.is_drift_car() and car.drivetrain == "RWD":
                scores["drift"] *= 1.2
            if car.is_high_power():
                scores["safe"] *= 1.1  # High power benefits from stability
        
        # Apply track-specific adjustments
        if track:
            if track.is_touge():
                scores["safe"] *= 1.1
                scores["balanced"] *= 1.1
            if track.is_technical():
                scores["attack"] *= 0.9  # Technical tracks need more control
        
        # Find best behavior
        best_behavior = max(scores, key=scores.get)
        best_score = scores[best_behavior]
        
        # Calculate confidence based on score difference
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) > 1:
            confidence = min(1.0, (sorted_scores[0] - sorted_scores[1]) * 2 + 0.5)
        else:
            confidence = 0.7
        
        # Generate reasoning
        reasoning = []
        if factors["stability"] > 0.6:
            reasoning.append("High stability preference detected")
        if factors["aggression"] > 0.6:
            reasoning.append("Aggressive driving style detected")
        if factors["drift"] > 0.5:
            reasoning.append("Drift-oriented preference detected")
        if factors["grip"] > 0.7:
            reasoning.append("Strong grip preference detected")
        
        if not reasoning:
            reasoning.append("Balanced preferences detected")
        
        # Get alternatives
        alternatives = [b for b in scores.keys() if b != best_behavior]
        alternatives.sort(key=lambda b: scores[b], reverse=True)
        
        return Decision(
            decision_type="behavior",
            value=best_behavior,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=alternatives[:2]
        )
    
    def _analyze_adjustments(
        self,
        setup: Setup,
        profile: DriverProfile,
        car: Optional[Car],
        track: Optional[Track]
    ) -> list[Decision]:
        """Analyze setup and generate adjustment decisions."""
        decisions = []
        
        # Analyze differential settings
        diff_power = setup.get_value("DIFFERENTIAL", "POWER", 45)
        if diff_power > 70:
            decisions.append(Decision(
                decision_type="adjustment",
                value="high_diff_power",
                confidence=0.8,
                reasoning=[
                    "High differential power setting",
                    "Good for maintaining slides and power oversteer",
                    "May be challenging in tight corners"
                ]
            ))
        elif diff_power < 30:
            decisions.append(Decision(
                decision_type="adjustment",
                value="low_diff_power",
                confidence=0.8,
                reasoning=[
                    "Low differential power setting",
                    "Provides stability on power",
                    "Easier to control but less rotation"
                ]
            ))
        
        # Analyze brake bias
        brake_bias = setup.get_value("BRAKES", "BIAS", 58)
        if brake_bias < 55:
            decisions.append(Decision(
                decision_type="adjustment",
                value="rear_brake_bias",
                confidence=0.7,
                reasoning=[
                    "Rear-biased brake distribution",
                    "Helps rotation on corner entry",
                    "Requires careful brake modulation"
                ]
            ))
        elif brake_bias > 62:
            decisions.append(Decision(
                decision_type="adjustment",
                value="front_brake_bias",
                confidence=0.7,
                reasoning=[
                    "Front-biased brake distribution",
                    "Stable and predictable braking",
                    "May understeer on corner entry"
                ]
            ))
        
        # Analyze camber
        front_camber = abs(setup.get_value("ALIGNMENT", "CAMBER_LF", -3))
        if front_camber > 3.5:
            decisions.append(Decision(
                decision_type="adjustment",
                value="aggressive_camber",
                confidence=0.75,
                reasoning=[
                    "Aggressive front camber setting",
                    "Maximizes cornering grip",
                    "May reduce straight-line grip"
                ]
            ))
        
        return decisions
    
    def _generate_summary(
        self,
        behavior_id: str,
        score: ScoreBreakdown,
        decisions: list[Decision],
        profile: DriverProfile
    ) -> str:
        """Generate a human-readable summary of the recommendation."""
        behavior_names = {
            "safe": "Safe Touge",
            "balanced": "Balanced Touge",
            "attack": "Attack Touge",
            "drift": "Drift Touge"
        }
        
        behavior_name = behavior_names.get(behavior_id, behavior_id.title())
        
        summary_parts = [
            f"Recommended: {behavior_name} setup",
            f"Overall score: {score.total_score:.0f}/100",
            f"Confidence: {score.confidence:.0%}"
        ]
        
        # Add key characteristics
        if score.stability_score > 70:
            summary_parts.append("High stability configuration")
        if score.rotation_score > 70:
            summary_parts.append("Good rotation characteristics")
        if score.grip_score > 70:
            summary_parts.append("Optimized for grip")
        
        # Add notes from score
        if score.notes:
            summary_parts.extend(score.notes[:2])
        
        return " | ".join(summary_parts)
    
    def compare_behaviors(
        self,
        profile: DriverProfile,
        car: Optional[Car] = None,
        track: Optional[Track] = None
    ) -> dict[str, dict]:
        """Compare all behaviors for the given context."""
        comparisons = {}
        
        for behavior_id in ["safe", "balanced", "attack", "drift"]:
            setup, score = self.setup_engine.generate_setup(
                profile=profile,
                behavior_id=behavior_id,
                car=car,
                track=track
            )
            
            comparisons[behavior_id] = {
                "score": score.total_score,
                "confidence": score.confidence,
                "stability": score.stability_score,
                "rotation": score.rotation_score,
                "grip": score.grip_score,
                "notes": score.notes
            }
        
        return comparisons
    
    def get_quick_recommendation(
        self,
        profile: DriverProfile
    ) -> str:
        """Get a quick behavior recommendation without full analysis."""
        factors = profile.get_all_factors()
        
        # Simple decision tree
        if factors["drift"] > 0.6:
            return "drift"
        if factors["aggression"] > 0.7 and factors["stability"] < 0.4:
            return "attack"
        if factors["stability"] > 0.7 or factors["safety"] > 0.7:
            return "safe"
        
        return "balanced"
