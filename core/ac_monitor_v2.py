"""
AC Monitor V2 - Enhanced Shared Memory Reader
Extracts thermal data (ambient_temp, road_temp) and dynamic physics from Assetto Corsa.

Structure based on AC's shared memory documentation:
- SPageFilePhysics: Real-time physics data (updated ~60Hz)
- SPageFileGraphics: Graphics/UI data
- SPageFileStatic: Static car/track data
"""

import mmap
import ctypes
from ctypes import c_int32, c_float, c_wchar
from typing import Optional, Dict
import struct


# ═══════════════════════════════════════════════════════════════════════════
# ASSETTO CORSA SHARED MEMORY STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

class SPageFilePhysics(ctypes.Structure):
    """
    Physics data structure from Assetto Corsa shared memory.
    
    Memory map name: "Local\\acpmf_physics"
    Update rate: ~60 Hz (every frame)
    Size: Variable (check AC documentation for exact size)
    
    Key fields for V2.1:
    - airTemp: Ambient air temperature (°C)
    - roadTemp: Road surface temperature (°C)
    - wheelLoad[4]: Vertical load on each wheel (N)
    - suspensionTravel[4]: Suspension compression (m)
    """
    _fields_ = [
        ("packetId", c_int32),              # Packet ID
        ("gas", c_float),                   # Gas pedal (0.0 to 1.0)
        ("brake", c_float),                 # Brake pedal (0.0 to 1.0)
        ("fuel", c_float),                  # Fuel remaining (liters)
        ("gear", c_int32),                  # Current gear (0=R, 1=N, 2+=gears)
        ("rpm", c_int32),                   # Engine RPM
        ("steerAngle", c_float),            # Steering angle (radians)
        ("speedKmh", c_float),              # Speed (km/h)
        ("velocity", c_float * 3),          # Velocity vector (x, y, z) m/s
        ("accG", c_float * 3),              # G-force (x, y, z)
        ("wheelSlip", c_float * 4),         # Wheel slip (0.0 to 1.0+)
        ("wheelLoad", c_float * 4),         # Wheel load (N) - IMPORTANT
        ("wheelsPressure", c_float * 4),    # Tire pressure (PSI) - IMPORTANT
        ("wheelAngularSpeed", c_float * 4), # Wheel rotation speed (rad/s)
        ("tyreWear", c_float * 4),          # Tire wear (0.0 to 1.0)
        ("tyreDirtyLevel", c_float * 4),    # Tire dirt level
        ("tyreCoreTemperature", c_float * 4), # Tire core temp (°C) - IMPORTANT
        ("camberRAD", c_float * 4),         # Camber angle (radians)
        ("suspensionTravel", c_float * 4),  # Suspension travel (m) - IMPORTANT
        ("drs", c_float),                   # DRS status
        ("tc", c_float),                    # TC level
        ("heading", c_float),               # Heading angle (radians)
        ("pitch", c_float),                 # Pitch angle (radians)
        ("roll", c_float),                  # Roll angle (radians)
        ("cgHeight", c_float),              # Center of gravity height (m)
        ("carDamage", c_float * 5),         # Damage levels
        ("numberOfTyresOut", c_int32),      # Tires off track
        ("pitLimiterOn", c_int32),          # Pit limiter status
        ("abs", c_float),                   # ABS level
        ("kersCharge", c_float),            # KERS charge
        ("kersInput", c_float),             # KERS input
        ("autoShifterOn", c_int32),         # Auto shifter status
        ("rideHeight", c_float * 2),        # Ride height front/rear (m)
        ("turboBoost", c_float),            # Turbo boost pressure (bar)
        ("ballast", c_float),               # Ballast (kg)
        ("airDensity", c_float),            # Air density (kg/m³)
        ("airTemp", c_float),               # Ambient air temperature (°C) - KEY
        ("roadTemp", c_float),              # Road surface temperature (°C) - KEY
        ("localAngularVel", c_float * 3),   # Angular velocity
        ("finalFF", c_float),               # Force feedback
        ("performanceMeter", c_float),      # Performance meter
        ("engineBrake", c_int32),           # Engine brake setting
        ("ersRecoveryLevel", c_int32),      # ERS recovery level
        ("ersPowerLevel", c_int32),         # ERS power level
        ("ersHeatCharging", c_int32),       # ERS heat charging
        ("ersIsCharging", c_int32),         # ERS charging status
        ("kersCurrentKJ", c_float),         # KERS current energy (kJ)
        ("drsAvailable", c_int32),          # DRS available
        ("drsEnabled", c_int32),            # DRS enabled
        ("brakeTemp", c_float * 4),         # Brake temperature (°C)
        ("clutch", c_float),                # Clutch (0.0 to 1.0)
        ("tyreTempI", c_float * 4),         # Tire temp inner (°C)
        ("tyreTempM", c_float * 4),         # Tire temp middle (°C)
        ("tyreTempO", c_float * 4),         # Tire temp outer (°C)
        ("isAIControlled", c_int32),        # AI controlled
        ("tyreContactPoint", c_float * 4 * 3), # Tire contact points
        ("tyreContactNormal", c_float * 4 * 3), # Tire contact normals
        ("tyreContactHeading", c_float * 4 * 3), # Tire contact headings
        ("brakeBias", c_float),             # Brake bias
        ("localVelocity", c_float * 3),     # Local velocity
    ]


