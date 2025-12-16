"""
AC Shared Memory - Read Assetto Corsa shared memory for live data.
Uses the official AC Shared Memory API (no injection, no cheat).
"""

import ctypes
import mmap
from dataclasses import dataclass
from typing import Optional
from enum import IntEnum


class ACStatus(IntEnum):
    """Assetto Corsa game status."""
    AC_OFF = 0
    AC_REPLAY = 1
    AC_LIVE = 2
    AC_PAUSE = 3


class ACSessionType(IntEnum):
    """Session type."""
    AC_UNKNOWN = -1
    AC_PRACTICE = 0
    AC_QUALIFY = 1
    AC_RACE = 2
    AC_HOTLAP = 3
    AC_TIME_ATTACK = 4
    AC_DRIFT = 5
    AC_DRAG = 6


# Shared Memory structure for AC Physics
class SPageFilePhysics(ctypes.Structure):
    """AC Physics shared memory structure."""
    _fields_ = [
        ("packetId", ctypes.c_int),
        ("gas", ctypes.c_float),
        ("brake", ctypes.c_float),
        ("fuel", ctypes.c_float),
        ("gear", ctypes.c_int),
        ("rpms", ctypes.c_int),
        ("steerAngle", ctypes.c_float),
        ("speedKmh", ctypes.c_float),
        ("velocity", ctypes.c_float * 3),
        ("accG", ctypes.c_float * 3),
        ("wheelSlip", ctypes.c_float * 4),
        ("wheelLoad", ctypes.c_float * 4),
        ("wheelsPressure", ctypes.c_float * 4),
        ("wheelAngularSpeed", ctypes.c_float * 4),
        ("tyreWear", ctypes.c_float * 4),
        ("tyreDirtyLevel", ctypes.c_float * 4),
        ("tyreCoreTemperature", ctypes.c_float * 4),
        ("camberRAD", ctypes.c_float * 4),
        ("suspensionTravel", ctypes.c_float * 4),
        ("drs", ctypes.c_float),
        ("tc", ctypes.c_float),
        ("heading", ctypes.c_float),
        ("pitch", ctypes.c_float),
        ("roll", ctypes.c_float),
        ("cgHeight", ctypes.c_float),
        ("carDamage", ctypes.c_float * 5),
        ("numberOfTyresOut", ctypes.c_int),
        ("pitLimiterOn", ctypes.c_int),
        ("abs", ctypes.c_float),
        ("kersCharge", ctypes.c_float),
        ("kersInput", ctypes.c_float),
        ("autoShifterOn", ctypes.c_int),
        ("rideHeight", ctypes.c_float * 2),
        ("turboBoost", ctypes.c_float),
        ("ballast", ctypes.c_float),
        ("airDensity", ctypes.c_float),
        ("airTemp", ctypes.c_float),
        ("roadTemp", ctypes.c_float),
        ("localAngularVel", ctypes.c_float * 3),
        ("finalFF", ctypes.c_float),
        ("performanceMeter", ctypes.c_float),
        ("engineBrake", ctypes.c_int),
        ("ersRecoveryLevel", ctypes.c_int),
        ("ersPowerLevel", ctypes.c_int),
        ("ersHeatCharging", ctypes.c_int),
        ("ersIsCharging", ctypes.c_int),
        ("kersCurrentKJ", ctypes.c_float),
        ("drsAvailable", ctypes.c_int),
        ("drsEnabled", ctypes.c_int),
        ("brakeTemp", ctypes.c_float * 4),
        ("clutch", ctypes.c_float),
        ("tyreTempI", ctypes.c_float * 4),
        ("tyreTempM", ctypes.c_float * 4),
        ("tyreTempO", ctypes.c_float * 4),
        ("isAIControlled", ctypes.c_int),
        ("tyreContactPoint", ctypes.c_float * 4 * 3),
        ("tyreContactNormal", ctypes.c_float * 4 * 3),
        ("tyreContactHeading", ctypes.c_float * 4 * 3),
        ("brakeBias", ctypes.c_float),
        ("localVelocity", ctypes.c_float * 3),
    ]


