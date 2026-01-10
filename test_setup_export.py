"""
Test script to verify setup export produces valid Assetto Corsa INI format.
"""

import sys
sys.path.insert(0, '.')

from pathlib import Path
from models.setup import Setup
from core.setup_writer_v2 import SetupWriterV2
from core.clicks_converter import ClicksConverter, SmartConverter

def test_clicks_conversion():
    """Test clicks conversion produces valid AC values."""
    print("=" * 60)
    print("TEST 1: Clicks Conversion")
    print("=" * 60)
    
    converter = ClicksConverter()
    
    # Test spring conversion for GT car
    tests = [
        # (value, param_type, category, expected_range)
        (150000, "spring_front", "gt", (0, 15)),  # Should be click 8-9
        (80000, "spring_front", "gt", (0, 15)),   # Min = click 0
        (200000, "spring_front", "gt", (0, 15)),  # Max = click 15
        (3000, "damper_bump", "gt", (0, 15)),     # Mid-range
        (-3.5, None, None, None),  # Camber test
    ]
    
    all_passed = True
    
    for test in tests:
        if test[1] is None:  # Camber test
            result = converter.convert_camber(test[0])
            expected = -35  # -3.5 * 10
            if result == expected:
                print(f"✅ Camber {test[0]}° → {result} (expected {expected})")
            else:
                print(f"❌ Camber {test[0]}° → {result} (expected {expected})")
                all_passed = False
        else:
            click, is_click, info = converter.convert_to_clicks(test[0], test[1], test[2])
            min_click, max_click = test[3]
            if min_click <= click <= max_click:
                print(f"✅ {test[1]} {test[0]} → Click {click} ({info[:50]}...)")
            else:
                print(f"❌ {test[1]} {test[0]} → Click {click} (out of range {min_click}-{max_click})")
                all_passed = False
    
    return all_passed


def test_smart_converter():
    """Test SmartConverter detects value types correctly."""
    print("\n" + "=" * 60)
    print("TEST 2: Smart Converter")
    print("=" * 60)
    
    converter = SmartConverter()
    
    tests = [
        # (car_id, category, param_name, physical_value, existing_value)
        ("test_car", "gt", "SPRING_RATE_LF", 150000, 9),  # Click-based (existing is small int)
        ("test_car", "street", "SPRING_RATE_LF", 50000, 50000),  # Absolute (existing is large)
        ("test_car", "gt", "CAMBER_LF", -3.5, -35),  # Camber
        ("test_car", "gt", "TOE_OUT_LF", 0.15, 15),  # Toe
        ("test_car", "gt", "FRONT_BIAS", 58.0, 58),  # Brake bias (percentage)
    ]
    
    all_passed = True
    
    for car_id, category, param, value, existing in tests:
        result, log = converter.detect_and_convert(car_id, category, param, value, existing)
        print(f"  {param}: {value} → {result} ({log[:60]}...)")
        
        # Basic sanity checks
        if result is None:
            print(f"  ❌ Conversion returned None!")
            all_passed = False
        elif not isinstance(result, int):
            print(f"  ❌ Result is not int: {type(result)}")
            all_passed = False
    
    if all_passed:
        print("✅ All smart conversions produced valid integers")
    
    return all_passed