class SPageFileGraphics(ctypes.Structure):
    """
    Graphics/UI data structure.
    Memory map name: "Local\\acpmf_graphics"
    """
    _fields_ = [
        ("packetId", c_int32),
        ("status", c_int32),                # AC_STATUS (0=off, 1=replay, 2=live, 3=pause)
        ("session", c_int32),               # AC_SESSION_TYPE
        ("currentTime", c_wchar * 15),      # Current time string
        ("lastTime", c_wchar * 15),         # Last lap time
        ("bestTime", c_wchar * 15),         # Best lap time
        ("split", c_wchar * 15),            # Split time
        ("completedLaps", c_int32),         # Completed laps
        ("position", c_int32),              # Current position
        ("iCurrentTime", c_int32),          # Current time (ms)
        ("iLastTime", c_int32),             # Last lap time (ms)
        ("iBestTime", c_int32),             # Best lap time (ms)
        ("sessionTimeLeft", c_float),       # Session time left (s)
        ("distanceTraveled", c_float),      # Distance traveled (m)
        ("isInPit", c_int32),               # In pit
        ("currentSectorIndex", c_int32),    # Current sector
        ("lastSectorTime", c_int32),        # Last sector time (ms)
        ("numberOfLaps", c_int32),          # Number of laps
        ("tyreCompound", c_wchar * 33),     # Tire compound name
        ("replayTimeMultiplier", c_float),  # Replay speed
        ("normalizedCarPosition", c_float), # Position on track (0.0 to 1.0)
        ("activeCars", c_int32),            # Number of active cars
        ("carCoordinates", c_float * 60 * 3), # Car coordinates
        ("carID", c_int32 * 60),            # Car IDs
        ("playerCarID", c_int32),           # Player car ID
        ("penaltyTime", c_float),           # Penalty time
        ("flag", c_int32),                  # Flag status
        ("penalty", c_int32),               # Penalty type
        ("idealLineOn", c_int32),           # Ideal line on
        ("isInPitLane", c_int32),           # In pit lane
        ("surfaceGrip", c_float),           # Surface grip (0.0 to 1.0)
        ("mandatoryPitDone", c_int32),      # Mandatory pit done
        ("windSpeed", c_float),             # Wind speed (m/s)
        ("windDirection", c_float),         # Wind direction (radians)
    ]


