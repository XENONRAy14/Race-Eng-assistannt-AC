"""
Track Map Widget - Real-time track visualization with sector times.
Initial D / Retro Neon Racing aesthetic.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPainterPath, 
    QLinearGradient, QRadialGradient
)

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from pathlib import Path
import struct
import math


class SectorStatus(Enum):
    """Status of a sector time."""
    NONE = 0
    CURRENT = 1
    PERSONAL_BEST = 2
    SLOWER = 3


@dataclass
class TrackPoint:
    """A point on the track spline."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    length: float = 0.0


@dataclass 
class TrackData:
    """Track layout data."""
    points: list[TrackPoint] = field(default_factory=list)
    sector_splits: list[float] = field(default_factory=list)
    total_length: float = 0.0
    
    def get_point_at_position(self, normalized_pos: float) -> tuple[float, float]:
        """Get X, Z coordinates at a normalized position (0-1)."""
        if not self.points:
            return (0.0, 0.0)
        
        normalized_pos = max(0.0, min(1.0, normalized_pos))
        target_length = normalized_pos * self.total_length
        
        for i, point in enumerate(self.points):
            if point.length >= target_length:
                if i == 0:
                    return (point.x, point.z)
                
                prev = self.points[i - 1]
                segment_length = point.length - prev.length
                if segment_length > 0:
                    t = (target_length - prev.length) / segment_length
                    x = prev.x + t * (point.x - prev.x)
                    z = prev.z + t * (point.z - prev.z)
                    return (x, z)
                return (point.x, point.z)
        
        if self.points:
            return (self.points[-1].x, self.points[-1].z)
        return (0.0, 0.0)


def load_fast_lane(track_path: Path) -> Optional[TrackData]:
    """Load track spline from AC fast_lane.ai file."""
    # Try multiple possible locations
    possible_paths = [
        track_path / "ai" / "fast_lane.ai",
        track_path / "data" / "ai" / "fast_lane.ai",
        track_path / "ai" / "fast_lane.aip",
    ]
    
    fast_lane_path = None
    for path in possible_paths:
        if path.exists():
            fast_lane_path = path
            break
    
    if not fast_lane_path:
        return None
    
    try:
        with open(fast_lane_path, 'rb') as f:
            header = f.read(4)
            if len(header) < 4:
                return None
            
            num_points = struct.unpack('<i', header)[0]
            
            if num_points <= 0 or num_points > 100000:
                return None
            
            points = []
            total_length = 0.0
            prev_x, prev_z = None, None
            
            # Try different point sizes (AC format varies)
            for point_size in [72, 68, 64, 60]:  # 18, 17, 16, 15 floats
                f.seek(4)  # Reset to after header
                points = []
                total_length = 0.0
                prev_x, prev_z = None, None
                
                success = True
                for i in range(min(num_points, 10000)):  # Limit for safety
                    point_data = f.read(point_size)
                    if len(point_data) < 12:
                        success = False
                        break
                    
                    try:
                        x, y, z = struct.unpack('<fff', point_data[:12])
                        
                        # Sanity check
                        if abs(x) > 100000 or abs(y) > 100000 or abs(z) > 100000:
                            success = False
                            break
                        
                        if prev_x is not None:
                            dx = x - prev_x
                            dz = z - prev_z
                            total_length += (dx * dx + dz * dz) ** 0.5
                        
                        points.append(TrackPoint(x=x, y=y, z=z, length=total_length))
                        prev_x, prev_z = x, z
                    except:
                        success = False
                        break
                
                if success and len(points) >= 10:
                    track_data = TrackData(
                        points=points,
                        total_length=total_length,
                        sector_splits=[0.33, 0.66]
                    )
                    return track_data
            
            return None
            
    except Exception:
        return None