# Shared Memory structure for AC Graphics
class SPageFileGraphic(ctypes.Structure):
    """AC Graphics shared memory structure."""
    _fields_ = [
        ("packetId", ctypes.c_int),
        ("status", ctypes.c_int),
        ("session", ctypes.c_int),
        ("currentTime", ctypes.c_wchar * 15),
        ("lastTime", ctypes.c_wchar * 15),
        ("bestTime", ctypes.c_wchar * 15),
        ("split", ctypes.c_wchar * 15),
        ("completedLaps", ctypes.c_int),
        ("position", ctypes.c_int),
        ("iCurrentTime", ctypes.c_int),
        ("iLastTime", ctypes.c_int),
        ("iBestTime", ctypes.c_int),
        ("sessionTimeLeft", ctypes.c_float),
        ("distanceTraveled", ctypes.c_float),
        ("isInPit", ctypes.c_int),
        ("currentSectorIndex", ctypes.c_int),
        ("lastSectorTime", ctypes.c_int),
        ("numberOfLaps", ctypes.c_int),
        ("tyreCompound", ctypes.c_wchar * 33),
        ("replayTimeMultiplier", ctypes.c_float),
        ("normalizedCarPosition", ctypes.c_float),
        ("carCoordinates", ctypes.c_float * 3),
        ("penaltyTime", ctypes.c_float),
        ("flag", ctypes.c_int),
        ("idealLineOn", ctypes.c_int),
        ("isInPitLane", ctypes.c_int),
        ("surfaceGrip", ctypes.c_float),
        ("mandatoryPitDone", ctypes.c_int),
        ("windSpeed", ctypes.c_float),
        ("windDirection", ctypes.c_float),
    ]


# Shared Memory structure for AC Static info
class SPageFileStatic(ctypes.Structure):
    """AC Static shared memory structure - contains car/track info."""
    _fields_ = [
        ("smVersion", ctypes.c_wchar * 15),
        ("acVersion", ctypes.c_wchar * 15),
        ("numberOfSessions", ctypes.c_int),
        ("numCars", ctypes.c_int),
        ("carModel", ctypes.c_wchar * 33),
        ("track", ctypes.c_wchar * 33),
        ("playerName", ctypes.c_wchar * 33),
        ("playerSurname", ctypes.c_wchar * 33),
        ("playerNick", ctypes.c_wchar * 33),
        ("sectorCount", ctypes.c_int),
        ("maxTorque", ctypes.c_float),
        ("maxPower", ctypes.c_float),
        ("maxRpm", ctypes.c_int),
        ("maxFuel", ctypes.c_float),
        ("suspensionMaxTravel", ctypes.c_float * 4),
        ("tyreRadius", ctypes.c_float * 4),
        ("maxTurboBoost", ctypes.c_float),
        ("deprecated1", ctypes.c_float),
        ("deprecated2", ctypes.c_float),
        ("penaltiesEnabled", ctypes.c_int),
        ("aidFuelRate", ctypes.c_float),
        ("aidTireRate", ctypes.c_float),
        ("aidMechanicalDamage", ctypes.c_float),
        ("aidAllowTyreBlankets", ctypes.c_int),
        ("aidStability", ctypes.c_float),
        ("aidAutoClutch", ctypes.c_int),
        ("aidAutoBlip", ctypes.c_int),
        ("hasDRS", ctypes.c_int),
        ("hasERS", ctypes.c_int),
        ("hasKERS", ctypes.c_int),
        ("kersMaxJ", ctypes.c_float),
        ("engineBrakeSettingsCount", ctypes.c_int),
        ("ersPowerControllerCount", ctypes.c_int),
        ("trackSPlineLength", ctypes.c_float),
        ("trackConfiguration", ctypes.c_wchar * 33),
        ("ersMaxJ", ctypes.c_float),
        ("isTimedRace", ctypes.c_int),
        ("hasExtraLap", ctypes.c_int),
        ("carSkin", ctypes.c_wchar * 33),
        ("reversedGridPositions", ctypes.c_int),
        ("pitWindowStart", ctypes.c_int),
        ("pitWindowEnd", ctypes.c_int),
    ]


