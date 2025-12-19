"""
Test script to debug AC shared memory detection.
Run this while AC is running to see what's happening.
"""

from assetto.ac_shared_memory import ACSharedMemory, ACStatus
import time

def test_detection():
    print("=== AC SHARED MEMORY DETECTION TEST ===\n")
    
    sm = ACSharedMemory()
    
    print("1. Attempting to connect to AC shared memory...")
    connected = sm.connect()
    print(f"   Connection result: {connected}")
    print(f"   is_connected property: {sm.is_connected}\n")
    
    if not connected:
        print("❌ Could not connect to AC shared memory")
        print("   Make sure Assetto Corsa is running and you're in a session!")
        return
    
    print("✅ Connected successfully!\n")
    
    print("2. Reading live data...")
    live_data = sm.get_live_data()
    
    print(f"   is_connected: {live_data.is_connected}")
    print(f"   status: {live_data.status} ({live_data.status.name})")
    print(f"   session_type: {live_data.session_type} ({live_data.session_type.name})")
    print(f"   car_model: '{live_data.car_model}'")
    print(f"   track: '{live_data.track}'")
    print(f"   track_config: '{live_data.track_config}'")
    print(f"   speed_kmh: {live_data.speed_kmh:.1f}")
    print(f"   rpm: {live_data.rpm}")
    print(f"   gear: {live_data.gear}")
    print(f"   is_in_pit: {live_data.is_in_pit}")
    print(f"   is_in_pit_lane: {live_data.is_in_pit_lane}\n")
    
    print("3. Status check:")
    if live_data.status == ACStatus.AC_OFF:
        print("   ⚠️ Status is AC_OFF - Game might be in menu")
    elif live_data.status == ACStatus.AC_LIVE:
        print("   ✅ Status is AC_LIVE - Game is running!")
    elif live_data.status == ACStatus.AC_PAUSE:
        print("   ⏸️ Status is AC_PAUSE - Game is paused")
    elif live_data.status == ACStatus.AC_REPLAY:
        print("   🎬 Status is AC_REPLAY - Watching replay")
    
    print("\n4. Continuous monitoring (10 seconds)...")
    for i in range(10):
        live_data = sm.get_live_data()
        status_icon = "🟢" if live_data.status in [ACStatus.AC_LIVE, ACStatus.AC_PAUSE] else "🔴"
        print(f"   [{i+1}/10] {status_icon} Status: {live_data.status.name:12} | Speed: {live_data.speed_kmh:6.1f} km/h | RPM: {live_data.rpm:5} | Gear: {live_data.gear}")
        time.sleep(1)
    
    print("\n✅ Test complete!")
    sm.disconnect()

if __name__ == "__main__":
    try:
        test_detection()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
