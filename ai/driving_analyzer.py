"""
Driving Analyzer - Analyzes driving style from telemetry data.
Detects if driver is aggressive, smooth, or drift-oriented.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from collections import deque
from enum import Enum
import time


class DrivingStyle(Enum):
    """Detected driving styles."""
    UNKNOWN = "unknown"
    SMOOTH = "smooth"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    DRIFT = "drift"


@dataclass
class DrivingMetrics:
    """Metrics used to analyze driving style."""
    
    # Throttle behavior
    avg_throttle: float = 0.0
    throttle_smoothness: float = 0.0  # 0 = jerky, 1 = smooth
    full_throttle_pct: float = 0.0  # % time at 100% throttle
    
    # Brake behavior
    avg_brake_pressure: float = 0.0
    brake_smoothness: float = 0.0
    trail_braking_score: float = 0.0  # How much brake is used while turning
    
    # Steering behavior
    steering_smoothness: float = 0.0
    counter_steer_count: int = 0  # Number of counter-steers detected
    
    # G-forces
    avg_lateral_g: float = 0.0
    max_lateral_g: float = 0.0
    avg_longitudinal_g: float = 0.0
    
    # Slide detection
    slide_time_pct: float = 0.0  # % time in slide
    avg_slide_angle: float = 0.0
    drift_score: float = 0.0  # 0-1, how much drifting
    
    # Overall scores
    aggression_score: float = 0.5
    smoothness_score: float = 0.5
    
    # Detected style
    style: DrivingStyle = DrivingStyle.UNKNOWN
    confidence: float = 0.0


@dataclass
class TelemetrySample:
    """A single telemetry sample."""
    timestamp: float
    speed: float
    throttle: float
    brake: float
    steering: float  # -1 to 1
    g_lateral: float
    g_longitudinal: float
    slip_angle: float = 0.0  # Estimated from g-forces


class DrivingAnalyzer:
    """
    Analyzes driving style from live telemetry.
    Uses rolling window of samples to detect patterns.
    """
    
    # Analysis window size (samples)
    WINDOW_SIZE = 500  # ~10 seconds at 50Hz
    
    # Thresholds
    SLIDE_THRESHOLD = 0.3  # G-force threshold for slide detection
    COUNTER_STEER_THRESHOLD = 0.15  # Steering change threshold
    AGGRESSIVE_THROTTLE_THRESHOLD = 0.8
    
    def __init__(self):
        """Initialize the analyzer."""
        self._samples: deque = deque(maxlen=self.WINDOW_SIZE)
        self._metrics = DrivingMetrics()
        self._last_analysis = 0.0
        self._analysis_interval = 2.0  # Analyze every 2 seconds
        
        # For derivative calculations
        self._prev_throttle = 0.0
        self._prev_brake = 0.0
        self._prev_steering = 0.0
        
        # Counters
        self._counter_steers = 0
        self._slide_samples = 0
    
    def add_sample(self, speed: float, throttle: float, brake: float,
                   steering: float, g_lat: float, g_lon: float) -> Optional[DrivingMetrics]:
        """
        Add a telemetry sample and optionally return updated analysis.
        
        Args:
            speed: Speed in km/h
            throttle: Throttle position 0-1
            brake: Brake position 0-1
            steering: Steering position -1 to 1
            g_lat: Lateral G-force
            g_lon: Longitudinal G-force
        
        Returns:
            Updated metrics if analysis was performed, None otherwise
        """
        now = time.time()
        
        # Estimate slip angle from lateral G and speed
        slip_angle = 0.0
        if speed > 20:  # Only calculate at reasonable speeds
            # Simplified slip angle estimation
            expected_g = abs(steering) * (speed / 100) * 0.5
            if abs(g_lat) > expected_g + 0.2:
                slip_angle = (abs(g_lat) - expected_g) * 10  # Rough degrees
        
        sample = TelemetrySample(
            timestamp=now,
            speed=speed,
            throttle=throttle,
            brake=brake,
            steering=steering,
            g_lateral=g_lat,
            g_longitudinal=g_lon,
            slip_angle=slip_angle
        )
        
        self._samples.append(sample)
        
        # Detect counter-steering
        steering_delta = steering - self._prev_steering
        if abs(steering_delta) > self.COUNTER_STEER_THRESHOLD:
            # Check if it's opposite to lateral G (counter-steer)
            if (steering_delta > 0 and g_lat < -0.2) or (steering_delta < 0 and g_lat > 0.2):
                self._counter_steers += 1
        
        # Detect slide
        if abs(g_lat) > self.SLIDE_THRESHOLD and speed > 30:
            self._slide_samples += 1
        
        # Update previous values
        self._prev_throttle = throttle
        self._prev_brake = brake
        self._prev_steering = steering
        
        # Perform analysis periodically
        if now - self._last_analysis >= self._analysis_interval:
            self._last_analysis = now
            return self._analyze()
        
        return None
    
    def _analyze(self) -> DrivingMetrics:
        """Perform full analysis on current sample window."""
        if len(self._samples) < 50:
            return self._metrics
        
        samples = list(self._samples)
        n = len(samples)
        
        # Calculate throttle metrics
        throttles = [s.throttle for s in samples]
        self._metrics.avg_throttle = sum(throttles) / n
        self._metrics.full_throttle_pct = sum(1 for t in throttles if t > 0.95) / n
        
        # Throttle smoothness (inverse of variance in changes)
        throttle_changes = [abs(throttles[i] - throttles[i-1]) for i in range(1, n)]
        avg_change = sum(throttle_changes) / len(throttle_changes) if throttle_changes else 0
        self._metrics.throttle_smoothness = max(0, 1 - avg_change * 10)
        
        # Calculate brake metrics
        brakes = [s.brake for s in samples]
        self._metrics.avg_brake_pressure = sum(brakes) / n
        
        brake_changes = [abs(brakes[i] - brakes[i-1]) for i in range(1, n)]
        avg_brake_change = sum(brake_changes) / len(brake_changes) if brake_changes else 0
        self._metrics.brake_smoothness = max(0, 1 - avg_brake_change * 10)
        
        # Trail braking score (brake while turning)
        trail_samples = sum(1 for s in samples if s.brake > 0.1 and abs(s.steering) > 0.2)
        self._metrics.trail_braking_score = trail_samples / n
        
        # Steering smoothness
        steerings = [s.steering for s in samples]
        steering_changes = [abs(steerings[i] - steerings[i-1]) for i in range(1, n)]
        avg_steer_change = sum(steering_changes) / len(steering_changes) if steering_changes else 0
        self._metrics.steering_smoothness = max(0, 1 - avg_steer_change * 5)
        
        # Counter-steer count
        self._metrics.counter_steer_count = self._counter_steers
        
        # G-force metrics
        lat_gs = [abs(s.g_lateral) for s in samples]
        lon_gs = [abs(s.g_longitudinal) for s in samples]
        
        self._metrics.avg_lateral_g = sum(lat_gs) / n
        self._metrics.max_lateral_g = max(lat_gs)
        self._metrics.avg_longitudinal_g = sum(lon_gs) / n
        
        # Slide metrics
        self._metrics.slide_time_pct = self._slide_samples / n
        
        slip_angles = [s.slip_angle for s in samples if s.slip_angle > 0]
        self._metrics.avg_slide_angle = sum(slip_angles) / len(slip_angles) if slip_angles else 0
        
        # Drift score (combination of slide time, counter-steers, and maintained slides)
        drift_factors = [
            self._metrics.slide_time_pct * 2,
            min(self._counter_steers / 20, 1.0),
            min(self._metrics.avg_slide_angle / 15, 1.0)
        ]
        self._metrics.drift_score = sum(drift_factors) / 3
        
        # Calculate overall scores
        self._calculate_scores()
        
        # Determine style
        self._determine_style()
        
        # Reset counters for next window
        self._counter_steers = 0
        self._slide_samples = 0
        
        return self._metrics
    
    def _calculate_scores(self):
        """Calculate aggression and smoothness scores."""
        # Aggression score based on:
        # - High throttle usage
        # - Hard braking
        # - High G-forces
        # - Quick inputs
        
        aggression_factors = [
            self._metrics.full_throttle_pct,
            self._metrics.avg_brake_pressure * 2,
            min(self._metrics.max_lateral_g / 1.5, 1.0),
            1 - self._metrics.throttle_smoothness,
            1 - self._metrics.brake_smoothness
        ]
        self._metrics.aggression_score = sum(aggression_factors) / len(aggression_factors)
        
        # Smoothness score based on:
        # - Smooth throttle
        # - Smooth braking
        # - Smooth steering
        # - Trail braking (indicates skill)
        
        smoothness_factors = [
            self._metrics.throttle_smoothness,
            self._metrics.brake_smoothness,
            self._metrics.steering_smoothness,
            self._metrics.trail_braking_score
        ]
        self._metrics.smoothness_score = sum(smoothness_factors) / len(smoothness_factors)
    
    def _determine_style(self):
        """Determine the driving style from metrics."""
        drift = self._metrics.drift_score
        aggression = self._metrics.aggression_score
        smoothness = self._metrics.smoothness_score
        
        # Drift style: high drift score
        if drift > 0.4:
            self._metrics.style = DrivingStyle.DRIFT
            self._metrics.confidence = min(drift * 1.5, 1.0)
        
        # Aggressive style: high aggression, lower smoothness
        elif aggression > 0.6 and smoothness < 0.5:
            self._metrics.style = DrivingStyle.AGGRESSIVE
            self._metrics.confidence = aggression
        
        # Smooth style: high smoothness, lower aggression
        elif smoothness > 0.6 and aggression < 0.4:
            self._metrics.style = DrivingStyle.SMOOTH
            self._metrics.confidence = smoothness
        
        # Balanced: everything moderate
        else:
            self._metrics.style = DrivingStyle.BALANCED
            self._metrics.confidence = 0.5 + abs(0.5 - aggression) + abs(0.5 - smoothness)
            self._metrics.confidence = min(self._metrics.confidence / 2, 1.0)
    
    def get_metrics(self) -> DrivingMetrics:
        """Get current driving metrics."""
        return self._metrics
    
    def get_style(self) -> DrivingStyle:
        """Get detected driving style."""
        return self._metrics.style
    
    def get_recommendation(self) -> str:
        """Get setup recommendation based on detected style."""
        style = self._metrics.style
        
        recommendations = {
            DrivingStyle.UNKNOWN: "Continue à rouler pour que j'analyse ton style...",
            DrivingStyle.SMOOTH: "Style fluide détecté! Je recommande le mode 'Safe' ou 'Balanced' pour maximiser ton grip.",
            DrivingStyle.BALANCED: "Style équilibré! Le mode 'Balanced' te conviendra parfaitement.",
            DrivingStyle.AGGRESSIVE: "Style agressif détecté! Le mode 'Attack' avec suspension ferme te donnera la réactivité que tu cherches.",
            DrivingStyle.DRIFT: "Style drift détecté! Le mode 'Drift' avec diff serré et arrière glissant est fait pour toi!"
        }
        
        return recommendations.get(style, "")
    
    def reset(self):
        """Reset the analyzer."""
        self._samples.clear()
        self._metrics = DrivingMetrics()
        self._counter_steers = 0
        self._slide_samples = 0
        self._prev_throttle = 0.0
        self._prev_brake = 0.0
        self._prev_steering = 0.0