class SPageFileStatic(ctypes.Structure):
    """
    Static car/track data structure.
    Memory map name: "Local\\acpmf_static"
    """
    _fields_ = [
        ("_smVersion", c_wchar * 15),       # Shared memory version
        ("_acVersion", c_wchar * 15),       # AC version
        ("numberOfSessions", c_int32),      # Number of sessions
        ("numCars", c_int32),               # Number of cars
        ("carModel", c_wchar * 33),         # Car model name - KEY
        ("track", c_wchar * 33),            # Track name - KEY
        ("playerName", c_wchar * 33),       # Player name
        ("playerSurname", c_wchar * 33),    # Player surname
        ("playerNick", c_wchar * 33),       # Player nickname
        ("sectorCount", c_int32),           # Number of sectors
        ("maxTorque", c_float),             # Max torque (Nm) - KEY
        ("maxPower", c_float),              # Max power (W)
        ("maxRpm", c_int32),                # Max RPM
        ("maxFuel", c_float),               # Max fuel (liters)
        ("suspensionMaxTravel", c_float * 4), # Max suspension travel (m)
        ("tyreRadius", c_float * 4),        # Tire radius (m)
        ("maxTurboBoost", c_float),         # Max turbo boost
        ("deprecated_1", c_float),          # Deprecated
        ("deprecated_2", c_float),          # Deprecated
        ("penaltiesEnabled", c_int32),      # Penalties enabled
        ("aidFuelRate", c_float),           # Fuel rate aid
        ("aidTireRate", c_float),           # Tire rate aid
        ("aidMechanicalDamage", c_float),   # Mechanical damage aid
        ("aidAllowTyreBlankets", c_int32),  # Allow tire blankets
        ("aidStability", c_float),          # Stability aid
        ("aidAutoClutch", c_int32),         # Auto clutch
        ("aidAutoBlip", c_int32),           # Auto blip
        ("hasDRS", c_int32),                # Has DRS
        ("hasERS", c_int32),                # Has ERS
        ("hasKERS", c_int32),               # Has KERS
        ("kersMaxJ", c_float),              # KERS max energy (J)
        ("engineBrakeSettingsCount", c_int32), # Engine brake settings count
        ("ersPowerControllerCount", c_int32),  # ERS power controller count
        ("trackSPlineLength", c_float),     # Track spline length (m)
        ("trackConfiguration", c_wchar * 33), # Track configuration - KEY
        ("ersMaxJ", c_float),               # ERS max energy (J)
        ("isTimedRace", c_int32),           # Is timed race
        ("hasExtraLap", c_int32),           # Has extra lap
        ("carSkin", c_wchar * 33),          # Car skin
        ("reversedGridPositions", c_int32), # Reversed grid positions
        ("PitWindowStart", c_int32),        # Pit window start
        ("PitWindowEnd", c_int32),          # Pit window end
    ]


# ═══════════════════════════════════════════════════════════════════════════
# AC MONITOR V2 CLASS
# ═══════════════════════════════════════════════════════════════════════════

