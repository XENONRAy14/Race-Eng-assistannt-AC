"""
Debug track selection issue.
"""

import sys
sys.path.insert(0, '.')

from assetto.ac_shared_memory import ACSharedMemory

def debug_track():
    """Debug track detection."""
    print("=" * 60)
    print("DEBUG: Track Selection Issue")
    print("=" * 60)
    
    sm = ACSharedMemory()
    
    if not sm.connect():
        print("❌ Cannot connect to AC")
        return
    
    live = sm.get_live_data()
    
    print(f"\nDetected from AC:")
    print(f"  car_model: '{live.car_model}'")
    print(f"  car_skin: '{live.car_skin}'")
    print(f"  track: '{live.track}'")
    print(f"  track_config: '{live.track_config}'")
    
    # The issue: track_config is "downhill_real" but the fallback track
    # might be added with empty config, causing mismatch
    
    print(f"\nProblem Analysis:")
    print(f"  Track ID: {live.track}")
    print(f"  Track Config: {live.track_config}")
    print(f"  Full ID would be: {live.track}_{live.track_config}" if live.track_config else f"  Full ID: {live.track}")
    
    sm.disconnect()


if __name__ == "__main__":
    debug_track()