class TrackVisualization(QWidget):
    """
    Retro neon track visualization with GPS dot.
    Initial D inspired aesthetic.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(350)
        self.setMinimumWidth(350)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self._track_data: Optional[TrackData] = None
        self._sector_count = 3
        self._car_position = 0.0
        self._current_sector = 0
        
        # Neon colors - Initial D style
        self._sector_colors = [
            QColor("#00FFFF"),  # Cyan neon
            QColor("#FF00FF"),  # Magenta neon
            QColor("#FFFF00"),  # Yellow neon
            QColor("#00FF00"),  # Green neon
            QColor("#FF0080"),  # Pink neon
            QColor("#8000FF"),  # Purple neon
        ]
        
        self._bounds = None
        
        # Animation for glow effect
        self._glow_intensity = 0
        self._glow_timer = QTimer(self)
        self._glow_timer.timeout.connect(self._animate_glow)
        self._glow_timer.start(50)
    
    def _animate_glow(self):
        """Animate the glow effect."""
        self._glow_intensity = (self._glow_intensity + 5) % 100
        self.update()
    
    def set_track_data(self, track_data: TrackData) -> None:
        """Set the track layout data."""
        self._track_data = track_data
        self._calculate_bounds()
        self.update()
    
    def set_sector_count(self, count: int) -> None:
        """Set the number of sectors."""
        self._sector_count = max(1, min(count, 6))
        if self._track_data:
            self._track_data.sector_splits = [
                (i + 1) / self._sector_count 
                for i in range(self._sector_count - 1)
            ]
        self.update()
    
    def set_car_position(self, position: float) -> None:
        """Set car position (0.0 to 1.0)."""
        self._car_position = max(0.0, min(1.0, position))
        self._current_sector = int(self._car_position * self._sector_count)
        if self._current_sector >= self._sector_count:
            self._current_sector = self._sector_count - 1
        self.update()
    
    def _calculate_bounds(self) -> None:
        """Calculate track bounds for scaling."""
        if not self._track_data or not self._track_data.points:
            return
        
        min_x = min(p.x for p in self._track_data.points)
        max_x = max(p.x for p in self._track_data.points)
        min_z = min(p.z for p in self._track_data.points)
        max_z = max(p.z for p in self._track_data.points)
        
        self._bounds = (min_x, max_x, min_z, max_z)
    
    def _world_to_screen(self, x: float, z: float) -> QPointF:
        """Convert world coordinates to screen coordinates."""
        if not self._bounds:
            return QPointF(0, 0)
        
        min_x, max_x, min_z, max_z = self._bounds
        
        width = self.width() - 60
        height = self.height() - 60
        
        track_width = max_x - min_x
        track_height = max_z - min_z
        
        if track_width <= 0 or track_height <= 0:
            return QPointF(30, 30)
        
        scale_x = width / track_width
        scale_z = height / track_height
        scale = min(scale_x, scale_z) * 0.85
        
        center_x = (min_x + max_x) / 2
        center_z = (min_z + max_z) / 2
        
        screen_x = 30 + width / 2 + (x - center_x) * scale
        screen_z = 30 + height / 2 + (z - center_z) * scale
        
        return QPointF(screen_x, screen_z)
    
    def paintEvent(self, event):
        """Draw the track with neon aesthetic."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dark background with grid
        painter.fillRect(self.rect(), QColor("#0a0a0a"))
        self._draw_grid(painter)
        
        if not self._track_data or not self._track_data.points:
            self._draw_placeholder(painter)
            return
        
        # Draw track with neon glow
        self._draw_track_neon(painter)
        
        # Draw car GPS dot
        self._draw_car_neon(painter)
        
        # Draw start/finish
        self._draw_start_finish_neon(painter)
    
    def _draw_grid(self, painter: QPainter) -> None:
        """Draw retro grid background."""
        painter.setPen(QPen(QColor(0, 255, 255, 20), 1))
        
        grid_size = 30
        for x in range(0, self.width(), grid_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), grid_size):
            painter.drawLine(0, y, self.width(), y)
    
    def _draw_placeholder(self, painter: QPainter) -> None:
        """Draw placeholder with neon style."""
        # Neon text
        painter.setPen(QColor("#00FFFF"))
        font = QFont("Consolas", 14, QFont.Bold)
        painter.setFont(font)
        
        text = "TRACK DATA LOADING..."
        rect = self.rect()
        painter.drawText(rect, Qt.AlignCenter, text)
        
        # Animated scan line
        scan_y = (self._glow_intensity * self.height()) // 100
        gradient = QLinearGradient(0, scan_y - 20, 0, scan_y + 20)
        gradient.setColorAt(0, QColor(0, 255, 255, 0))
        gradient.setColorAt(0.5, QColor(0, 255, 255, 100))
        gradient.setColorAt(1, QColor(0, 255, 255, 0))
        painter.fillRect(0, scan_y - 2, self.width(), 4, gradient)
    
    def _draw_track_neon(self, painter: QPainter) -> None:
        """Draw track with neon glow effect."""
        if not self._track_data:
            return
        
        points = self._track_data.points
        total_length = self._track_data.total_length
        
        if total_length <= 0:
            return
        
        sector_starts = [0.0] + self._track_data.sector_splits + [1.0]
        
        for sector_idx in range(self._sector_count):
            start_pos = sector_starts[sector_idx]
            end_pos = sector_starts[sector_idx + 1] if sector_idx + 1 < len(sector_starts) else 1.0
            
            color = self._sector_colors[sector_idx % len(self._sector_colors)]
            
            # Glow layers for neon effect
            for glow_width in [12, 8, 4]:
                alpha = 80 if glow_width == 12 else (120 if glow_width == 8 else 255)
                glow_color = QColor(color)
                glow_color.setAlpha(alpha)
                
                pen = QPen(glow_color, glow_width)
                pen.setCapStyle(Qt.RoundCap)
                pen.setJoinStyle(Qt.RoundJoin)
                painter.setPen(pen)
                
                path = QPainterPath()
                first_point = True
                
                for point in points:
                    normalized_pos = point.length / total_length if total_length > 0 else 0
                    
                    if start_pos <= normalized_pos <= end_pos:
                        screen_pt = self._world_to_screen(point.x, point.z)
                        
                        if first_point:
                            path.moveTo(screen_pt)
                            first_point = False
                        else:
                            path.lineTo(screen_pt)
                
                painter.drawPath(path)
    
    def _draw_car_neon(self, painter: QPainter) -> None:
        """Draw car as neon GPS dot."""
        if not self._track_data:
            return
        
        x, z = self._track_data.get_point_at_position(self._car_position)
        screen_pt = self._world_to_screen(x, z)
        
        # Pulsing glow
        pulse = 0.8 + 0.2 * math.sin(self._glow_intensity * 0.1)
        
        # Outer glow
        gradient = QRadialGradient(screen_pt, 25 * pulse)
        gradient.setColorAt(0, QColor(255, 215, 0, 180))
        gradient.setColorAt(0.5, QColor(255, 215, 0, 80))
        gradient.setColorAt(1, QColor(255, 215, 0, 0))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(screen_pt, 25 * pulse, 25 * pulse)
        
        # Inner core
        painter.setBrush(QBrush(QColor("#FFD700")))
        painter.drawEllipse(screen_pt, 8, 8)
        
        # Center
        painter.setBrush(QBrush(QColor("#FFF")))
        painter.drawEllipse(screen_pt, 3, 3)
    
    def _draw_start_finish_neon(self, painter: QPainter) -> None:
        """Draw start/finish with neon style."""
        if not self._track_data or not self._track_data.points:
            return
        
        start_pt = self._track_data.points[0]
        screen_pt = self._world_to_screen(start_pt.x, start_pt.z)
        
        # Neon checkered flag
        painter.setPen(QPen(QColor("#00FFFF"), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(int(screen_pt.x()) - 10, int(screen_pt.y()) - 10, 20, 20)
        
        # S/F text with glow
        painter.setPen(QColor("#00FFFF"))
        font = QFont("Consolas", 10, QFont.Bold)
        painter.setFont(font)
        painter.drawText(int(screen_pt.x()) - 12, int(screen_pt.y()) + 28, "S/F")


class SectorTimeDisplay(QFrame):
    """Neon-styled sector time display."""
    
    def __init__(self, sector_index: int, parent=None):
        super().__init__(parent)
        self.sector_index = sector_index
        self.setFrameStyle(QFrame.NoFrame)
        
        # Neon border colors
        colors = ["#00FFFF", "#FF00FF", "#FFFF00", "#00FF00", "#FF0080", "#8000FF"]
        border_color = colors[sector_index % len(colors)]
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(10, 10, 10, 200);
                border: 2px solid {border_color};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        
        # Sector label with neon color
        self.sector_label = QLabel(f"SECTOR {sector_index + 1}")
        self.sector_label.setStyleSheet(f"""
            color: {border_color};
            font-family: 'Consolas', monospace;
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        self.sector_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.sector_label)
        
        # Time display
        self.time_label = QLabel("--:--.---")
        self.time_label.setStyleSheet("""
            color: #FFFFFF;
            font-family: 'Consolas', monospace;
            font-size: 22px;
            font-weight: bold;
        """)
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)
        
        # Delta
        self.delta_label = QLabel("")
        self.delta_label.setStyleSheet("""
            color: #888;
            font-family: 'Consolas', monospace;
            font-size: 13px;
        """)
        self.delta_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.delta_label)
    
    def set_time(self, time_ms: int, status: SectorStatus = SectorStatus.NONE) -> None:
        """Set the sector time."""
        if time_ms <= 0:
            self.time_label.setText("--:--.---")
            self.time_label.setStyleSheet("""
                color: #FFFFFF;
                font-family: 'Consolas', monospace;
                font-size: 22px;
                font-weight: bold;
            """)
            return
        
        total_seconds = time_ms / 1000
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        time_str = f"{minutes}:{seconds:06.3f}"
        
        self.time_label.setText(time_str)
        
        # Neon colors based on status
        if status == SectorStatus.PERSONAL_BEST:
            self.time_label.setStyleSheet("""
                color: #00FF00;
                font-family: 'Consolas', monospace;
                font-size: 22px;
                font-weight: bold;
                text-shadow: 0 0 10px #00FF00;
            """)
        elif status == SectorStatus.SLOWER:
            self.time_label.setStyleSheet("""
                color: #FF0080;
                font-family: 'Consolas', monospace;
                font-size: 22px;
                font-weight: bold;
                text-shadow: 0 0 10px #FF0080;
            """)
        else:
            self.time_label.setStyleSheet("""
                color: #FFFFFF;
                font-family: 'Consolas', monospace;
                font-size: 22px;
                font-weight: bold;
            """)
    
    def set_delta(self, delta_ms: int) -> None:
        """Set the delta to best time."""
        if delta_ms == 0:
            self.delta_label.setText("")
            return
        
        sign = "+" if delta_ms > 0 else ""
        delta_seconds = delta_ms / 1000
        
        if delta_ms > 0:
            self.delta_label.setStyleSheet("""
                color: #FF0080;
                font-family: 'Consolas', monospace;
                font-size: 13px;
            """)
        else:
            self.delta_label.setStyleSheet("""
                color: #00FF00;
                font-family: 'Consolas', monospace;
                font-size: 13px;
            """)
        
        self.delta_label.setText(f"{sign}{delta_seconds:.3f}s")


class TrackMapWidget(QWidget):
    """
    Main track map widget with Initial D / Retro Neon aesthetic.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._sector_count = 3
        self._current_sector = 0
        self._best_sector_times: list[int] = []
        self._current_sector_times: list[int] = []
        self._last_sector_times: list[int] = []
        self._track_path: Optional[Path] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the neon UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Title with neon glow
        title = QLabel("🗺️ TRACK MAP")
        title.setStyleSheet("""
            color: #00FFFF;
            font-family: 'Consolas', monospace;
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 3px;
            text-shadow: 0 0 20px #00FFFF;
        """)
        layout.addWidget(title)
        
        # Track info
        self.track_info_label = QLabel("TRACK: -- | LENGTH: -- | SECTORS: --")
        self.track_info_label.setStyleSheet("""
            color: #888;
            font-family: 'Consolas', monospace;
            font-size: 11px;
            letter-spacing: 1px;
        """)
        layout.addWidget(self.track_info_label)
        
        # Track visualization
        self.track_viz = TrackVisualization()
        layout.addWidget(self.track_viz, stretch=2)
        
        # Sector times
        sectors_group = QGroupBox("SECTOR TIMES")
        sectors_group.setStyleSheet("""
            QGroupBox {
                color: #FF00FF;
                font-family: 'Consolas', monospace;
                font-weight: bold;
                font-size: 13px;
                letter-spacing: 2px;
                border: 2px solid #FF00FF;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                background-color: #0a0a0a;
            }
        """)
        self.sectors_layout = QHBoxLayout(sectors_group)
        self.sectors_layout.setSpacing(12)
        
        self.sector_displays: list[SectorTimeDisplay] = []
        for i in range(3):
            display = SectorTimeDisplay(i)
            self.sector_displays.append(display)
            self.sectors_layout.addWidget(display)
        
        layout.addWidget(sectors_group)
        
        # Lap times
        lap_group = QGroupBox("LAP TIMES")
        lap_group.setStyleSheet("""
            QGroupBox {
                color: #FFFF00;
                font-family: 'Consolas', monospace;
                font-weight: bold;
                font-size: 13px;
                letter-spacing: 2px;
                border: 2px solid #FFFF00;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                background-color: #0a0a0a;
            }
        """)
        lap_layout = QGridLayout(lap_group)
        lap_layout.setSpacing(15)
        
        # Current lap
        current_label = QLabel("CURRENT:")
        current_label.setStyleSheet("color: #888; font-family: 'Consolas'; font-size: 11px;")
        lap_layout.addWidget(current_label, 0, 0)
        
        self.current_lap_label = QLabel("--:--.---")
        self.current_lap_label.setStyleSheet("""
            color: #00FFFF;
            font-family: 'Consolas', monospace;
            font-size: 26px;
            font-weight: bold;
            text-shadow: 0 0 15px #00FFFF;
        """)
        lap_layout.addWidget(self.current_lap_label, 0, 1)
        
        # Last lap
        last_label = QLabel("LAST:")
        last_label.setStyleSheet("color: #888; font-family: 'Consolas'; font-size: 11px;")
        lap_layout.addWidget(last_label, 1, 0)
        
        self.last_lap_label = QLabel("--:--.---")
        self.last_lap_label.setStyleSheet("""
            color: #FFF;
            font-family: 'Consolas', monospace;
            font-size: 20px;
            font-weight: bold;
        """)
        lap_layout.addWidget(self.last_lap_label, 1, 1)
        
        # Best lap
        best_label = QLabel("BEST:")
        best_label.setStyleSheet("color: #888; font-family: 'Consolas'; font-size: 11px;")
        lap_layout.addWidget(best_label, 2, 0)
        
        self.best_lap_label = QLabel("--:--.---")
        self.best_lap_label.setStyleSheet("""
            color: #00FF00;
            font-family: 'Consolas', monospace;
            font-size: 20px;
            font-weight: bold;
            text-shadow: 0 0 10px #00FF00;
        """)
        lap_layout.addWidget(self.best_lap_label, 2, 1)
        
        # Delta
        delta_label = QLabel("DELTA:")
        delta_label.setStyleSheet("color: #888; font-family: 'Consolas'; font-size: 11px;")
        lap_layout.addWidget(delta_label, 0, 2)
        
        self.delta_label = QLabel("--")
        self.delta_label.setStyleSheet("""
            color: #888;
            font-family: 'Consolas', monospace;
            font-size: 26px;
            font-weight: bold;
        """)
        lap_layout.addWidget(self.delta_label, 0, 3)
        
        # Laps
        laps_label = QLabel("LAPS:")
        laps_label.setStyleSheet("color: #888; font-family: 'Consolas'; font-size: 11px;")
        lap_layout.addWidget(laps_label, 1, 2)
        
        self.laps_label = QLabel("0")
        self.laps_label.setStyleSheet("""
            color: #FFF;
            font-family: 'Consolas', monospace;
            font-size: 20px;
            font-weight: bold;
        """)
        lap_layout.addWidget(self.laps_label, 1, 3)
        
        layout.addWidget(lap_group)
    
    def set_track_path(self, track_path: Path) -> None:
        """Set the track path and load track data."""
        self._track_path = track_path
        track_data = load_fast_lane(track_path)
        if track_data:
            self.track_viz.set_track_data(track_data)
    
    def set_sector_count(self, count: int) -> None:
        """Set the number of sectors."""
        if count == self._sector_count:
            return
        
        self._sector_count = max(1, min(count, 6))
        self.track_viz.set_sector_count(self._sector_count)
        
        for display in self.sector_displays:
            self.sectors_layout.removeWidget(display)
            display.deleteLater()
        
        self.sector_displays = []
        for i in range(self._sector_count):
            display = SectorTimeDisplay(i)
            self.sector_displays.append(display)
            self.sectors_layout.addWidget(display)
        
        self._best_sector_times = [0] * self._sector_count
        self._current_sector_times = [0] * self._sector_count
        self._last_sector_times = [0] * self._sector_count
    
    def set_track_info(self, track_name: str, track_length: float) -> None:
        """Set track information."""
        length_km = track_length / 1000
        self.track_info_label.setText(
            f"TRACK: {track_name.upper()} | LENGTH: {length_km:.2f} KM | SECTORS: {self._sector_count}"
        )
    
    def update_car_position(self, position: float) -> None:
        """Update car position."""
        self.track_viz.set_car_position(position)
    
    def update_sector_time(self, sector: int, time_ms: int) -> None:
        """Update a sector time."""
        if sector < 0 or sector >= self._sector_count:
            return
        
        self._current_sector_times[sector] = time_ms
        
        status = SectorStatus.NONE
        if self._best_sector_times[sector] > 0:
            if time_ms < self._best_sector_times[sector]:
                status = SectorStatus.PERSONAL_BEST
                self._best_sector_times[sector] = time_ms
            elif time_ms > self._best_sector_times[sector]:
                status = SectorStatus.SLOWER
        else:
            self._best_sector_times[sector] = time_ms
            status = SectorStatus.PERSONAL_BEST
        
        if sector < len(self.sector_displays):
            self.sector_displays[sector].set_time(time_ms, status)
            
            if self._best_sector_times[sector] > 0:
                delta = time_ms - self._best_sector_times[sector]
                self.sector_displays[sector].set_delta(delta)
    
    def update_current_sector(self, sector: int) -> None:
        """Update current sector."""
        self._current_sector = sector
    
    def update_lap_times(self, current_time: str, last_time: str, best_time: str, completed_laps: int) -> None:
        """Update lap times."""
        self.current_lap_label.setText(current_time if current_time else "--:--.---")
        self.last_lap_label.setText(last_time if last_time else "--:--.---")
        self.best_lap_label.setText(best_time if best_time else "--:--.---")
        self.laps_label.setText(str(completed_laps))
    
    def update_delta(self, delta_ms: int) -> None:
        """Update delta."""
        if delta_ms == 0:
            self.delta_label.setText("--")
            self.delta_label.setStyleSheet("""
                color: #888;
                font-family: 'Consolas', monospace;
                font-size: 26px;
                font-weight: bold;
            """)
            return
        
        sign = "+" if delta_ms > 0 else ""
        delta_seconds = delta_ms / 1000
        
        if delta_ms > 0:
            self.delta_label.setStyleSheet("""
                color: #FF0080;
                font-family: 'Consolas', monospace;
                font-size: 26px;
                font-weight: bold;
                text-shadow: 0 0 15px #FF0080;
            """)
        else:
            self.delta_label.setStyleSheet("""
                color: #00FF00;
                font-family: 'Consolas', monospace;
                font-size: 26px;
                font-weight: bold;
                text-shadow: 0 0 15px #00FF00;
            """)
        
        self.delta_label.setText(f"{sign}{delta_seconds:.3f}")
    
    def reset(self) -> None:
        """Reset all data."""
        self._best_sector_times = [0] * self._sector_count
        self._current_sector_times = [0] * self._sector_count
        self._last_sector_times = [0] * self._sector_count
        
        for display in self.sector_displays:
            display.set_time(0)
            display.set_delta(0)
        
        self.current_lap_label.setText("--:--.---")
        self.last_lap_label.setText("--:--.---")
        self.best_lap_label.setText("--:--.---")
        self.laps_label.setText("0")
        self.delta_label.setText("--")
        
        self.track_viz.set_car_position(0.0)
