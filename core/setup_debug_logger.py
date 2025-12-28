"""
Setup Debug Logger - Detailed logging for setup generation and export.
Tracks calculations, conversions, clamping, and ignored parameters.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, Any
import json


class SetupDebugLogger:
    """
    Detailed logger for setup generation debugging.
    
    Logs:
    - Physics calculations (frequencies, forces, etc.)
    - Unit conversions (N/m → clicks, degrees → tenths, etc.)
    - Value clamping (limits enforcement)
    - Ignored parameters (not available for car)
    - Final exported values
    """
    
    def __init__(self, log_path: Optional[Path] = None):
        """
        Initialize debug logger.
        
        Args:
            log_path: Path to log file (default: debug_setup_TIMESTAMP.log)
        """
        if log_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = Path(f"debug_setup_{timestamp}.log")
        
        self.log_path = Path(log_path)
        self.entries = []
        self.start_time = datetime.now()
        
        # Metadata
        self.car_id = None
        self.track_id = None
        self.behavior = None
        self.category = None
    
    def set_metadata(self, car_id: str, track_id: str, behavior: str, category: str):
        """Set setup metadata."""
        self.car_id = car_id
        self.track_id = track_id
        self.behavior = behavior
        self.category = category
    
    def log_calculation(self, param: str, calculated_value: float, unit: str, formula: str = ""):
        """
        Log a physics calculation.
        
        Args:
            param: Parameter name (e.g., "SPRING_RATE_LF")
            calculated_value: Calculated value
            unit: Unit (e.g., "N/m", "Hz", "PSI")
            formula: Optional formula used
        """
        self.entries.append({
            "stage": "calculation",
            "param": param,
            "value": calculated_value,
            "unit": unit,
            "formula": formula,
            "timestamp": datetime.now()
        })
    
    def log_conversion(self, param: str, from_value: float, to_value: Any, reason: str):
        """
        Log a unit conversion.
        
        Args:
            param: Parameter name
            from_value: Original value
            to_value: Converted value
            reason: Reason for conversion (e.g., "Motion ratio 0.9", "degrees × 10")
        """
        self.entries.append({
            "stage": "conversion",
            "param": param,
            "from": from_value,
            "to": to_value,
            "reason": reason,
            "timestamp": datetime.now()
        })
    
    def log_clamp(self, param: str, original: float, clamped: float, limit_type: str, limit_value: float):
        """
        Log value clamping.
        
        Args:
            param: Parameter name
            original: Original value
            clamped: Clamped value
            limit_type: "min" or "max"
            limit_value: Limit value
        """
        self.entries.append({
            "stage": "clamp",
            "param": param,
            "original": original,
            "clamped": clamped,
            "limit_type": limit_type,
            "limit_value": limit_value,
            "timestamp": datetime.now()
        })
    
    def log_ignored(self, param: str, reason: str):
        """
        Log ignored parameter.
        
        Args:
            param: Parameter name
            reason: Reason for ignoring (e.g., "Not found in car setup")
        """
        self.entries.append({
            "stage": "ignored",
            "param": param,
            "reason": reason,
            "timestamp": datetime.now()
        })
    
    def log_exported(self, param: str, value: Any, ac_format: str):
        """
        Log final exported value.
        
        Args:
            param: Parameter name
            value: Final value written to file
            ac_format: AC format (e.g., "[PRESSURE_LF]\nVALUE=26")
        """
        self.entries.append({
            "stage": "exported",
            "param": param,
            "value": value,
            "ac_format": ac_format,
            "timestamp": datetime.now()
        })
    
    def log_behavior_adjustment(self, param: str, base_value: float, adjustment: float, final_value: float, behavior_modifier: str):
        """
        Log behavior-based adjustment.
        
        Args:
            param: Parameter name
            base_value: Base value before adjustment
            adjustment: Adjustment amount
            final_value: Final value after adjustment
            behavior_modifier: Behavior modifier applied (e.g., "suspension_stiffness +0.7")
        """
        self.entries.append({
            "stage": "behavior",
            "param": param,
            "base": base_value,
            "adjustment": adjustment,
            "final": final_value,
            "modifier": behavior_modifier,
            "timestamp": datetime.now()
        })
    
    def log_profile_adjustment(self, param: str, base_value: float, adjustment: float, final_value: float, profile_factor: str):
        """
        Log profile slider adjustment.
        
        Args:
            param: Parameter name
            base_value: Base value before adjustment
            adjustment: Adjustment amount
            final_value: Final value after adjustment
            profile_factor: Profile factor applied (e.g., "rotation 0.8")
        """
        self.entries.append({
            "stage": "profile",
            "param": param,
            "base": base_value,
            "adjustment": adjustment,
            "final": final_value,
            "factor": profile_factor,
            "timestamp": datetime.now()
        })
    
    def export_text(self) -> str:
        """
        Export log as formatted text.
        
        Returns:
            Formatted log string
        """
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append("SETUP GENERATION DEBUG LOG")
        lines.append("=" * 80)
        lines.append(f"Generated: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if self.car_id:
            lines.append(f"Car: {self.car_id}")
        if self.track_id:
            lines.append(f"Track: {self.track_id}")
        if self.behavior:
            lines.append(f"Behavior: {self.behavior}")
        if self.category:
            lines.append(f"Category: {self.category}")
        
        lines.append("=" * 80)
        lines.append("")
        
        # Group by parameter
        params = {}
        for entry in self.entries:
            param = entry.get("param", "unknown")
            if param not in params:
                params[param] = []
            params[param].append(entry)
        
        # Output by parameter
        for param, entries in sorted(params.items()):
            lines.append(f"[{param}]")
            lines.append("-" * 80)
            
            for entry in entries:
                stage = entry["stage"]
                
                if stage == "calculation":
                    lines.append(f"  [CALC] {entry['value']:.4f} {entry['unit']}")
                    if entry.get("formula"):
                        lines.append(f"         Formula: {entry['formula']}")
                
                elif stage == "conversion":
                    lines.append(f"  [CONV] {entry['from']:.4f} → {entry['to']}")
                    lines.append(f"         Reason: {entry['reason']}")
                
                elif stage == "behavior":
                    lines.append(f"  [BEHV] {entry['base']:.4f} + {entry['adjustment']:+.4f} = {entry['final']:.4f}")
                    lines.append(f"         Modifier: {entry['modifier']}")
                
                elif stage == "profile":
                    lines.append(f"  [PROF] {entry['base']:.4f} + {entry['adjustment']:+.4f} = {entry['final']:.4f}")
                    lines.append(f"         Factor: {entry['factor']}")
                
                elif stage == "clamp":
                    lines.append(f"  [CLAMP] {entry['original']:.4f} → {entry['clamped']:.4f}")
                    lines.append(f"          Limit: {entry['limit_type']}={entry['limit_value']:.4f}")
                
                elif stage == "ignored":
                    lines.append(f"  [IGNORE] {entry['reason']}")
                
                elif stage == "exported":
                    lines.append(f"  [EXPORT] VALUE={entry['value']}")
                    if entry.get("ac_format"):
                        lines.append(f"           Format: {entry['ac_format']}")
            
            lines.append("")
        
        # Summary
        lines.append("=" * 80)
        lines.append("SUMMARY")
        lines.append("=" * 80)
        
        total = len(self.entries)
        by_stage = {}
        for entry in self.entries:
            stage = entry["stage"]
            by_stage[stage] = by_stage.get(stage, 0) + 1
        
        lines.append(f"Total entries: {total}")
        for stage, count in sorted(by_stage.items()):
            lines.append(f"  {stage}: {count}")
        
        duration = (datetime.now() - self.start_time).total_seconds()
        lines.append(f"Duration: {duration:.2f}s")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def export_json(self) -> str:
        """
        Export log as JSON.
        
        Returns:
            JSON string
        """
        data = {
            "metadata": {
                "generated": self.start_time.isoformat(),
                "car_id": self.car_id,
                "track_id": self.track_id,
                "behavior": self.behavior,
                "category": self.category
            },
            "entries": []
        }
        
        for entry in self.entries:
            # Convert datetime to string
            entry_copy = dict(entry)
            if "timestamp" in entry_copy:
                entry_copy["timestamp"] = entry_copy["timestamp"].isoformat()
            data["entries"].append(entry_copy)
        
        return json.dumps(data, indent=2)
    
    def save(self, format: str = "text"):
        """
        Save log to file.
        
        Args:
            format: "text" or "json"
        """
        if format == "json":
            content = self.export_json()
            path = self.log_path.with_suffix(".json")
        else:
            content = self.export_text()
            path = self.log_path
        
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[DEBUG LOG] Saved to {path}")
        except Exception as e:
            print(f"[DEBUG LOG] Error saving: {e}")
    
    def print_summary(self):
        """Print summary to console."""
        by_stage = {}
        for entry in self.entries:
            stage = entry["stage"]
            by_stage[stage] = by_stage.get(stage, 0) + 1
        
        print("\n" + "=" * 60)
        print("SETUP DEBUG SUMMARY")
        print("=" * 60)
        print(f"Total entries: {len(self.entries)}")
        for stage, count in sorted(by_stage.items()):
            print(f"  {stage}: {count}")
        print(f"Log file: {self.log_path}")
        print("=" * 60 + "\n")


# Global logger instance (optional convenience)
_global_logger: Optional[SetupDebugLogger] = None


def get_global_logger() -> Optional[SetupDebugLogger]:
    """Get global logger instance."""
    return _global_logger


def set_global_logger(logger: SetupDebugLogger):
    """Set global logger instance."""
    global _global_logger
    _global_logger = logger


def clear_global_logger():
    """Clear global logger instance."""
    global _global_logger
    _global_logger = None