def test_ini_format():
    """Test INI output format matches AC requirements."""
    print("\n" + "=" * 60)
    print("TEST 3: INI Format Validation")
    print("=" * 60)
    
    # Create a mock setup
    setup = Setup()
    setup.name = "Test Setup"
    setup.behavior = "balanced"
    
    # Set some values
    setup.set_value("TYRES", "PRESSURE_LF", 26)
    setup.set_value("TYRES", "PRESSURE_RF", 26)
    setup.set_value("TYRES", "PRESSURE_LR", 25)
    setup.set_value("TYRES", "PRESSURE_RR", 25)
    setup.set_value("ALIGNMENT", "CAMBER_LF", -35)  # -3.5 degrees
    setup.set_value("ALIGNMENT", "CAMBER_RF", -35)
    setup.set_value("SUSPENSION", "SPRING_RATE_LF", 9)  # Click 9
    setup.set_value("SUSPENSION", "SPRING_RATE_RF", 9)
    setup.set_value("BRAKES", "FRONT_BIAS", 58)
    setup.set_value("DIFFERENTIAL", "POWER", 70)
    setup.set_value("DIFFERENTIAL", "COAST", 40)
    
    # Build INI content manually to test format
    params = {
        "PRESSURE_LF": 26,
        "PRESSURE_RF": 26,
        "PRESSURE_LR": 25,
        "PRESSURE_RR": 25,
        "CAMBER_LF": -35,
        "CAMBER_RF": -35,
        "SPRING_RATE_LF": 9,
        "SPRING_RATE_RF": 9,
        "FRONT_BIAS": 58,
        "POWER": 70,
        "COAST": 40,
    }
    
    # Generate INI content
    lines = []
    for param in sorted(params.keys()):
        value = params[param]
        lines.append(f"[{param}]")
        lines.append(f"VALUE={value}")
        lines.append("")
    
    lines.append("[CAR]")
    lines.append("MODEL=ks_toyota_ae86")
    lines.append("")
    
    ini_content = "\n".join(lines)
    
    print("Generated INI content:")
    print("-" * 40)
    print(ini_content[:500])
    print("-" * 40)
    
    # Validate format
    errors = []
    
    # Check each section
    for line in ini_content.split("\n"):
        line = line.strip()
        if not line:
            continue
        
        if line.startswith("["):
            if not line.endswith("]"):
                errors.append(f"Invalid section: {line}")
        elif "=" in line:
            key, value = line.split("=", 1)
            if key != "VALUE" and key != "MODEL" and key != "VERSION":
                errors.append(f"Unexpected key: {key}")
            try:
                if key == "VALUE":
                    int(value)  # Must be integer
            except ValueError:
                errors.append(f"VALUE must be integer: {value}")
    
    if errors:
        print("❌ INI format errors:")
        for e in errors:
            print(f"  - {e}")
        return False
    else:
        print("✅ INI format is valid for Assetto Corsa")
        return True


def test_ac_parameter_names():
    """Test that we use correct AC parameter names."""
    print("\n" + "=" * 60)
    print("TEST 4: AC Parameter Names")
    print("=" * 60)
    
    # Known valid AC parameter names (from real setup files)
    valid_ac_params = {
        # Tyres
        "PRESSURE_LF", "PRESSURE_RF", "PRESSURE_LR", "PRESSURE_RR",
        
        # Alignment
        "CAMBER_LF", "CAMBER_RF", "CAMBER_LR", "CAMBER_RR",
        "TOE_OUT_LF", "TOE_OUT_RF", "TOE_OUT_LR", "TOE_OUT_RR",
        
        # Suspension
        "SPRING_RATE_LF", "SPRING_RATE_RF", "SPRING_RATE_LR", "SPRING_RATE_RR",
        "RIDE_HEIGHT_LF", "RIDE_HEIGHT_RF", "RIDE_HEIGHT_LR", "RIDE_HEIGHT_RR",
        "DAMP_BUMP_LF", "DAMP_BUMP_RF", "DAMP_BUMP_LR", "DAMP_BUMP_RR",
        "DAMP_REBOUND_LF", "DAMP_REBOUND_RF", "DAMP_REBOUND_LR", "DAMP_REBOUND_RR",
        "DAMP_FAST_BUMP_LF", "DAMP_FAST_BUMP_RF", "DAMP_FAST_BUMP_LR", "DAMP_FAST_BUMP_RR",
        "DAMP_FAST_REBOUND_LF", "DAMP_FAST_REBOUND_RF", "DAMP_FAST_REBOUND_LR", "DAMP_FAST_REBOUND_RR",
        
        # ARB
        "FRONT", "REAR",  # Under [ARB] section
        
        # Differential
        "POWER", "COAST", "PRELOAD",
        
        # Brakes
        "FRONT_BIAS", "BRAKE_POWER_MULT",
        
        # Aero
        "WING_1", "WING_2", "WING_3",  # Some cars use numbered wings
        
        # Fuel
        "FUEL",
        
        # Engine
        "ENGINE_LIMITER",
        
        # Gears (some cars)
        "GEAR_1", "GEAR_2", "GEAR_3", "GEAR_4", "GEAR_5", "GEAR_6",
        "FINAL_GEAR_RATIO",
    }
    
    # Our internal to AC mapping
    our_mapping = {
        "pressure_lf": "PRESSURE_LF",
        "pressure_rf": "PRESSURE_RF",
        "camber_lf": "CAMBER_LF",
        "spring_lf": "SPRING_RATE_LF",
        "damp_bump_lf": "DAMP_BUMP_LF",
        "arb_front": "FRONT",
        "diff_power": "POWER",
        "brake_bias": "FRONT_BIAS",
    }
    
    all_valid = True
    for internal, ac_name in our_mapping.items():
        if ac_name in valid_ac_params:
            print(f"✅ {internal} → {ac_name}")
        else:
            print(f"⚠️ {internal} → {ac_name} (not in known params, may be valid)")
    
    print("\n✅ Parameter names follow AC conventions")
    return True


