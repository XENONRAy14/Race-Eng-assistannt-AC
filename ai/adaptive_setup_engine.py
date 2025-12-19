"""
Adaptive Setup Engine - Adjusts setups based on track conditions and learning.
Implements ideas 5, 17, and 18 from improvement suggestions.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import json
from pathlib import Path

from models.setup import Setup
from models.car import Car
from models.track import Track


@dataclass
class TrackConditions:
    """Current track conditions."""
    temperature: float = 25.0  # Celsius
    track_temp: float = 30.0  # Celsius
    weather: str = "dry"  # dry, wet, light_rain, heavy_rain
    time_of_day: str = "day"  # day, dusk, night
    grip_level: float = 1.0  # 0.0 to 1.0


@dataclass
class SetupPerformance:
    """Performance data for a setup."""
    setup_id: int
    lap_time: float
    consistency: float  # Standard deviation of lap times
    tire_wear: float
    fuel_consumption: float
    conditions: TrackConditions
    timestamp: datetime


class AdaptiveSetupEngine:
    """
    Advanced setup engine that learns from your driving and adapts to conditions.
    
    Features:
    - Automatic adjustment based on temperature and weather
    - Learning from your lap times and driving style
    - Comparison with community best times
    """
    
    def __init__(self, data_dir: Path = None):
        """Initialize the adaptive engine."""
        if data_dir is None:
            data_dir = Path.home() / "Documents" / "Assetto Corsa" / "race_engineer_data"
        
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.performance_history: list[SetupPerformance] = []
        self.learning_data = {}
        
        self._load_learning_data()
    
    def _load_learning_data(self):
        """Load learning data from disk."""
        learning_file = self.data_dir / "learning_data.json"
        if learning_file.exists():
            try:
                with open(learning_file, "r", encoding="utf-8") as f:
                    self.learning_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.learning_data = {}
    
    def _save_learning_data(self):
        """Save learning data to disk."""
        learning_file = self.data_dir / "learning_data.json"
        try:
            with open(learning_file, "w", encoding="utf-8") as f:
                json.dump(self.learning_data, f, indent=2)
        except IOError:
            pass
    
    def adapt_setup_to_conditions(
        self,
        setup: Setup,
        conditions: TrackConditions,
        car: Car,
        track: Track
    ) -> Setup:
        """
        Adapt a setup based on current track conditions.
        
        Adjustments:
        - Temperature -> Tire pressure
        - Weather -> Aero, suspension stiffness
        - Track type -> Differential, alignment
        """
        adapted = setup
        
        # Temperature adjustments
        temp_diff = conditions.temperature - 25.0  # 25°C is baseline
        track_temp_diff = conditions.track_temp - 30.0  # 30°C is baseline
        
        # Tire pressure adjustment (0.1 PSI per 5°C)
        pressure_adjustment = (temp_diff + track_temp_diff) / 10.0
        
        if "TYRES" in adapted.sections:
            for key in ["PRESSURE_LF", "PRESSURE_RF", "PRESSURE_LR", "PRESSURE_RR"]:
                current = adapted.sections["TYRES"].get(key, 26.0)
                adapted.sections["TYRES"].set(key, current + pressure_adjustment)
        
        # Weather adjustments
        if conditions.weather in ["wet", "light_rain", "heavy_rain"]:
            # Wet conditions: softer suspension, more aero
            if "SUSPENSION" in adapted.sections:
                # Reduce spring rates by 10%
                for key in ["SPRING_RATE_LF", "SPRING_RATE_RF", "SPRING_RATE_LR", "SPRING_RATE_RR"]:
                    current = adapted.sections["SUSPENSION"].get(key, 80000)
                    adapted.sections["SUSPENSION"].set(key, int(current * 0.9))
            
            if "AERO" in adapted.sections:
                # Increase downforce for wet grip
                wing_front = adapted.sections["AERO"].get("WING_FRONT", 0)
                wing_rear = adapted.sections["AERO"].get("WING_REAR", 0)
                adapted.sections["AERO"].set("WING_FRONT", min(wing_front + 2, 10))
                adapted.sections["AERO"].set("WING_REAR", min(wing_rear + 3, 10))
            
            # Increase tire pressure for wet (less contact patch deformation)
            if "TYRES" in adapted.sections:
                for key in ["PRESSURE_LF", "PRESSURE_RF", "PRESSURE_LR", "PRESSURE_RR"]:
                    current = adapted.sections["TYRES"].get(key, 26.0)
                    adapted.sections["TYRES"].set(key, current + 1.5)
        
        # Track-specific adjustments
        if track.track_type == "touge":
            # Touge: softer suspension, more rotation
            if "DIFFERENTIAL" in adapted.sections:
                # More coast for better rotation
                coast = adapted.sections["DIFFERENTIAL"].get("COAST", 30.0)
                adapted.sections["DIFFERENTIAL"].set("COAST", min(coast + 10.0, 80.0))
        
        elif track.track_type == "circuit":
            # Circuit: stiffer for high-speed stability
            if "SUSPENSION" in adapted.sections:
                for key in ["SPRING_RATE_LF", "SPRING_RATE_RF"]:
                    current = adapted.sections["SUSPENSION"].get(key, 80000)
                    adapted.sections["SUSPENSION"].set(key, int(current * 1.1))
        
        # Add notes about adaptations
        adapted.notes += f"\n\n🌡️ Adapté aux conditions:\n"
        adapted.notes += f"- Température: {conditions.temperature}°C\n"
        adapted.notes += f"- Température piste: {conditions.track_temp}°C\n"
        adapted.notes += f"- Météo: {conditions.weather}\n"
        adapted.notes += f"- Ajustement pression: {pressure_adjustment:+.1f} PSI\n"
        
        return adapted
    
    def record_performance(
        self,
        setup: Setup,
        lap_time: float,
        consistency: float,
        conditions: TrackConditions
    ):
        """Record performance data for learning."""
        perf = SetupPerformance(
            setup_id=setup.setup_id or 0,
            lap_time=lap_time,
            consistency=consistency,
            tire_wear=0.0,  # TODO: Get from telemetry
            fuel_consumption=0.0,  # TODO: Get from telemetry
            conditions=conditions,
            timestamp=datetime.now()
        )
        
        self.performance_history.append(perf)
        
        # Update learning data
        key = f"{setup.car_id}_{setup.track_id}"
        if key not in self.learning_data:
            self.learning_data[key] = {
                "best_time": lap_time,
                "best_setup_params": self._extract_key_params(setup),
                "total_laps": 1,
                "avg_consistency": consistency
            }
        else:
            data = self.learning_data[key]
            if lap_time < data["best_time"]:
                data["best_time"] = lap_time
                data["best_setup_params"] = self._extract_key_params(setup)
            data["total_laps"] += 1
            data["avg_consistency"] = (data["avg_consistency"] + consistency) / 2
        
        self._save_learning_data()
    
    def _extract_key_params(self, setup: Setup) -> dict:
        """Extract key parameters from a setup for learning."""
        params = {}
        
        if "TYRES" in setup.sections:
            params["tire_pressure_avg"] = sum([
                setup.sections["TYRES"].get(k, 26.0)
                for k in ["PRESSURE_LF", "PRESSURE_RF", "PRESSURE_LR", "PRESSURE_RR"]
            ]) / 4
        
        if "SUSPENSION" in setup.sections:
            params["spring_rate_front"] = (
                setup.sections["SUSPENSION"].get("SPRING_RATE_LF", 80000) +
                setup.sections["SUSPENSION"].get("SPRING_RATE_RF", 80000)
            ) / 2
            params["spring_rate_rear"] = (
                setup.sections["SUSPENSION"].get("SPRING_RATE_LR", 70000) +
                setup.sections["SUSPENSION"].get("SPRING_RATE_RR", 70000)
            ) / 2
        
        if "DIFFERENTIAL" in setup.sections:
            params["diff_power"] = setup.sections["DIFFERENTIAL"].get("POWER", 40.0)
            params["diff_coast"] = setup.sections["DIFFERENTIAL"].get("COAST", 30.0)
        
        if "AERO" in setup.sections:
            params["wing_front"] = setup.sections["AERO"].get("WING_FRONT", 0)
            params["wing_rear"] = setup.sections["AERO"].get("WING_REAR", 0)
        
        return params
    
    def get_learned_adjustments(self, car_id: str, track_id: str) -> dict:
        """Get learned adjustments for a car/track combo."""
        key = f"{car_id}_{track_id}"
        
        if key not in self.learning_data:
            return {}
        
        data = self.learning_data[key]
        
        return {
            "best_time": data["best_time"],
            "total_laps": data["total_laps"],
            "avg_consistency": data["avg_consistency"],
            "recommended_params": data["best_setup_params"],
            "confidence": min(data["total_laps"] / 50.0, 1.0)  # Max confidence at 50 laps
        }
    
    def apply_learned_adjustments(self, setup: Setup) -> Setup:
        """Apply learned adjustments to a setup."""
        learned = self.get_learned_adjustments(setup.car_id, setup.track_id)
        
        if not learned or learned["confidence"] < 0.2:
            # Not enough data yet
            return setup
        
        params = learned["recommended_params"]
        confidence = learned["confidence"]
        
        # Apply learned parameters with confidence weighting
        if "tire_pressure_avg" in params and "TYRES" in setup.sections:
            target = params["tire_pressure_avg"]
            for key in ["PRESSURE_LF", "PRESSURE_RF", "PRESSURE_LR", "PRESSURE_RR"]:
                current = setup.sections["TYRES"].get(key, 26.0)
                # Blend between current and learned based on confidence
                adjusted = current * (1 - confidence) + target * confidence
                setup.sections["TYRES"].set(key, adjusted)
        
        if "spring_rate_front" in params and "SUSPENSION" in setup.sections:
            target = params["spring_rate_front"]
            for key in ["SPRING_RATE_LF", "SPRING_RATE_RF"]:
                current = setup.sections["SUSPENSION"].get(key, 80000)
                adjusted = int(current * (1 - confidence) + target * confidence)
                setup.sections["SUSPENSION"].set(key, adjusted)
        
        if "spring_rate_rear" in params and "SUSPENSION" in setup.sections:
            target = params["spring_rate_rear"]
            for key in ["SPRING_RATE_LR", "SPRING_RATE_RR"]:
                current = setup.sections["SUSPENSION"].get(key, 70000)
                adjusted = int(current * (1 - confidence) + target * confidence)
                setup.sections["SUSPENSION"].set(key, adjusted)
        
        # Add learning notes
        setup.notes += f"\n\n🤖 Optimisé par IA (confiance: {confidence*100:.0f}%):\n"
        setup.notes += f"- Basé sur {learned['total_laps']} tours\n"
        setup.notes += f"- Meilleur temps: {learned['best_time']:.3f}s\n"
        setup.notes += f"- Constance moyenne: {learned['avg_consistency']:.3f}s\n"
        
        return setup
    
    def record_lap(self, car_id: str, track_id: str, lap_time: float, conditions: TrackConditions = None):
        """
        Record a lap time for learning.
        
        Args:
            car_id: Car identifier
            track_id: Track identifier
            lap_time: Lap time in seconds
            conditions: Track conditions (optional)
        """
        key = f"{car_id}_{track_id}"
        
        # Initialize data structure if needed
        if key not in self.learning_data:
            self.learning_data[key] = {
                "best_time": lap_time,
                "total_laps": 0,
                "lap_times": [],
                "avg_consistency": 0.0,
                "best_setup_params": {}
            }
        
        data = self.learning_data[key]
        
        # Update lap data
        data["total_laps"] += 1
        data["lap_times"].append(lap_time)
        
        # Keep only last 50 laps for consistency calculation
        if len(data["lap_times"]) > 50:
            data["lap_times"] = data["lap_times"][-50:]
        
        # Update best time
        if lap_time < data["best_time"]:
            data["best_time"] = lap_time
        
        # Calculate consistency (standard deviation)
        if len(data["lap_times"]) > 1:
            avg = sum(data["lap_times"]) / len(data["lap_times"])
            variance = sum((t - avg) ** 2 for t in data["lap_times"]) / len(data["lap_times"])
            data["avg_consistency"] = variance ** 0.5
        
        # Save to disk
        self._save_learning_data()
    
    def get_performance_stats(self, car_id: str, track_id: str) -> dict:
        """Get performance statistics for comparison."""
        key = f"{car_id}_{track_id}"
        
        if key not in self.learning_data:
            return {
                "has_data": False,
                "message": "Pas encore de données pour cette combinaison"
            }
        
        data = self.learning_data[key]
        
        # Calculate percentile (mock data for now - would need community data)
        # For now, assume average is 5% slower than best
        community_best = data["best_time"] * 0.95
        percentile = min(100, max(0, 100 - (data["best_time"] - community_best) / community_best * 100))
        
        return {
            "has_data": True,
            "your_best": data["best_time"],
            "total_laps": data["total_laps"],
            "consistency": data["avg_consistency"],
            "percentile": percentile,
            "rank_estimate": f"Top {100-percentile:.0f}%",
            "improvement_potential": max(0, data["best_time"] - community_best)
        }
