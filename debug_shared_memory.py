"""
Debug script to check what's being read from AC shared memory.
"""

import sys
sys.path.insert(0, '.')

from assetto.ac_shared_memory import ACSharedMemory, SPageFileStatic
import ctypes

def debug_shared_memory():
    """Debug shared memory reading."""
    print("=" * 60)
    print("AC SHARED MEMORY DEBUG")
    print("=" * 60)
    
    sm = ACSharedMemory()
    
    if not sm.connect():
        print("❌ Cannot connect to AC shared memory")
        print("   Make sure Assetto Corsa is running!")
        return
    
    print("✅ Connected to AC shared memory")
    print()
    
    # Read static data
    static = sm.read_static()
    if static:
        print("Static Data:")
        print(f"  smVersion: '{static.smVersion}'")
        print(f"  acVersion: '{static.acVersion}'")
        print(f"  numberOfSessions: {static.numberOfSessions}")
        print(f"  numCars: {static.numCars}")
        print(f"  carModel (raw): '{static.carModel}'")
        print(f"  carModel (stripped): '{static.carModel.strip(chr(0))}'")
        print(f"  track (raw): '{static.track}'")
        print(f"  track (stripped): '{static.track.strip(chr(0))}'")
        print(f"  trackConfiguration: '{static.trackConfiguration}'")
        print(f"  playerName: '{static.playerName}'")
        print(f"  sectorCount: {static.sectorCount}")
        print(f"  maxRpm: {static.maxRpm}")
        print(f"  maxPower: {static.maxPower}")
        print(f"  carSkin: '{static.carSkin}'")
    else:
        print("❌ Could not read static data")
    
    print()
    
    # Read live data
    live = sm.get_live_data()
    if live:
        print("Live Data:")
        print(f"  car_model: '{live.car_model}'")
        print(f"  track: '{live.track}'")
        print(f"  track_config: '{live.track_config}'")
        print(f"  status: {live.status}")
        print(f"  speed_kmh: {live.speed_kmh:.1f}")
        print(f"  rpm: {live.rpm}")
        print(f"  gear: {live.gear}")
    else:
        print("❌ Could not read live data")
    
    print()
    
    # Check structure size
    print("Structure Info:")
    print(f"  SPageFileStatic size: {ctypes.sizeof(SPageFileStatic)} bytes")
    
    # Try to read raw bytes to see what's there
    if sm._static_view:
        print()
        print("Raw memory at carModel offset:")
        # carModel starts after smVersion(15*2) + acVersion(15*2) + numberOfSessions(4) + numCars(4)
        # = 30 + 30 + 4 + 4 = 68 bytes
        offset = 68
        try:
            raw_bytes = ctypes.string_at(sm._static_view + offset, 66)  # 33 wchars = 66 bytes
            print(f"  Bytes: {raw_bytes[:40]}...")
            # Decode as UTF-16
            try:
                decoded = raw_bytes.decode('utf-16-le').strip('\x00')
                print(f"  Decoded: '{decoded}'")
            except:
                print("  Could not decode as UTF-16")
        except Exception as e:
            print(f"  Error reading raw: {e}")
    
    sm.disconnect()
    print()
    print("Done!")


if __name__ == "__main__":
    debug_shared_memory()
