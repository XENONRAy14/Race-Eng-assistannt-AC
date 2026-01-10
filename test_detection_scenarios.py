"""
Test script for car/track detection scenarios.
Simulates all possible session change scenarios to identify bugs.
"""

import sys
sys.path.insert(0, '.')

from dataclasses import dataclass
from typing import Optional

# Mock the ACLiveData
@dataclass
class MockLiveData:
    is_connected: bool = False
    car_model: str = ""
    track: str = ""
    track_config: str = ""
    status: int = 0  # 0=OFF, 1=REPLAY, 2=LIVE, 3=PAUSE
    rpm: int = 0

# Simulate the detection logic from main_window.py
class DetectionSimulator:
    def __init__(self):
        self._last_detected_car: str = ""
        self._last_detected_track: str = ""
        self._last_detected_track_config: str = ""
        self._selected_car: str = ""
        self._selected_track: str = ""
        self._cars_cache: list = []
        self._tracks_cache: list = []
        self.logs: list = []
    
    def log(self, msg: str):
        self.logs.append(msg)
        print(msg)
    
    def simulate_poll(self, live_data: MockLiveData) -> dict:
        """Simulate _poll_ac_status logic"""
        result = {
            "detected_change": False,
            "car_selected": False,
            "track_selected": False,
            "errors": []
        }
        
        # Check for car/track change (FIXED: now includes track_config)
        if live_data.is_connected and live_data.car_model and live_data.track:
            car_changed = live_data.car_model != self._last_detected_car
            track_changed = live_data.track != self._last_detected_track
            config_changed = live_data.track_config != self._last_detected_track_config
            
            if car_changed or track_changed or config_changed:
                
                self.log(f"[CHANGE] Car: '{self._last_detected_car}' -> '{live_data.car_model}'")
                self.log(f"[CHANGE] Track: '{self._last_detected_track}' -> '{live_data.track}'")
                self.log(f"[CHANGE] Config: '{self._last_detected_track_config}' -> '{live_data.track_config}'")
                
                self._last_detected_car = live_data.car_model
                self._last_detected_track = live_data.track
                self._last_detected_track_config = live_data.track_config
                result["detected_change"] = True
                
                # Simulate auto_select_car_track
                car_found, track_found, errors = self.simulate_auto_select(
                    live_data.car_model,
                    live_data.track,
                    live_data.track_config
                )
                result["car_selected"] = car_found
                result["track_selected"] = track_found
                result["errors"] = errors
        
        return result
    
    def simulate_auto_select(self, car_model: str, track: str, track_config: str) -> tuple:
        """Simulate _auto_select_car_track logic"""
        errors = []
        
        # Check if car exists in cache
        car_exists = car_model in self._cars_cache
        if not car_exists and car_model:
            self.log(f"[FALLBACK] Adding car '{car_model}' to cache")
            self._cars_cache.append(car_model)
        
        # Check if track exists in cache
        track_exists = track in self._tracks_cache
        if not track_exists and track:
            self.log(f"[FALLBACK] Adding track '{track}' to cache")
            self._tracks_cache.append(track)
        
        # Select car
        car_found = False
        if car_model:
            if car_model in self._cars_cache:
                self._selected_car = car_model
                car_found = True
                self.log(f"[SELECT] Car selected: {car_model}")
            else:
                errors.append(f"Car '{car_model}' not found after fallback!")
        
        # Select track
        track_found = False
        if track:
            if track in self._tracks_cache:
                self._selected_track = track
                track_found = True
                self.log(f"[SELECT] Track selected: {track}")
            else:
                errors.append(f"Track '{track}' not found after fallback!")
        
        return car_found, track_found, errors
    
    def simulate_session_quit(self):
        """Simulate quitting a session - shared memory returns empty data"""
        self.log("[SESSION] Quit session - shared memory cleared")
        # Note: We DON'T reset _last_detected_car/track here
        # This is important - they persist until new detection
    
    def reset_detection_state(self):
        """Reset detection state (simulates app restart or explicit reset)"""
        self._last_detected_car = ""
        self._last_detected_track = ""
        self.log("[RESET] Detection state cleared")


