"""
Track Map Widget - Real-time track visualization with sector times.
Shows car position on track and sector-by-sector timing data.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class SectorStatus(Enum):
    """Status of a sector time."""
    NONE = 0
    CURRENT = 1
    PERSONAL_BEST = 2
    SESSION_BEST = 3
    SLOWER = 4


@dataclass
class SectorTime:
    """Sector timing data."""
    sector_index: int = 0
    time_ms: int = 0
    status: SectorStatus = SectorStatus.NONE
    
    @property
    def time_str(self) -> str:
        """Format time as string."""
        if self.time_ms <= 0:
            return "--:--.---"
        
        total_seconds = self.time_ms / 1000
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:06.3f}"


@dataclass
class LapData:
    """Data for a single lap."""
    lap_number: int = 0
    sector_times: list[SectorTime] = field(default_factory=list)
    total_time_ms: int = 0
    is_valid: bool = True
    
    @property
    def total_time_str(self) -> str:
        """Format total time as string."""
        if self.total_time_ms <= 0:
            return "--:--.---"
        
        total_seconds = self.total_time_ms / 1000
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:06.3f}"


class TrackVisualization(QWidget):
    """
    Visual representation of the track with sectors.
    Shows car position in real-time.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self._sector_count = 3
        self._car_position = 0.0  # 0.0 to 1.0
        self._current_sector = 0
        self._sector_colors = [
            QColor("#2196F3"),  # Blue
            QColor("#4CAF50"),  # Green
            QColor("#FF9800"),  # Orange
            QColor("#9C27B0"),  # Purple
            QColor("#F44336"),  # Red
            QColor("#00BCD4"),  # Cyan
        ]
        self._sector_statuses: list[SectorStatus] = []
    
    def set_sector_count(self, count: int) -> None:
        """Set the number of sectors."""
        self._sector_count = max(1, count)
        self._sector_statuses = [SectorStatus.NONE] * self._sector_count
        self.update()
    
    def set_car_position(self, position: float) -> None:
        """Set car position (0.0 to 1.0)."""
        self._car_position = max(0.0, min(1.0, position))
        self._current_sector = int(self._car_position * self._sector_count)
        if self._current_sector >= self._sector_count:
            self._current_sector = self._sector_count - 1
        self.update()
    
    def set_sector_status(self, sector: int, status: SectorStatus) -> None:
        """Set the status of a sector (for coloring)."""
        if 0 <= sector < len(self._sector_statuses):
            self._sector_statuses[sector] = status
            self.update()
    
    def paintEvent(self, event):
        """Draw the track visualization."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        margin = 20
        track_height = 40
        track_y = (height - track_height) // 2
        
        # Draw track background
        track_rect = QRectF(margin, track_y, width - 2 * margin, track_height)
        painter.setPen(QPen(QColor("#333"), 2))
        painter.setBrush(QBrush(QColor("#1a1a1a")))
        painter.drawRoundedRect(track_rect, 8, 8)
        
        # Draw sectors
        sector_width = (width - 2 * margin) / self._sector_count
        
        for i in range(self._sector_count):
            sector_x = margin + i * sector_width
            sector_rect = QRectF(sector_x + 2, track_y + 2, sector_width - 4, track_height - 4)
            
            # Get sector color based on status
            if i < len(self._sector_statuses):
                status = self._sector_statuses[i]
                if status == SectorStatus.PERSONAL_BEST:
                    color = QColor("#4CAF50")  # Green
                elif status == SectorStatus.SESSION_BEST:
                    color = QColor("#9C27B0")  # Purple
                elif status == SectorStatus.SLOWER:
                    color = QColor("#F44336")  # Red
                elif status == SectorStatus.CURRENT:
                    color = self._sector_colors[i % len(self._sector_colors)].lighter(130)
                else:
                    color = self._sector_colors[i % len(self._sector_colors)]
            else:
                color = self._sector_colors[i % len(self._sector_colors)]
            
            # Highlight current sector
            if i == self._current_sector:
                color = color.lighter(150)
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            
            # Round corners only on ends
            if i == 0:
                painter.drawRoundedRect(sector_rect, 6, 6)
            elif i == self._sector_count - 1:
                painter.drawRoundedRect(sector_rect, 6, 6)
            else:
                painter.drawRect(sector_rect)
            
            # Draw sector number
            painter.setPen(QColor("#fff"))
            font = QFont("Segoe UI", 10, QFont.Bold)
            painter.setFont(font)
            painter.drawText(sector_rect, Qt.AlignCenter, f"S{i + 1}")
        
        # Draw car position marker
        car_x = margin + self._car_position * (width - 2 * margin)
        car_y = track_y - 15
        
        # Car marker (triangle pointing down)
        painter.setBrush(QBrush(QColor("#FFD700")))  # Gold
        painter.setPen(QPen(QColor("#000"), 1))
        
        points = [
            QPointF(car_x, car_y + 12),
            QPointF(car_x - 8, car_y),
            QPointF(car_x + 8, car_y),
        ]
        painter.drawPolygon(points)
        
        # Draw start/finish line
        sf_x = margin
        painter.setPen(QPen(QColor("#fff"), 3))
        painter.drawLine(int(sf_x), track_y - 5, int(sf_x), track_y + track_height + 5)
        
        # Draw position percentage
        painter.setPen(QColor("#888"))
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        pos_text = f"{self._car_position * 100:.1f}%"
        painter.drawText(int(car_x - 20), track_y + track_height + 20, pos_text)


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
        
        # Sector label
        self.sector_label = QLabel(f"Secteur {sector_index + 1}")
        self.sector_label.setStyleSheet("color: #888; font-size: 11px;")
        self.sector_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.sector_label)
        
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
        elif status == SectorStatus.SESSION_BEST:
            self.time_label.setStyleSheet("color: #9C27B0; font-size: 18px; font-weight: bold;")
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
        self.track_info_label = QLabel("Piste: -- | Secteurs: --")
        self.track_info_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self.track_info_label)
        
        # Track visualization
        self.track_viz = TrackVisualization()
        layout.addWidget(self.track_viz)
        
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
        
        # Spacer
        layout.addStretch()
    
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
        
        # Update track visualization
        self.track_viz.set_sector_status(sector, status)
    
    def update_current_sector(self, sector: int) -> None:
        """Update which sector the car is currently in."""
        self._current_sector = sector
        self.track_viz.set_sector_status(sector, SectorStatus.CURRENT)
    
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
