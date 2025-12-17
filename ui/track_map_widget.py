"""
Track Map Widget - Real-time track visualization with sector times.
Shows actual track layout loaded from AC files with GPS-like car position.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QGroupBox, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath, QPolygonF

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from pathlib import Path
import struct


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
    length: float = 0.0  # Distance from start


@dataclass 
class TrackData:
    """Track layout data."""
    points: list[TrackPoint] = field(default_factory=list)
    sector_splits: list[float] = field(default_factory=list)  # Normalized positions (0-1)
    total_length: float = 0.0
    
    def get_point_at_position(self, normalized_pos: float) -> tuple[float, float]:
        """Get X, Z coordinates at a normalized position (0-1)."""
        if not self.points:
            return (0.0, 0.0)
        
        normalized_pos = max(0.0, min(1.0, normalized_pos))
        target_length = normalized_pos * self.total_length
        
        # Find the two points surrounding this position
        for i, point in enumerate(self.points):
            if point.length >= target_length:
                if i == 0:
                    return (point.x, point.z)
                
                prev = self.points[i - 1]
                # Interpolate between prev and current
                segment_length = point.length - prev.length
                if segment_length > 0:
                    t = (target_length - prev.length) / segment_length
                    x = prev.x + t * (point.x - prev.x)
                    z = prev.z + t * (point.z - prev.z)
                    return (x, z)
                return (point.x, point.z)
        
        # Return last point
        if self.points:
            return (self.points[-1].x, self.points[-1].z)
        return (0.0, 0.0)


def load_fast_lane(track_path: Path) -> Optional[TrackData]:
    """
    Load track spline from AC fast_lane.ai file.
    File format: Binary with header + array of spline points.
    """
    fast_lane_path = track_path / "ai" / "fast_lane.ai"
    
    if not fast_lane_path.exists():
        # Try alternate locations
        for alt in ["data/ai/fast_lane.ai", "ai/fast_lane.aip"]:
            alt_path = track_path / alt
            if alt_path.exists():
                fast_lane_path = alt_path
                break
        else:
            return None
    
    try:
        with open(fast_lane_path, 'rb') as f:
            # Read header
            header = f.read(4)
            if len(header) < 4:
                return None
            
            # Number of points (little-endian int32)
            num_points = struct.unpack('<i', header)[0]
            
            if num_points <= 0 or num_points > 100000:
                return None
            
            points = []
            total_length = 0.0
            prev_x, prev_z = None, None
            
            # Each point: x, y, z (floats) + additional data
            # Format varies but typically 18 floats per point
            point_size = 18 * 4  # 18 floats * 4 bytes
            
            for i in range(num_points):
                point_data = f.read(point_size)
                if len(point_data) < 12:  # At least x, y, z
                    break
                
                # First 3 floats are x, y, z
                x, y, z = struct.unpack('<fff', point_data[:12])
                
                # Calculate cumulative length
                if prev_x is not None:
                    dx = x - prev_x
                    dz = z - prev_z
                    total_length += (dx * dx + dz * dz) ** 0.5
                
                points.append(TrackPoint(x=x, y=y, z=z, length=total_length))
                prev_x, prev_z = x, z
            
            if len(points) < 10:
                return None
            
            track_data = TrackData(
                points=points,
                total_length=total_length,
                sector_splits=[0.33, 0.66]  # Default 3 sectors
            )
            
            return track_data
            
    except Exception:
        return None


class TrackVisualization(QWidget):
    """
    Visual representation of the actual track layout.
    Shows track shape with colored sectors and GPS-like car position.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(300)
        self.setMinimumWidth(300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self._track_data: Optional[TrackData] = None
        self._sector_count = 3
        self._car_position = 0.0  # 0.0 to 1.0
        self._current_sector = 0
        
        # Sector colors
        self._sector_colors = [
            QColor("#2196F3"),  # Blue - Sector 1
            QColor("#4CAF50"),  # Green - Sector 2
            QColor("#FF9800"),  # Orange - Sector 3
            QColor("#9C27B0"),  # Purple - Sector 4
            QColor("#F44336"),  # Red - Sector 5
            QColor("#00BCD4"),  # Cyan - Sector 6
        ]
        
        # Cached drawing data
        self._bounds = None
        self._scale = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0
    
    def set_track_data(self, track_data: TrackData) -> None:
        """Set the track layout data."""
        self._track_data = track_data
        self._calculate_bounds()
        self.update()
    
    def set_sector_count(self, count: int) -> None:
        """Set the number of sectors."""
        self._sector_count = max(1, min(count, 6))
        if self._track_data:
            # Create even sector splits
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
        
        width = self.width() - 40
        height = self.height() - 40
        
        track_width = max_x - min_x
        track_height = max_z - min_z
        
        if track_width <= 0 or track_height <= 0:
            return QPointF(20, 20)
        
        # Scale to fit
        scale_x = width / track_width
        scale_z = height / track_height
        scale = min(scale_x, scale_z) * 0.9
        
        # Center the track
        center_x = (min_x + max_x) / 2
        center_z = (min_z + max_z) / 2
        
        screen_x = 20 + width / 2 + (x - center_x) * scale
        screen_z = 20 + height / 2 + (z - center_z) * scale
        
        return QPointF(screen_x, screen_z)
    
    def paintEvent(self, event):
        """Draw the track visualization."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor("#1a1a1a"))
        
        if not self._track_data or not self._track_data.points:
            # Draw placeholder
            self._draw_placeholder(painter)
            return
        
        # Draw track with colored sectors
        self._draw_track(painter)
        
        # Draw car position (GPS dot)
        self._draw_car_position(painter)
        
        # Draw start/finish line
        self._draw_start_finish(painter)
    
    def _draw_placeholder(self, painter: QPainter) -> None:
        """Draw placeholder when no track data."""
        painter.setPen(QColor("#666"))
        font = QFont("Segoe UI", 12)
        painter.setFont(font)
        painter.drawText(
            self.rect(), 
            Qt.AlignCenter, 
            "Tracé de piste non disponible\n(fichier ai/fast_lane.ai manquant)"
        )
    
    def _draw_track(self, painter: QPainter) -> None:
        """Draw the track with colored sectors."""
        if not self._track_data:
            return
        
        points = self._track_data.points
        total_length = self._track_data.total_length
        
        if total_length <= 0:
            return
        
        # Draw each sector with its color
        sector_starts = [0.0] + self._track_data.sector_splits + [1.0]
        
        for sector_idx in range(self._sector_count):
            start_pos = sector_starts[sector_idx]
            end_pos = sector_starts[sector_idx + 1] if sector_idx + 1 < len(sector_starts) else 1.0
            
            color = self._sector_colors[sector_idx % len(self._sector_colors)]
            
            # Highlight current sector
            if sector_idx == self._current_sector:
                color = color.lighter(140)
            
            pen = QPen(color, 4)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            
            # Draw this sector's portion of the track
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
    
    def _draw_car_position(self, painter: QPainter) -> None:
        """Draw the car as a GPS-like dot."""
        if not self._track_data:
            return
        
        x, z = self._track_data.get_point_at_position(self._car_position)
        screen_pt = self._world_to_screen(x, z)
        
        # Outer glow
        painter.setPen(Qt.NoPen)
        glow_color = QColor("#FFD700")
        glow_color.setAlpha(100)
        painter.setBrush(QBrush(glow_color))
        painter.drawEllipse(screen_pt, 15, 15)
        
        # Inner dot
        painter.setBrush(QBrush(QColor("#FFD700")))
        painter.drawEllipse(screen_pt, 8, 8)
        
        # Center
        painter.setBrush(QBrush(QColor("#FFF")))
        painter.drawEllipse(screen_pt, 3, 3)
    
    def _draw_start_finish(self, painter: QPainter) -> None:
        """Draw start/finish line indicator."""
        if not self._track_data or not self._track_data.points:
            return
        
        # Get start position
        start_pt = self._track_data.points[0]
        screen_pt = self._world_to_screen(start_pt.x, start_pt.z)
        
        # Draw checkered flag icon
        painter.setPen(QPen(QColor("#FFF"), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(int(screen_pt.x()) - 8, int(screen_pt.y()) - 8, 16, 16)
        
        # S/F text
        painter.setPen(QColor("#FFF"))
        font = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(font)
        painter.drawText(int(screen_pt.x()) - 10, int(screen_pt.y()) + 25, "S/F")


class SectorTimeDisplay(QFrame):
    """Display for a single sector time."""
    
    def __init__(self, sector_index: int, parent=None):
        super().__init__(parent)
        self.sector_index = sector_index
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        
        # Sector label with color indicator
        header = QHBoxLayout()
        
        # Color dot
        self.color_dot = QLabel("●")
        colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336", "#00BCD4"]
        self.color_dot.setStyleSheet(f"color: {colors[sector_index % len(colors)]}; font-size: 14px;")
        header.addWidget(self.color_dot)
        
        self.sector_label = QLabel(f"Secteur {sector_index + 1}")
        self.sector_label.setStyleSheet("color: #888; font-size: 11px;")
        header.addWidget(self.sector_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Current time
        self.time_label = QLabel("--:--.---")
        self.time_label.setStyleSheet("color: #fff; font-size: 18px; font-weight: bold;")
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)
        
        # Delta to best
        self.delta_label = QLabel("")
        self.delta_label.setStyleSheet("color: #888; font-size: 12px;")
        self.delta_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.delta_label)
    
    def set_time(self, time_ms: int, status: SectorStatus = SectorStatus.NONE) -> None:
        """Set the sector time."""
        if time_ms <= 0:
            self.time_label.setText("--:--.---")
            self.time_label.setStyleSheet("color: #fff; font-size: 18px; font-weight: bold;")
            return
        
        total_seconds = time_ms / 1000
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        time_str = f"{minutes}:{seconds:06.3f}"
        
        self.time_label.setText(time_str)
        
        # Color based on status
        if status == SectorStatus.PERSONAL_BEST:
            self.time_label.setStyleSheet("color: #4CAF50; font-size: 18px; font-weight: bold;")
        elif status == SectorStatus.SLOWER:
            self.time_label.setStyleSheet("color: #F44336; font-size: 18px; font-weight: bold;")
        else:
            self.time_label.setStyleSheet("color: #fff; font-size: 18px; font-weight: bold;")
    
    def set_delta(self, delta_ms: int) -> None:
        """Set the delta to best time."""
        if delta_ms == 0:
            self.delta_label.setText("")
            return
        
        sign = "+" if delta_ms > 0 else "-"
        delta_seconds = abs(delta_ms) / 1000
        
        if delta_ms > 0:
            self.delta_label.setStyleSheet("color: #F44336; font-size: 12px;")
        else:
            self.delta_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
        
        self.delta_label.setText(f"{sign}{delta_seconds:.3f}")


class TrackMapWidget(QWidget):
    """
    Main widget for track map and sector times.
    Shows real-time track position and sector timing data.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Data
        self._sector_count = 3
        self._current_sector = 0
        self._best_sector_times: list[int] = []
        self._current_sector_times: list[int] = []
        self._last_sector_times: list[int] = []
        self._track_path: Optional[Path] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🗺️ Carte de la Piste")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff;")
        layout.addWidget(title)
        
        # Track info
        self.track_info_label = QLabel("Piste: -- | Longueur: -- | Secteurs: --")
        self.track_info_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self.track_info_label)
        
        # Track visualization (the actual map)
        self.track_viz = TrackVisualization()
        layout.addWidget(self.track_viz, stretch=2)
        
        # Sector times group
        sectors_group = QGroupBox("Temps par Secteur")
        sectors_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        self.sectors_layout = QHBoxLayout(sectors_group)
        self.sectors_layout.setSpacing(10)
        
        # Create default sector displays
        self.sector_displays: list[SectorTimeDisplay] = []
        for i in range(3):
            display = SectorTimeDisplay(i)
            self.sector_displays.append(display)
            self.sectors_layout.addWidget(display)
        
        layout.addWidget(sectors_group)
        
        # Lap times group
        lap_group = QGroupBox("Temps au Tour")
        lap_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        lap_layout = QGridLayout(lap_group)
        lap_layout.setSpacing(15)
        
        # Current lap
        lap_layout.addWidget(QLabel("Tour actuel:"), 0, 0)
        self.current_lap_label = QLabel("--:--.---")
        self.current_lap_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2196F3;")
        lap_layout.addWidget(self.current_lap_label, 0, 1)
        
        # Last lap
        lap_layout.addWidget(QLabel("Dernier tour:"), 1, 0)
        self.last_lap_label = QLabel("--:--.---")
        self.last_lap_label.setStyleSheet("font-size: 18px; color: #fff;")
        lap_layout.addWidget(self.last_lap_label, 1, 1)
        
        # Best lap
        lap_layout.addWidget(QLabel("Meilleur tour:"), 2, 0)
        self.best_lap_label = QLabel("--:--.---")
        self.best_lap_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        lap_layout.addWidget(self.best_lap_label, 2, 1)
        
        # Delta
        lap_layout.addWidget(QLabel("Delta:"), 0, 2)
        self.delta_label = QLabel("--")
        self.delta_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #888;")
        lap_layout.addWidget(self.delta_label, 0, 3)
        
        # Completed laps
        lap_layout.addWidget(QLabel("Tours complétés:"), 1, 2)
        self.laps_label = QLabel("0")
        self.laps_label.setStyleSheet("font-size: 18px; color: #fff;")
        lap_layout.addWidget(self.laps_label, 1, 3)
        
        layout.addWidget(lap_group)
    
    def set_track_path(self, track_path: Path) -> None:
        """Set the track path and load track data."""
        self._track_path = track_path
        track_data = load_fast_lane(track_path)
        if track_data:
            self.track_viz.set_track_data(track_data)
    
    def set_sector_count(self, count: int) -> None:
        """Set the number of sectors and update UI."""
        if count == self._sector_count:
            return
        
        self._sector_count = max(1, min(count, 6))  # Max 6 sectors
        
        # Update track visualization
        self.track_viz.set_sector_count(self._sector_count)
        
        # Clear and recreate sector displays
        for display in self.sector_displays:
            self.sectors_layout.removeWidget(display)
            display.deleteLater()
        
        self.sector_displays = []
        for i in range(self._sector_count):
            display = SectorTimeDisplay(i)
            self.sector_displays.append(display)
            self.sectors_layout.addWidget(display)
        
        # Reset times
        self._best_sector_times = [0] * self._sector_count
        self._current_sector_times = [0] * self._sector_count
        self._last_sector_times = [0] * self._sector_count
    
    def set_track_info(self, track_name: str, track_length: float) -> None:
        """Set track information."""
        length_km = track_length / 1000
        self.track_info_label.setText(
            f"Piste: {track_name} | Longueur: {length_km:.2f} km | Secteurs: {self._sector_count}"
        )
    
    def update_car_position(self, position: float) -> None:
        """Update car position on track (0.0 to 1.0)."""
        self.track_viz.set_car_position(position)
    
    def update_sector_time(self, sector: int, time_ms: int) -> None:
        """Update a sector time."""
        if sector < 0 or sector >= self._sector_count:
            return
        
        self._current_sector_times[sector] = time_ms
        
        # Determine status
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
        
        # Update display
        if sector < len(self.sector_displays):
            self.sector_displays[sector].set_time(time_ms, status)
            
            # Calculate delta
            if self._best_sector_times[sector] > 0:
                delta = time_ms - self._best_sector_times[sector]
                self.sector_displays[sector].set_delta(delta)
    
    def update_current_sector(self, sector: int) -> None:
        """Update which sector the car is currently in."""
        self._current_sector = sector
    
    def update_lap_times(
        self,
        current_time: str,
        last_time: str,
        best_time: str,
        completed_laps: int
    ) -> None:
        """Update lap time displays."""
        self.current_lap_label.setText(current_time if current_time else "--:--.---")
        self.last_lap_label.setText(last_time if last_time else "--:--.---")
        self.best_lap_label.setText(best_time if best_time else "--:--.---")
        self.laps_label.setText(str(completed_laps))
    
    def update_delta(self, delta_ms: int) -> None:
        """Update the delta display."""
        if delta_ms == 0:
            self.delta_label.setText("--")
            self.delta_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #888;")
            return
        
        sign = "+" if delta_ms > 0 else "-"
        delta_seconds = abs(delta_ms) / 1000
        
        if delta_ms > 0:
            self.delta_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #F44336;")
        else:
            self.delta_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        
        self.delta_label.setText(f"{sign}{delta_seconds:.3f}")
    
    def reset(self) -> None:
        """Reset all data for a new session."""
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