@dataclass
class ACLiveData:
    """Live data from Assetto Corsa."""
    
    # Connection status
    is_connected: bool = False
    
    # Game status
    status: ACStatus = ACStatus.AC_OFF
    session_type: ACSessionType = ACSessionType.AC_UNKNOWN
    
    # Car and track info
    car_model: str = ""
    track: str = ""
    track_config: str = ""
    
    # Live telemetry
    speed_kmh: float = 0.0
    rpm: int = 0
    max_rpm: int = 8000
    gear: int = 0
    gas: float = 0.0
    brake: float = 0.0
    steer_angle: float = 0.0
    
    # G-forces
    g_lateral: float = 0.0
    g_longitudinal: float = 0.0
    
    # Tyre data
    tyre_pressure: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    tyre_temp_core: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    tyre_wear: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    
    # Session info
    is_in_pit: bool = False
    is_in_pit_lane: bool = False
    completed_laps: int = 0
    current_lap_time: str = ""
    best_lap_time: str = ""
    last_lap_time: str = ""
    
    # Physics
    brake_bias: float = 0.0
    air_temp: float = 0.0
    road_temp: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "is_connected": self.is_connected,
            "status": self.status.name,
            "session_type": self.session_type.name,
            "car_model": self.car_model,
            "track": self.track,
            "track_config": self.track_config,
            "speed_kmh": self.speed_kmh,
            "rpm": self.rpm,
            "gear": self.gear,
            "is_in_pit": self.is_in_pit,
            "completed_laps": self.completed_laps
        }