class ACMonitorV2:
    """
    Enhanced Assetto Corsa shared memory monitor.
    Reads thermal data and dynamic physics for V2.1 setup generation.
    """
    
    def __init__(self):
        self.physics_map = None
        self.graphics_map = None
        self.static_map = None
        
        self.physics_data = None
        self.graphics_data = None
        self.static_data = None
        
        self.is_connected = False
    
    def connect(self) -> bool:
        """
        Connect to Assetto Corsa shared memory.
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            # Open physics memory map
            self.physics_map = mmap.mmap(-1, ctypes.sizeof(SPageFilePhysics), "Local\\acpmf_physics")
            self.physics_data = SPageFilePhysics()
            
            # Open graphics memory map
            self.graphics_map = mmap.mmap(-1, ctypes.sizeof(SPageFileGraphics), "Local\\acpmf_graphics")
            self.graphics_data = SPageFileGraphics()
            
            # Open static memory map
            self.static_map = mmap.mmap(-1, ctypes.sizeof(SPageFileStatic), "Local\\acpmf_static")
            self.static_data = SPageFileStatic()
            
            self.is_connected = True
            print("[AC MONITOR V2] Connected to Assetto Corsa shared memory")
            return True
            
        except Exception as e:
            print(f"[AC MONITOR V2] Failed to connect: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from shared memory."""
        if self.physics_map:
            self.physics_map.close()
        if self.graphics_map:
            self.graphics_map.close()
        if self.static_map:
            self.static_map.close()
        
        self.is_connected = False
        print("[AC MONITOR V2] Disconnected from Assetto Corsa")
    
    def read_physics(self) -> Optional[SPageFilePhysics]:
        """
        Read physics data from shared memory.
        
        Returns:
            SPageFilePhysics object or None if not connected
        """
        if not self.is_connected or not self.physics_map:
            return None
        
        try:
            # Seek to start of memory map
            self.physics_map.seek(0)
            
            # Read data into structure
            ctypes.memmove(ctypes.addressof(self.physics_data), 
                          self.physics_map.read(ctypes.sizeof(SPageFilePhysics)), 
                          ctypes.sizeof(SPageFilePhysics))
            
            return self.physics_data
            
        except Exception as e:
            print(f"[AC MONITOR V2] Error reading physics: {e}")
            return None
    
    def read_static(self) -> Optional[SPageFileStatic]:
        """
        Read static data from shared memory.
        
        Returns:
            SPageFileStatic object or None if not connected
        """
        if not self.is_connected or not self.static_map:
            return None
        
        try:
            self.static_map.seek(0)
            ctypes.memmove(ctypes.addressof(self.static_data),
                          self.static_map.read(ctypes.sizeof(SPageFileStatic)),
                          ctypes.sizeof(SPageFileStatic))
            
            return self.static_data
            
        except Exception as e:
            print(f"[AC MONITOR V2] Error reading static: {e}")
            return None
    
    def get_thermal_data(self) -> Dict[str, float]:
        """
        Extract thermal data for setup generation.
        
        Returns:
            Dict with keys:
            - ambient_temp: Ambient air temperature (°C)
            - road_temp: Road surface temperature (°C)
            - tire_temp_avg: Average tire core temperature (°C)
        """
        physics = self.read_physics()
        
        if not physics:
            # Return default values if not connected
            return {
                "ambient_temp": 25.0,
                "road_temp": 30.0,
                "tire_temp_avg": 0.0
            }
        
        # Extract temperatures
        ambient_temp = physics.airTemp
        road_temp = physics.roadTemp
        
        # Calculate average tire core temperature
        tire_temps = [physics.tyreCoreTemperature[i] for i in range(4)]
        tire_temp_avg = sum(tire_temps) / 4.0 if any(tire_temps) else 0.0
        
        return {
            "ambient_temp": ambient_temp,
            "road_temp": road_temp,
            "tire_temp_avg": tire_temp_avg
        }
    
    def get_car_track_info(self) -> Dict[str, str]:
        """
        Extract car and track information.
        
        Returns:
            Dict with keys:
            - car_model: Car model name
            - track: Track name
            - track_config: Track configuration
            - max_torque: Max torque (Nm)
        """
        static = self.read_static()
        
        if not static:
            return {
                "car_model": "",
                "track": "",
                "track_config": "",
                "max_torque": 0.0
            }
        
        return {
            "car_model": static.carModel,
            "track": static.track,
            "track_config": static.trackConfiguration,
            "max_torque": static.maxTorque
        }
    
    def get_tire_pressures(self) -> Dict[str, float]:
        """
        Get current tire pressures (hot).
        
        Returns:
            Dict with keys: PRESSURE_LF, PRESSURE_RF, PRESSURE_LR, PRESSURE_RR
        """
        physics = self.read_physics()
        
        if not physics:
            return {
                "PRESSURE_LF": 0.0,
                "PRESSURE_RF": 0.0,
                "PRESSURE_LR": 0.0,
                "PRESSURE_RR": 0.0
            }
        
        return {
            "PRESSURE_LF": physics.wheelsPressure[0],  # Front left
            "PRESSURE_RF": physics.wheelsPressure[1],  # Front right
            "PRESSURE_LR": physics.wheelsPressure[2],  # Rear left
            "PRESSURE_RR": physics.wheelsPressure[3]   # Rear right
        }
    
    def get_suspension_travel(self) -> Dict[str, float]:
        """
        Get current suspension travel (compression).
        
        Returns:
            Dict with keys: TRAVEL_LF, TRAVEL_RF, TRAVEL_LR, TRAVEL_RR (meters)
        """
        physics = self.read_physics()
        
        if not physics:
            return {
                "TRAVEL_LF": 0.0,
                "TRAVEL_RF": 0.0,
                "TRAVEL_LR": 0.0,
                "TRAVEL_RR": 0.0
            }
        
        return {
            "TRAVEL_LF": physics.suspensionTravel[0],
            "TRAVEL_RF": physics.suspensionTravel[1],
            "TRAVEL_LR": physics.suspensionTravel[2],
            "TRAVEL_RR": physics.suspensionTravel[3]
        }
    
    def get_complete_data(self) -> Dict:
        """
        Get all data needed for V2.1 setup generation.
        
        Returns:
            Complete data dict with thermal, car, track, and dynamic info
        """
        thermal = self.get_thermal_data()
        car_track = self.get_car_track_info()
        pressures = self.get_tire_pressures()
        suspension = self.get_suspension_travel()
        
        return {
            # Thermal data (for tire pressure calculation)
            "ambient_temp": thermal["ambient_temp"],
            "road_temp": thermal["road_temp"],
            "tire_temp_avg": thermal["tire_temp_avg"],
            
            # Car/Track info
            "car_model": car_track["car_model"],
            "track": car_track["track"],
            "track_config": car_track["track_config"],
            "max_torque": car_track["max_torque"],
            
            # Dynamic data (for validation)
            "tire_pressures": pressures,
            "suspension_travel": suspension,
            
            # Connection status
            "is_connected": self.is_connected
        }


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def test_connection():
    """
    Test connection to AC shared memory.
    Prints thermal data if connected.
    """
    monitor = ACMonitorV2()
    
    if monitor.connect():
        print("\n" + "="*70)
        print("AC MONITOR V2 - CONNECTION TEST")
        print("="*70)
        
        # Get complete data
        data = monitor.get_complete_data()
        
        print(f"\nThermal Data:")
        print(f"  Ambient Temp: {data['ambient_temp']:.1f}°C")
        print(f"  Road Temp: {data['road_temp']:.1f}°C")
        print(f"  Avg Tire Temp: {data['tire_temp_avg']:.1f}°C")
        
        print(f"\nCar/Track:")
        print(f"  Car: {data['car_model']}")
        print(f"  Track: {data['track']}")
        print(f"  Config: {data['track_config']}")
        print(f"  Max Torque: {data['max_torque']:.0f} Nm")
        
        print(f"\nTire Pressures (Hot):")
        pressures = data['tire_pressures']
        print(f"  FL: {pressures['PRESSURE_LF']:.1f} PSI")
        print(f"  FR: {pressures['PRESSURE_RF']:.1f} PSI")
        print(f"  RL: {pressures['PRESSURE_LR']:.1f} PSI")
        print(f"  RR: {pressures['PRESSURE_RR']:.1f} PSI")
        
        print("\n" + "="*70)
        
        monitor.disconnect()
    else:
        print("[ERROR] Could not connect to AC. Is the game running?")


if __name__ == "__main__":
    # Run test if executed directly
    test_connection()