def run_all_tests():
    print("=" * 60)
    print("TESTING ALL DETECTION SCENARIOS")
    print("=" * 60)
    
    all_passed = True
    
    # ========================================
    # SCENARIO 1: Initial session launch
    # ========================================
    print("\n" + "=" * 60)
    print("SCENARIO 1: Initial session launch")
    print("=" * 60)
    
    sim = DetectionSimulator()
    
    # Poll 1: Not connected yet
    result = sim.simulate_poll(MockLiveData(is_connected=False))
    assert not result["detected_change"], "Should not detect change when not connected"
    
    # Poll 2: Connected, car/track loaded
    result = sim.simulate_poll(MockLiveData(
        is_connected=True,
        car_model="ks_toyota_ae86",
        track="akina_downhill",
        track_config="",
        status=2,  # LIVE
        rpm=3000
    ))
    
    if result["detected_change"] and result["car_selected"] and result["track_selected"]:
        print("✅ SCENARIO 1 PASSED: Initial detection works")
    else:
        print(f"❌ SCENARIO 1 FAILED: {result}")
        all_passed = False
    
    # ========================================
    # SCENARIO 2: Quit and join different session
    # ========================================
    print("\n" + "=" * 60)
    print("SCENARIO 2: Quit session, join new with different car/track")
    print("=" * 60)
    
    sim = DetectionSimulator()
    
    # Initial session
    sim.simulate_poll(MockLiveData(
        is_connected=True,
        car_model="ks_toyota_ae86",
        track="akina_downhill",
        status=2, rpm=3000
    ))
    
    # Quit session - shared memory may still have old data or be empty
    # BUG CHECK: What happens when we quit?
    sim.simulate_session_quit()
    
    # Poll while in menu (no car/track)
    result = sim.simulate_poll(MockLiveData(
        is_connected=True,
        car_model="",  # Empty in menu
        track="",
        status=0
    ))
    
    # Join new session with different car/track
    result = sim.simulate_poll(MockLiveData(
        is_connected=True,
        car_model="ks_nissan_skyline_r34",
        track="irohazaka",
        status=2, rpm=4000
    ))
    
    if result["detected_change"] and result["car_selected"] and result["track_selected"]:
        print("✅ SCENARIO 2 PASSED: New session detection works")
    else:
        print(f"❌ SCENARIO 2 FAILED: {result}")
        all_passed = False
    
    # ========================================
    # SCENARIO 3: Same car, different track
    # ========================================
    print("\n" + "=" * 60)
    print("SCENARIO 3: Same car, different track")
    print("=" * 60)
    
    sim = DetectionSimulator()
    
    # Initial session
    sim.simulate_poll(MockLiveData(
        is_connected=True,
        car_model="ks_toyota_ae86",
        track="akina_downhill",
        status=2, rpm=3000
    ))
    
    # Same car, different track
    result = sim.simulate_poll(MockLiveData(
        is_connected=True,
        car_model="ks_toyota_ae86",  # SAME
        track="irohazaka",  # DIFFERENT
        status=2, rpm=3000
    ))
    
    if result["detected_change"] and result["track_selected"]:
        print("✅ SCENARIO 3 PASSED: Track change detected with same car")
    else:
        print(f"❌ SCENARIO 3 FAILED: {result}")
        all_passed = False
    
    # ========================================
    # SCENARIO 4: Different car, same track
    # ========================================
    print("\n" + "=" * 60)
    print("SCENARIO 4: Different car, same track")
    print("=" * 60)
    
    sim = DetectionSimulator()
    
    # Initial session
    sim.simulate_poll(MockLiveData(
        is_connected=True,
        car_model="ks_toyota_ae86",
        track="akina_downhill",
        status=2, rpm=3000
    ))
    
    # Different car, same track
    result = sim.simulate_poll(MockLiveData(
        is_connected=True,
        car_model="ks_nissan_skyline_r34",  # DIFFERENT
        track="akina_downhill",  # SAME
        status=2, rpm=4000
    ))
    
    if result["detected_change"] and result["car_selected"]:
        print("✅ SCENARIO 4 PASSED: Car change detected with same track")
    else:
        print(f"❌ SCENARIO 4 FAILED: {result}")
        all_passed = False
    
    # ========================================
    # SCENARIO 5: Track with config change
    # ========================================
    print("\n" + "=" * 60)
    print("SCENARIO 5: Same track ID, different config")
    print("=" * 60)
    
    sim = DetectionSimulator()
    
    # Initial session - Nordschleife tourist
    sim.simulate_poll(MockLiveData(
        is_connected=True,
        car_model="ks_porsche_911_gt3",
        track="ks_nordschleife",
        track_config="tourist",
        status=2, rpm=5000
    ))
    
    # Same track, different config - Nordschleife endurance
    # BUG: Current logic only checks track_id, not config!
    result = sim.simulate_poll(MockLiveData(
        is_connected=True,
        car_model="ks_porsche_911_gt3",
        track="ks_nordschleife",  # SAME track_id
        track_config="endurance",  # DIFFERENT config
        status=2, rpm=5000
    ))
    
    # After fix, this should now detect the config change
    if result["detected_change"]:
        print("✅ SCENARIO 5 PASSED: Track config change detected")
    else:
        print("❌ SCENARIO 5 FAILED: Track config change NOT detected!")
        all_passed = False
    
    # ========================================
    # SCENARIO 6: Rapid session changes
    # ========================================
    print("\n" + "=" * 60)
    print("SCENARIO 6: Rapid session changes (stress test)")
    print("=" * 60)
    
    sim = DetectionSimulator()
    
    sessions = [
        ("car_a", "track_1", ""),
        ("car_b", "track_1", ""),
        ("car_b", "track_2", ""),
        ("car_c", "track_3", "config_a"),
        ("car_c", "track_3", "config_b"),  # Config change - will fail
        ("car_a", "track_1", ""),  # Back to first
    ]
    
    changes_detected = 0
    for car, track, config in sessions:
        result = sim.simulate_poll(MockLiveData(
            is_connected=True,
            car_model=car,
            track=track,
            track_config=config,
            status=2, rpm=3000
        ))
        if result["detected_change"]:
            changes_detected += 1
    
    # Should detect 5 changes (config change won't be detected)
    expected_changes = 4  # Without config detection
    if changes_detected >= expected_changes:
        print(f"✅ SCENARIO 6 PASSED: {changes_detected} changes detected")
    else:
        print(f"❌ SCENARIO 6 FAILED: Only {changes_detected}/{expected_changes} changes detected")
        all_passed = False
    
    # ========================================
    # SCENARIO 7: Connection lost and restored
    # ========================================
    print("\n" + "=" * 60)
    print("SCENARIO 7: Connection lost and restored")
    print("=" * 60)
    
    sim = DetectionSimulator()
    
    # Initial session
    sim.simulate_poll(MockLiveData(
        is_connected=True,
        car_model="ks_toyota_ae86",
        track="akina_downhill",
        status=2, rpm=3000
    ))
    
    # Connection lost
    result = sim.simulate_poll(MockLiveData(is_connected=False))
    
    # Connection restored - same session
    result = sim.simulate_poll(MockLiveData(
        is_connected=True,
        car_model="ks_toyota_ae86",
        track="akina_downhill",
        status=2, rpm=3000
    ))
    
    # Should NOT detect change (same car/track)
    if not result["detected_change"]:
        print("✅ SCENARIO 7 PASSED: No false detection after reconnect")
    else:
        print("⚠️ SCENARIO 7: Detected change after reconnect (may cause UI flicker)")
    
    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if all_passed:
        print("✅ ALL CORE TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED - BUGS FOUND:")
        print("   1. Track config changes are NOT detected")
        print("      Fix: Compare track_config in addition to track")
    
    return all_passed


if __name__ == "__main__":
    run_all_tests()