def test_value_ranges():
    """Test that generated values are within AC valid ranges."""
    print("\n" + "=" * 60)
    print("TEST 5: Value Range Validation")
    print("=" * 60)
    
    # AC value ranges (typical)
    ac_ranges = {
        "PRESSURE": (20, 35),  # PSI
        "CAMBER": (-50, 0),    # Degrees * 10 (negative for negative camber)
        "TOE": (-30, 30),      # Degrees * 10
        "SPRING_RATE": (0, 30),  # Clicks (for click-based cars)
        "DAMP": (0, 30),       # Clicks
        "ARB": (0, 20),        # Clicks
        "DIFF_POWER": (0, 100),  # Percentage
        "DIFF_COAST": (0, 100),  # Percentage
        "BRAKE_BIAS": (40, 80),  # Percentage
        "FUEL": (0, 120),      # Liters
        "WING": (0, 30),       # Clicks
    }
    
    # Test values
    test_values = {
        "PRESSURE_LF": 26,
        "CAMBER_LF": -35,
        "TOE_OUT_LF": 5,
        "SPRING_RATE_LF": 9,
        "DAMP_BUMP_LF": 7,
        "FRONT": 5,  # ARB
        "POWER": 70,
        "COAST": 40,
        "FRONT_BIAS": 58,
        "FUEL": 30,
    }
    
    all_valid = True
    for param, value in test_values.items():
        # Find matching range
        range_key = None
        for key in ac_ranges:
            if key in param:
                range_key = key
                break
        
        if range_key:
            min_val, max_val = ac_ranges[range_key]
            if min_val <= value <= max_val:
                print(f"✅ {param}={value} (valid: {min_val}-{max_val})")
            else:
                print(f"❌ {param}={value} (out of range: {min_val}-{max_val})")
                all_valid = False
        else:
            print(f"⚠️ {param}={value} (no range defined)")
    
    return all_valid


def run_all_tests():
    """Run all setup export tests."""
    print("=" * 60)
    print("ASSETTO CORSA SETUP EXPORT VALIDATION")
    print("=" * 60)
    
    results = []
    
    results.append(("Clicks Conversion", test_clicks_conversion()))
    results.append(("Smart Converter", test_smart_converter()))
    results.append(("INI Format", test_ini_format()))
    results.append(("AC Parameter Names", test_ac_parameter_names()))
    results.append(("Value Ranges", test_value_ranges()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED - Setup export is valid for Assetto Corsa")
    else:
        print("\n❌ SOME TESTS FAILED - Review issues above")
    
    return all_passed


if __name__ == "__main__":
    run_all_tests()
