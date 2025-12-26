"""
Car Data Loader - Utility to load enriched car data from JSON.
Provides physical parameters for V2.1 setup generation.
"""

import json
from pathlib import Path
from typing import Dict, Optional


def load_car_data(car_id: str) -> Dict:
    """
    Load enriched data for a specific car.
    
    Args:
        car_id: Car identifier (e.g., "ks_porsche_911_gt3_r_2016")
    
    Returns:
        Dict with physical parameters or empty dict if not found
        Keys: wheelbase_mm, max_torque_nm, motion_ratio_front, motion_ratio_rear, etc.
    """
    # Try enriched data first
    json_path = Path(__file__).parent.parent / "data" / "cars_enriched.json"
    
    if not json_path.exists():
        # Try example file
        json_path = Path(__file__).parent.parent / "data" / "cars_enriched_example.json"
    
    if not json_path.exists():
        print(f"[CAR DATA] Enriched data not found at {json_path}")
        return {}
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Search for car
        for car in data.get("cars", []):
            if car.get("car_id") == car_id:
                print(f"[CAR DATA] Loaded enriched data for {car_id}")
                return car
        
        print(f"[CAR DATA] Car {car_id} not found in enriched data")
        return {}
        
    except Exception as e:
        print(f"[CAR DATA] Error loading enriched data: {e}")
        return {}


def get_motion_ratios(car_id: str, category: str = "street") -> Dict[str, float]:
    """
    Get motion ratios for a car.
    
    Args:
        car_id: Car identifier
        category: Fallback category if car not found
    
    Returns:
        Dict with keys: motion_ratio_front, motion_ratio_rear
    """
    car_data = load_car_data(car_id)
    
    if car_data and "motion_ratio_front" in car_data:
        return {
            "motion_ratio_front": car_data["motion_ratio_front"],
            "motion_ratio_rear": car_data["motion_ratio_rear"]
        }
    
    # Fallback to category defaults
    from core.physics_refiner import MOTION_RATIOS
    ratios = MOTION_RATIOS.get(category, MOTION_RATIOS["street"])
    
    return {
        "motion_ratio_front": ratios["front"],
        "motion_ratio_rear": ratios["rear"]
    }


def get_wheelbase(car_id: str) -> float:
    """
    Get wheelbase for a car.
    
    Args:
        car_id: Car identifier
    
    Returns:
        Wheelbase in mm (default 2600mm if not found)
    """
    car_data = load_car_data(car_id)
    return car_data.get("wheelbase_mm", 2600.0)


def get_max_torque(car_id: str) -> float:
    """
    Get max torque for a car.
    
    Args:
        car_id: Car identifier
    
    Returns:
        Max torque in Nm (default 400Nm if not found)
    """
    car_data = load_car_data(car_id)
    return car_data.get("max_torque_nm", 400.0)
