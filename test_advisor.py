"""
Test the Race Engineer Advisor system.
"""

import sys
sys.path.insert(0, '.')

from models.car import Car
from models.track import Track
from models.setup import Setup
from core.race_engineer_advisor import RaceEngineerAdvisor, CarAnalyzer, TrackDatabase


def test_car_analysis():
    """Test car characteristics analysis."""
    print("=" * 60)
    print("TEST: Car Analysis")
    print("=" * 60)
    
    analyzer = CarAnalyzer()
    
    test_cars = [
        Car(car_id="ks_nissan_gtr", name="Nissan GT-R", power_hp=550, weight_kg=1750, drivetrain="AWD"),
        Car(car_id="ks_toyota_ae86", name="Toyota AE86", power_hp=130, weight_kg=940, drivetrain="RWD"),
        Car(car_id="ks_mazda_rx7_tuned", name="Mazda RX-7 FC Tuned", power_hp=350, weight_kg=1150, drivetrain="RWD"),
        Car(car_id="ks_honda_s2000", name="Honda S2000", power_hp=240, weight_kg=1250, drivetrain="RWD"),
        Car(car_id="bmw_m3_e30_drift", name="BMW M3 E30 Drift", power_hp=320, weight_kg=1200, drivetrain="RWD"),
    ]
    
    for car in test_cars:
        chars = analyzer.analyze(car)
        print(f"\n{car.name}:")
        print(f"  Power: {chars.power_hp}hp")
        print(f"  Weight: {chars.weight_kg}kg")
        print(f"  P/W Ratio: {chars.power_to_weight:.1f} kg/hp")
        print(f"  Drivetrain: {chars.drivetrain}")
        print(f"  Turbo: {'Yes' if chars.is_turbo else 'No'}")
        print(f"  Category: {chars.category}")
    
    return True


def test_track_knowledge():
    """Test track knowledge database."""
    print("\n" + "=" * 60)
    print("TEST: Track Knowledge")
    print("=" * 60)
    
    db = TrackDatabase()
    
    test_tracks = [
        Track(track_id="akina_downhill", name="Akina Downhill"),
        Track(track_id="usui_pass", name="Usui Pass"),
        Track(track_id="irohazaka", name="Irohazaka"),
        Track(track_id="shutoko_revival", name="Shutoko Revival Project"),
        Track(track_id="ks_nurburgring", name="Nurburgring GP"),
    ]
    
    for track in test_tracks:
        knowledge = db.get_track_knowledge(track)
        print(f"\n{track.name}:")
        print(f"  Type: {knowledge.type}")
        print(f"  Hairpins: {'Yes' if knowledge.has_tight_hairpins else 'No'}")
        print(f"  High speed: {'Yes' if knowledge.has_high_speed_sections else 'No'}")
        print(f"  Cliff edges: {'Yes' if knowledge.has_cliff_edges else 'No'}")
        if knowledge.overtake_zones:
            print(f"  Overtake zones: {len(knowledge.overtake_zones)}")
    
    return True


def test_setup_advice():
    """Test setup-based advice."""
    print("\n" + "=" * 60)
    print("TEST: Setup-Based Advice")
    print("=" * 60)
    
    from core.race_engineer_advisor import SetupAnalyzer
    
    analyzer = SetupAnalyzer()
    
    # Create aggressive setup
    setup = Setup()
    setup.set_value("DIFFERENTIAL", "POWER", 80)
    setup.set_value("DIFFERENTIAL", "COAST", 65)
    setup.set_value("BRAKES", "FRONT_BIAS", 65)
    setup.set_value("ARB", "FRONT", 5)
    setup.set_value("ARB", "REAR", 8)
    setup.set_value("ALIGNMENT", "CAMBER_LF", -45)  # -4.5 degrees in AC format
    setup.set_value("TYRES", "PRESSURE_LF", 23)
    
    advice_list = analyzer.analyze(setup)
    
    print(f"\nGenerated {len(advice_list)} setup-based advice items:")
    for advice in advice_list:
        print(f"\n  {advice.icon} {advice.title}")
        print(f"     {advice.description[:80]}...")
    
    return len(advice_list) > 0


def test_full_advice_generation():
    """Test complete advice generation."""
    print("\n" + "=" * 60)
    print("TEST: Full Advice Generation")
    print("=" * 60)
    
    advisor = RaceEngineerAdvisor()
    
    # Create test scenario: RX-7 on Akina
    car = Car(
        car_id="ks_mazda_rx7_tuned",
        name="Mazda RX-7 FC Tuned",
        power_hp=350,
        weight_kg=1150,
        drivetrain="RWD"
    )
    
    track = Track(
        track_id="akina_downhill",
        name="Akina Downhill"
    )
    
    # Create drift-oriented setup
    setup = Setup()
    setup.set_value("DIFFERENTIAL", "POWER", 75)
    setup.set_value("DIFFERENTIAL", "COAST", 55)
    setup.set_value("BRAKES", "FRONT_BIAS", 52)
    setup.set_value("ARB", "FRONT", 4)
    setup.set_value("ARB", "REAR", 7)
    
    print(f"\nScenario: {car.name} @ {track.name}")
    print("-" * 40)
    
    advice_list = advisor.generate_advice(car, track, setup)
    
    print(f"\nGenerated {len(advice_list)} total advice items:\n")
    
    for advice in advice_list[:8]:
        print(f"{advice.icon} [{advice.type.value.upper()}] {advice.title}")
        print(f"   {advice.description}")
        print()
    
    return len(advice_list) >= 5


def run_all_tests():
    """Run all advisor tests."""
    print("=" * 60)
    print("RACE ENGINEER ADVISOR TESTS")
    print("=" * 60)
    
    results = []
    
    results.append(("Car Analysis", test_car_analysis()))
    results.append(("Track Knowledge", test_track_knowledge()))
    results.append(("Setup Advice", test_setup_advice()))
    results.append(("Full Advice Generation", test_full_advice_generation()))
    
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
        print("\n✅ ALL ADVISOR TESTS PASSED")
    
    return all_passed


if __name__ == "__main__":
    run_all_tests()