class ACSharedMemory:
    """
    Reader for Assetto Corsa Shared Memory.
    Provides live game data without any injection or modification.
    Uses Python mmap for Windows 10/11 compatibility.
    """
    
    # Shared memory names
    PHYSICS_MAP = "Local\\acpmf_physics"
    GRAPHICS_MAP = "Local\\acpmf_graphics"
    STATIC_MAP = "Local\\acpmf_static"
    
    def __init__(self):
        """Initialize shared memory reader."""
        self._physics_mmap: Optional[mmap.mmap] = None
        self._graphics_mmap: Optional[mmap.mmap] = None
        self._static_mmap: Optional[mmap.mmap] = None
        
        self._is_connected = False
        self._last_car = ""
        self._last_track = ""

    def _open_mmap(self, name: str, size: int) -> Optional[mmap.mmap]:
        """Open an existing named shared memory using mmap."""
        try:
            # mmap with tagname opens existing shared memory on Windows
            # Using access=mmap.ACCESS_READ for read-only
            m = mmap.mmap(-1, size, tagname=name, access=mmap.ACCESS_READ)
            return m
        except (OSError, ValueError, PermissionError):
            return None
    
    def connect(self) -> bool:
        """
        Connect to AC shared memory.
        Returns True if successful.
        """
        try:
            # Try to open all three shared memory regions
            physics = self._open_mmap(self.PHYSICS_MAP, ctypes.sizeof(SPageFilePhysics))
            graphics = self._open_mmap(self.GRAPHICS_MAP, ctypes.sizeof(SPageFileGraphic))
            static = self._open_mmap(self.STATIC_MAP, ctypes.sizeof(SPageFileStatic))

            if not (physics and graphics and static):
                # Close any that were opened
                if physics:
                    physics.close()
                if graphics:
                    graphics.close()
                if static:
                    static.close()
                self._is_connected = False
                return False

            self._physics_mmap = physics
            self._graphics_mmap = graphics
            self._static_mmap = static
            
            self._is_connected = True
            return True
            
        except Exception:
            self.disconnect()
            self._is_connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from shared memory."""
        if self._physics_mmap:
            try:
                self._physics_mmap.close()
            except:
                pass
        if self._graphics_mmap:
            try:
                self._graphics_mmap.close()
            except:
                pass
        if self._static_mmap:
            try:
                self._static_mmap.close()
            except:
                pass

        self._physics_mmap = None
        self._graphics_mmap = None
        self._static_mmap = None
        
        self._is_connected = False
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to AC."""
        return self._is_connected
    
    def read_static(self) -> Optional[SPageFileStatic]:
        """Read static data (car, track info)."""
        if not self._static_mmap:
            return None
        
        try:
            self._static_mmap.seek(0)
            data = self._static_mmap.read(ctypes.sizeof(SPageFileStatic))
            return SPageFileStatic.from_buffer_copy(data)
        except Exception:
            return None
    
    def read_physics(self) -> Optional[SPageFilePhysics]:
        """Read physics data (telemetry)."""
        if not self._physics_mmap:
            return None
        
        try:
            self._physics_mmap.seek(0)
            data = self._physics_mmap.read(ctypes.sizeof(SPageFilePhysics))
            return SPageFilePhysics.from_buffer_copy(data)
        except Exception:
            return None
    
    def read_graphics(self) -> Optional[SPageFileGraphic]:
        """Read graphics data (session info)."""
        if not self._graphics_mmap:
            return None
        
        try:
            self._graphics_mmap.seek(0)
            data = self._graphics_mmap.read(ctypes.sizeof(SPageFileGraphic))
            return SPageFileGraphic.from_buffer_copy(data)
        except Exception:
            return None
    
    def get_live_data(self) -> ACLiveData:
        """
        Get all live data from AC.
        Returns ACLiveData with current game state.
        """
        data = ACLiveData()
        
        # Try to connect if not connected
        if not self._is_connected:
            self.connect()
        
        if not self._is_connected:
            return data
        
        data.is_connected = True
        
        # Read static info (car/track)
        static = self.read_static()
        if static:
            data.car_model = static.carModel.strip('\x00')
            data.track = static.track.strip('\x00')
            data.track_config = static.trackConfiguration.strip('\x00')
        
        # Read graphics info (session)
        graphics = self.read_graphics()
        if graphics:
            try:
                data.status = ACStatus(graphics.status)
            except ValueError:
                data.status = ACStatus.AC_OFF
            try:
                data.session_type = ACSessionType(graphics.session)
            except ValueError:
                data.session_type = ACSessionType.AC_UNKNOWN
            data.is_in_pit = bool(graphics.isInPit)
            data.is_in_pit_lane = bool(graphics.isInPitLane)
            data.completed_laps = graphics.completedLaps
            data.current_lap_time = graphics.currentTime.strip('\x00')
            data.best_lap_time = graphics.bestTime.strip('\x00')
            data.last_lap_time = graphics.lastTime.strip('\x00')
        
        # Read static info for max RPM
        static = self.read_static()
        if static:
            data.max_rpm = static.maxRpm if static.maxRpm > 0 else 8000
        
        # Read physics info (telemetry)
        physics = self.read_physics()
        if physics:
            data.speed_kmh = physics.speedKmh
            data.rpm = physics.rpms
            data.gear = physics.gear
            data.gas = physics.gas
            data.brake = physics.brake
            data.steer_angle = physics.steerAngle
            data.brake_bias = physics.brakeBias
            data.air_temp = physics.airTemp
            data.road_temp = physics.roadTemp
            
            # G-forces from acceleration
            data.g_lateral = physics.accG[0] if len(physics.accG) > 0 else 0.0
            data.g_longitudinal = physics.accG[2] if len(physics.accG) > 2 else 0.0
            
            data.tyre_pressure = tuple(physics.wheelsPressure)
            data.tyre_temp_core = tuple(physics.tyreCoreTemperature)
            data.tyre_wear = tuple(physics.tyreWear)
        
        return data
    
    def get_car_track(self) -> tuple[str, str, str]:
        """
        Get current car and track.
        Returns (car_model, track, track_config).
        """
        if not self._is_connected:
            self.connect()
        
        static = self.read_static()
        if static:
            car = static.carModel.strip('\x00')
            track = static.track.strip('\x00')
            config = static.trackConfiguration.strip('\x00')
            return car, track, config
        
        return "", "", ""
    
    def is_ac_running(self) -> bool:
        """Check if AC is running and in a session."""
        data = self.get_live_data()
        return data.is_connected and data.status in [ACStatus.AC_LIVE, ACStatus.AC_PAUSE]
    
    def is_in_menu(self) -> bool:
        """Check if player is in pit/menu (can change setup)."""
        data = self.get_live_data()
        return data.is_connected and (data.is_in_pit or data.is_in_pit_lane)
    
    def car_track_changed(self) -> bool:
        """Check if car or track changed since last check."""
        car, track, _ = self.get_car_track()
        
        changed = (car != self._last_car or track != self._last_track)
        
        if car:
            self._last_car = car
        if track:
            self._last_track = track
        
        return changed and bool(car) and bool(track)
