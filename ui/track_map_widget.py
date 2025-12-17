"""
Track Map Widget - Sector times and lap times display.
Initial D black/red gradient aesthetic.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from typing import Optional
from enum import Enum
from pathlib import Path


class SectorStatus(Enum):
    """Status of a sector time."""
    NONE = 0
    CURRENT = 1
    PERSONAL_BEST = 2
    SLOWER = 3


class SectorTimeDisplay(QFrame):
    """Display for a single sector time - Initial D style."""
    
    def __init__(self, sector_index: int, parent=None):
        super().__init__(parent)
        self.sector_index = sector_index
        self.setFrameStyle(QFrame.NoFrame)
        
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a0000, stop:1 #000000);
                border: 2px solid #ff0000;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        
        # Sector label
        self.sector_label = QLabel(f"SECTEUR {sector_index + 1}")
        self.sector_label.setStyleSheet("""
            color: #ff0000;
            font-family: 'Arial', sans-serif;
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        self.sector_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.sector_label)
        
        # Time display
        self.time_label = QLabel("--:--.---")
        self.time_label.setStyleSheet("""
            color: #ffffff;
            font-family: 'Arial', sans-serif;
            font-size: 24px;
            font-weight: bold;
        """)
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)
        
        # Delta
        self.delta_label = QLabel("")
        self.delta_label.setStyleSheet("""
            color: #888;
            font-family: 'Arial', sans-serif;
            font-size: 13px;
        """)
        self.delta_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.delta_label)
    
    def set_time(self, time_ms: int, status: SectorStatus = SectorStatus.NONE) -> None:
        """Set the sector time."""
        if time_ms <= 0:
            self.time_label.setText("--:--.---")
            self.time_label.setStyleSheet("""
                color: #ffffff;
                font-family: 'Arial', sans-serif;
                font-size: 24px;
                font-weight: bold;
            """)
            return
        
        total_seconds = time_ms / 1000
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        time_str = f"{minutes}:{seconds:06.3f}"
        
        self.time_label.setText(time_str)
        
        # Color based on status
        if status == SectorStatus.PERSONAL_BEST:
            self.time_label.setStyleSheet("""
                color: #00ff00;
                font-family: 'Arial', sans-serif;
                font-size: 24px;
                font-weight: bold;
            """)
        elif status == SectorStatus.SLOWER:
            self.time_label.setStyleSheet("""
                color: #ff0000;
                font-family: 'Arial', sans-serif;
                font-size: 24px;
                font-weight: bold;
            """)
        else:
            self.time_label.setStyleSheet("""
                color: #ffffff;
                font-family: 'Arial', sans-serif;
                font-size: 24px;
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
                color: #ff0000;
                font-family: 'Arial', sans-serif;
                font-size: 13px;
            """)
        else:
            self.delta_label.setStyleSheet("""
                color: #00ff00;
                font-family: 'Arial', sans-serif;
                font-size: 13px;
            """)
        
        self.delta_label.setText(f"{sign}{delta_seconds:.3f}s")


