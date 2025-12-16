"""
Feedback Engine - Processes user feedback to improve recommendations.
Tracks setup usage and adjusts weights based on feedback.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from models.setup import Setup
from models.driver_profile import DriverProfile


@dataclass
class FeedbackEntry:
    """Represents a single feedback entry."""
    
    feedback_id: Optional[int] = None
    setup_id: Optional[int] = None
    profile_id: Optional[int] = None
    
    # Feedback type: "rating", "issue", "preference"
    feedback_type: str = "rating"
    
    # Rating (1-5 stars)
    rating: int = 3
    
    # Specific issues reported
    issues: list[str] = field(default_factory=list)
    
    # Free-form comments
    comments: str = ""
    
    # Behavior used
    behavior: str = ""
    
    # Timestamp
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "feedback_id": self.feedback_id,
            "setup_id": self.setup_id,
            "profile_id": self.profile_id,
            "feedback_type": self.feedback_type,
            "rating": self.rating,
            "issues": self.issues,
            "comments": self.comments,
            "behavior": self.behavior,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "FeedbackEntry":
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
        
        return cls(
            feedback_id=data.get("feedback_id"),
            setup_id=data.get("setup_id"),
            profile_id=data.get("profile_id"),
            feedback_type=data.get("feedback_type", "rating"),
            rating=data.get("rating", 3),
            issues=data.get("issues", []),
            comments=data.get("comments", ""),
            behavior=data.get("behavior", ""),
            created_at=created_at
        )


@dataclass
class FeedbackAnalysis:
    """Analysis results from feedback data."""
    
    total_feedback_count: int = 0
    average_rating: float = 0.0
    
    # Issue frequency
    issue_counts: dict[str, int] = field(default_factory=dict)
    
    # Behavior ratings
    behavior_ratings: dict[str, float] = field(default_factory=dict)
    
    # Suggested adjustments
    suggested_adjustments: list[str] = field(default_factory=list)
    
    # Confidence in analysis
    confidence: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "total_feedback_count": self.total_feedback_count,
            "average_rating": self.average_rating,
            "issue_counts": self.issue_counts,
            "behavior_ratings": self.behavior_ratings,
            "suggested_adjustments": self.suggested_adjustments,
            "confidence": self.confidence
        }


class FeedbackEngine:
    """
    Engine for processing and learning from user feedback.
    Adjusts recommendation weights based on feedback patterns.
    """
    
    # Known issue types and their setup implications
    ISSUE_ADJUSTMENTS = {
        "too_unstable": {
            "DIFFERENTIAL": {"POWER": -10, "COAST": -5},
            "ALIGNMENT": {"TOE_LR": 0.05, "TOE_RR": 0.05},
            "description": "Reduce oversteer tendency"
        },
        "too_stable": {
            "DIFFERENTIAL": {"POWER": 10, "COAST": 5},
            "ARB": {"FRONT": 1, "REAR": -1},
            "description": "Increase rotation capability"
        },
        "understeer": {
            "ARB": {"FRONT": -1, "REAR": 1},
            "BRAKES": {"BIAS": -2},
            "ALIGNMENT": {"CAMBER_LF": -0.3, "CAMBER_RF": -0.3},
            "description": "Reduce understeer"
        },
        "oversteer": {
            "ARB": {"FRONT": 1, "REAR": -1},
            "BRAKES": {"BIAS": 2},
            "DIFFERENTIAL": {"POWER": -10},
            "description": "Reduce oversteer"
        },
        "poor_traction": {
            "DIFFERENTIAL": {"POWER": -5, "PRELOAD": -10},
            "TYRES": {"PRESSURE_LR": -0.5, "PRESSURE_RR": -0.5},
            "description": "Improve traction"
        },
        "harsh_ride": {
            "SUSPENSION": {"DAMP_MULTIPLIER": 0.9, "SPRING_MULTIPLIER": 0.95},
            "description": "Soften suspension"
        },
        "too_soft": {
            "SUSPENSION": {"DAMP_MULTIPLIER": 1.1, "SPRING_MULTIPLIER": 1.05},
            "description": "Stiffen suspension"
        },
        "brake_lock": {
            "BRAKES": {"BIAS": 2, "BRAKE_POWER_MULT": -0.05},
            "description": "Reduce front brake lock tendency"
        },
        "rear_brake_lock": {
            "BRAKES": {"BIAS": -3},
            "description": "Reduce rear brake lock tendency"
        }
    }
    
    def __init__(self):
        """Initialize feedback engine."""
        self._feedback_history: list[FeedbackEntry] = []
        self._weight_adjustments: dict[str, float] = {}
    
    def add_feedback(self, feedback: FeedbackEntry) -> None:
        """Add a new feedback entry."""
        self._feedback_history.append(feedback)
        self._update_weights(feedback)
    
    def _update_weights(self, feedback: FeedbackEntry) -> None:
        """Update internal weights based on feedback."""
        # Adjust behavior weights based on rating
        if feedback.behavior:
            key = f"behavior_{feedback.behavior}"
            current = self._weight_adjustments.get(key, 1.0)
            
            # Positive feedback increases weight, negative decreases
            adjustment = (feedback.rating - 3) * 0.05
            self._weight_adjustments[key] = max(0.5, min(1.5, current + adjustment))
    
    def get_suggested_adjustments(
        self,
        setup: Setup,
        issues: list[str]
    ) -> dict[str, dict]:
        """
        Get suggested setup adjustments based on reported issues.
        Returns adjustments to apply to the setup.
        """
        all_adjustments: dict[str, dict] = {}
        
        for issue in issues:
            if issue in self.ISSUE_ADJUSTMENTS:
                issue_adj = self.ISSUE_ADJUSTMENTS[issue]
                
                for section, params in issue_adj.items():
                    if section == "description":
                        continue
                    
                    if section not in all_adjustments:
                        all_adjustments[section] = {}
                    
                    for param, value in params.items():
                        if param in all_adjustments[section]:
                            # Average multiple adjustments
                            all_adjustments[section][param] = (
                                all_adjustments[section][param] + value
                            ) / 2
                        else:
                            all_adjustments[section][param] = value
        
        return all_adjustments
    
    def apply_feedback_adjustments(
        self,
        setup: Setup,
        issues: list[str]
    ) -> Setup:
        """
        Apply feedback-based adjustments to a setup.
        Returns a modified copy of the setup.
        """
        adjusted_setup = setup.clone()
        adjustments = self.get_suggested_adjustments(setup, issues)
        
        for section, params in adjustments.items():
            for param, adjustment in params.items():
                # Handle multiplier parameters
                if param.endswith("_MULTIPLIER"):
                    base_param = param.replace("_MULTIPLIER", "")
                    # Apply to all matching parameters
                    section_obj = adjusted_setup.get_section(section)
                    if section_obj:
                        for key in section_obj.values.keys():
                            if base_param in key:
                                current = section_obj.get(key, 1.0)
                                section_obj.set(key, current * adjustment)
                else:
                    current = adjusted_setup.get_value(section, param)
                    if current is not None:
                        adjusted_setup.set_value(section, param, current + adjustment)
        
        return adjusted_setup
    
    def analyze_feedback(
        self,
        profile_id: Optional[int] = None,
        behavior: Optional[str] = None
    ) -> FeedbackAnalysis:
        """
        Analyze feedback history and generate insights.
        Can filter by profile or behavior.
        """
        # Filter feedback
        filtered = self._feedback_history
        
        if profile_id is not None:
            filtered = [f for f in filtered if f.profile_id == profile_id]
        
        if behavior is not None:
            filtered = [f for f in filtered if f.behavior == behavior]
        
        if not filtered:
            return FeedbackAnalysis(confidence=0.0)
        
        # Calculate statistics
        total_count = len(filtered)
        avg_rating = sum(f.rating for f in filtered) / total_count
        
        # Count issues
        issue_counts: dict[str, int] = {}
        for feedback in filtered:
            for issue in feedback.issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # Calculate behavior ratings
        behavior_ratings: dict[str, float] = {}
        behavior_counts: dict[str, int] = {}
        
        for feedback in filtered:
            if feedback.behavior:
                if feedback.behavior not in behavior_ratings:
                    behavior_ratings[feedback.behavior] = 0.0
                    behavior_counts[feedback.behavior] = 0
                
                behavior_ratings[feedback.behavior] += feedback.rating
                behavior_counts[feedback.behavior] += 1
        
        for b in behavior_ratings:
            if behavior_counts[b] > 0:
                behavior_ratings[b] /= behavior_counts[b]
        
        # Generate suggested adjustments
        suggested = []
        for issue, count in sorted(issue_counts.items(), key=lambda x: -x[1]):
            if count >= 2 and issue in self.ISSUE_ADJUSTMENTS:
                desc = self.ISSUE_ADJUSTMENTS[issue].get("description", issue)
                suggested.append(f"{desc} (reported {count} times)")
        
        # Calculate confidence
        confidence = min(1.0, total_count / 10)  # Max confidence at 10+ feedback
        
        return FeedbackAnalysis(
            total_feedback_count=total_count,
            average_rating=avg_rating,
            issue_counts=issue_counts,
            behavior_ratings=behavior_ratings,
            suggested_adjustments=suggested[:5],
            confidence=confidence
        )
    
    def get_behavior_weight(self, behavior: str) -> float:
        """Get the current weight adjustment for a behavior."""
        return self._weight_adjustments.get(f"behavior_{behavior}", 1.0)
    
    def get_available_issues(self) -> list[dict]:
        """Get list of available issue types for feedback."""
        return [
            {
                "id": issue_id,
                "description": data.get("description", issue_id)
            }
            for issue_id, data in self.ISSUE_ADJUSTMENTS.items()
        ]
    
    def clear_feedback(self, profile_id: Optional[int] = None) -> int:
        """
        Clear feedback history.
        Returns number of entries cleared.
        """
        if profile_id is None:
            count = len(self._feedback_history)
            self._feedback_history.clear()
            self._weight_adjustments.clear()
            return count
        
        original_count = len(self._feedback_history)
        self._feedback_history = [
            f for f in self._feedback_history 
            if f.profile_id != profile_id
        ]
        return original_count - len(self._feedback_history)
    
    def export_feedback(self) -> list[dict]:
        """Export all feedback as list of dictionaries."""
        return [f.to_dict() for f in self._feedback_history]
    
    def import_feedback(self, data: list[dict]) -> int:
        """
        Import feedback from list of dictionaries.
        Returns number of entries imported.
        """
        count = 0
        for entry_data in data:
            try:
                feedback = FeedbackEntry.from_dict(entry_data)
                self._feedback_history.append(feedback)
                self._update_weights(feedback)
                count += 1
            except Exception:
                continue
        return count