class TrackMapWidget(QWidget):
    """
    Main widget for sector times and lap times.
    Initial D black/red gradient aesthetic.
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
        """Set up the UI with Initial D style."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🏁 CHRONOMÉTRAGE")
        title.setStyleSheet("""
            color: #ff0000;
            font-family: 'Arial', sans-serif;
            font-size: 26px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        layout.addWidget(title)
        
        # Track info
        self.track_info_label = QLabel("Piste: -- | Longueur: -- | Secteurs: --")
        self.track_info_label.setStyleSheet("""
            color: #888;
            font-family: 'Arial', sans-serif;
            font-size: 12px;
        """)
        layout.addWidget(self.track_info_label)
        
        # Sector times group
        sectors_group = QGroupBox("Temps par Secteur")
        sectors_group.setStyleSheet("""
            QGroupBox {
                color: #ff0000;
                font-family: 'Arial', sans-serif;
                font-weight: bold;
                font-size: 14px;
                letter-spacing: 1px;
                border: 2px solid #ff0000;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 20px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a0000, stop:1 #000000);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                background-color: #000000;
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
        
        # Lap times group
        lap_group = QGroupBox("Temps au Tour")
        lap_group.setStyleSheet("""
            QGroupBox {
                color: #ff0000;
                font-family: 'Arial', sans-serif;
                font-weight: bold;
                font-size: 14px;
                letter-spacing: 1px;
                border: 2px solid #ff0000;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 20px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a0000, stop:1 #000000);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                background-color: #000000;
            }
        """)
        lap_layout = QGridLayout(lap_group)
        lap_layout.setSpacing(15)
        lap_layout.setContentsMargins(20, 25, 20, 20)
        
        # Current lap
        current_label = QLabel("Tour actuel:")
        current_label.setStyleSheet("color: #888; font-family: 'Arial'; font-size: 12px;")
        lap_layout.addWidget(current_label, 0, 0)
        
        self.current_lap_label = QLabel("--:--.---")
        self.current_lap_label.setStyleSheet("""
            color: #ffffff;
            font-family: 'Arial', sans-serif;
            font-size: 28px;
            font-weight: bold;
        """)
        lap_layout.addWidget(self.current_lap_label, 0, 1)
        
        # Last lap
        last_label = QLabel("Dernier tour:")
        last_label.setStyleSheet("color: #888; font-family: 'Arial'; font-size: 12px;")
        lap_layout.addWidget(last_label, 1, 0)
        
        self.last_lap_label = QLabel("--:--.---")
        self.last_lap_label.setStyleSheet("""
            color: #ffffff;
            font-family: 'Arial', sans-serif;
            font-size: 22px;
            font-weight: bold;
        """)
        lap_layout.addWidget(self.last_lap_label, 1, 1)
        
        # Best lap
        best_label = QLabel("Meilleur tour:")
        best_label.setStyleSheet("color: #888; font-family: 'Arial'; font-size: 12px;")
        lap_layout.addWidget(best_label, 2, 0)
        
        self.best_lap_label = QLabel("--:--.---")
        self.best_lap_label.setStyleSheet("""
            color: #00ff00;
            font-family: 'Arial', sans-serif;
            font-size: 22px;
            font-weight: bold;
        """)
        lap_layout.addWidget(self.best_lap_label, 2, 1)
        
        # Delta
        delta_label = QLabel("Delta:")
        delta_label.setStyleSheet("color: #888; font-family: 'Arial'; font-size: 12px;")
        lap_layout.addWidget(delta_label, 0, 2)
        
        self.delta_label = QLabel("--")
        self.delta_label.setStyleSheet("""
            color: #888;
            font-family: 'Arial', sans-serif;
            font-size: 28px;
            font-weight: bold;
        """)
        lap_layout.addWidget(self.delta_label, 0, 3)
        
        # Laps
        laps_label = QLabel("Tours complétés:")
        laps_label.setStyleSheet("color: #888; font-family: 'Arial'; font-size: 12px;")
        lap_layout.addWidget(laps_label, 1, 2)
        
        self.laps_label = QLabel("0")
        self.laps_label.setStyleSheet("""
            color: #ffffff;
            font-family: 'Arial', sans-serif;
            font-size: 22px;
            font-weight: bold;
        """)
        lap_layout.addWidget(self.laps_label, 1, 3)
        
        layout.addWidget(lap_group)
        layout.addStretch()
    
    def set_track_path(self, track_path: Path) -> None:
        """Set the track path (not used anymore but kept for compatibility)."""
        self._track_path = track_path
    
    def set_sector_count(self, count: int) -> None:
        """Set the number of sectors."""
        if count == self._sector_count:
            return
        
        self._sector_count = max(1, min(count, 6))
        
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
            f"Piste: {track_name} | Longueur: {length_km:.2f} km | Secteurs: {self._sector_count}"
        )
    
    def update_car_position(self, position: float) -> None:
        """Update car position (not used anymore but kept for compatibility)."""
        pass
    
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
                font-family: 'Arial', sans-serif;
                font-size: 28px;
                font-weight: bold;
            """)
            return
        
        sign = "+" if delta_ms > 0 else ""
        delta_seconds = delta_ms / 1000
        
        if delta_ms > 0:
            self.delta_label.setStyleSheet("""
                color: #ff0000;
                font-family: 'Arial', sans-serif;
                font-size: 28px;
                font-weight: bold;
            """)
        else:
            self.delta_label.setStyleSheet("""
                color: #00ff00;
                font-family: 'Arial', sans-serif;
                font-size: 28px;
                font-weight: bold;
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
