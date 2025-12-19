"""
Track Map Widget V2 - Professional sector times and lap times display.
Clean design with minimal borders and better visual hierarchy.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from typing import Optional
from enum import Enum


class SectorStatus(Enum):
    """Status of a sector time."""
    NONE = 0
    CURRENT = 1
    PERSONAL_BEST = 2
    SLOWER = 3


class SectorTimeDisplay(QFrame):
    """Display for a single sector time - professional minimal design."""
    
    def __init__(self, sector_index: int, parent=None):
        super().__init__(parent)
        self.sector_index = sector_index
        self.setFrameStyle(QFrame.NoFrame)
        
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.02);
                border: none;
                border-left: 3px solid #666666;
                border-radius: 0px;
                padding: 15px 20px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        
        # Sector label
        self.sector_label = QLabel(f"S{sector_index + 1}")
        self.sector_label.setStyleSheet("""
            color: #666666;
            font-family: 'Arial', sans-serif;
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        self.sector_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.sector_label)
        
        # Time display
        self.time_label = QLabel("--:--.---")
        self.time_label.setStyleSheet("""
            color: #ffffff;
            font-family: 'Consolas', monospace;
            font-size: 20px;
            font-weight: bold;
        """)
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)
        
        # Delta
        self.delta_label = QLabel("")
        self.delta_label.setStyleSheet("""
            color: #999999;
            font-family: 'Consolas', monospace;
            font-size: 12px;
        """)
        self.delta_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.delta_label)
    
    def set_time(self, time_ms: int, status: SectorStatus = SectorStatus.NONE, delta_ms: Optional[int] = None):
        """Set sector time and status."""
        if time_ms <= 0:
            self.time_label.setText("--:--.---")
            self.delta_label.setText("")
            self._set_status_style(SectorStatus.NONE)
            return
        
        # Format time
        minutes = time_ms // 60000
        seconds = (time_ms % 60000) / 1000.0
        time_str = f"{minutes}:{seconds:06.3f}"
        self.time_label.setText(time_str)
        
        # Format delta
        if delta_ms is not None:
            sign = "+" if delta_ms > 0 else ""
            delta_str = f"{sign}{delta_ms / 1000.0:.3f}"
            self.delta_label.setText(delta_str)
        else:
            self.delta_label.setText("")
        
        self._set_status_style(status)
    
    def _set_status_style(self, status: SectorStatus):
        """Update styling based on status."""
        if status == SectorStatus.PERSONAL_BEST:
            border_color = "#00ff00"
            label_color = "#00ff00"
            time_color = "#00ff00"
        elif status == SectorStatus.CURRENT:
            border_color = "#ff8800"
            label_color = "#ff8800"
            time_color = "#ffffff"
        elif status == SectorStatus.SLOWER:
            border_color = "#ff0000"
            label_color = "#666666"
            time_color = "#ffffff"
        else:
            border_color = "#666666"
            label_color = "#666666"
            time_color = "#ffffff"
        
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(255, 255, 255, 0.02);
                border: none;
                border-left: 3px solid {border_color};
                border-radius: 0px;
                padding: 15px 20px;
            }}
        """)
        
        self.sector_label.setStyleSheet(f"""
            color: {label_color};
            font-family: 'Arial', sans-serif;
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        
        self.time_label.setStyleSheet(f"""
            color: {time_color};
            font-family: 'Consolas', monospace;
            font-size: 20px;
            font-weight: bold;
        """)


class TrackMapWidget(QWidget):
    """Widget displaying track map and sector times - professional design."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
        self._sector_displays = []
        self._best_sector_times = [0, 0, 0]
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: #000000;
                border-bottom: 1px solid rgba(255, 0, 0, 0.15);
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(40, 15, 40, 15)
        
        title = QLabel("TRACK")
        title.setStyleSheet("""
            color: #ff0000;
            font-family: 'Arial', sans-serif;
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # Content area
        content = QWidget()
        content.setStyleSheet("background: #0a0a0a;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setSpacing(25)
        
        # Track name
        self.track_name_label = QLabel("No track loaded")
        self.track_name_label.setStyleSheet("""
            color: #999999;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        content_layout.addWidget(self.track_name_label)
        
        # Lap time section
        lap_section = QVBoxLayout()
        lap_section.setSpacing(10)
        
        lap_title = QLabel("LAP TIME")
        lap_title.setStyleSheet("""
            color: #666666;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        lap_section.addWidget(lap_title)
        
        # Current lap time
        self.current_lap_label = QLabel("--:--.---")
        self.current_lap_label.setStyleSheet("""
            color: #ffffff;
            font-family: 'Consolas', monospace;
            font-size: 32px;
            font-weight: bold;
        """)
        self.current_lap_label.setAlignment(Qt.AlignCenter)
        lap_section.addWidget(self.current_lap_label)
        
        # Best lap time
        best_lap_layout = QHBoxLayout()
        best_lap_layout.setSpacing(10)
        
        best_label = QLabel("Best:")
        best_label.setStyleSheet("color: #999999; font-size: 13px;")
        best_lap_layout.addWidget(best_label)
        
        self.best_lap_label = QLabel("--:--.---")
        self.best_lap_label.setStyleSheet("""
            color: #00ff00;
            font-family: 'Consolas', monospace;
            font-size: 16px;
            font-weight: bold;
        """)
        best_lap_layout.addWidget(self.best_lap_label)
        best_lap_layout.addStretch()
        
        # Delta
        delta_label = QLabel("Delta:")
        delta_label.setStyleSheet("color: #999999; font-size: 13px;")
        best_lap_layout.addWidget(delta_label)
        
        self.delta_lap_label = QLabel("--")
        self.delta_lap_label.setStyleSheet("""
            color: #ffffff;
            font-family: 'Consolas', monospace;
            font-size: 16px;
            font-weight: bold;
        """)
        best_lap_layout.addWidget(self.delta_lap_label)
        
        lap_section.addLayout(best_lap_layout)
        content_layout.addLayout(lap_section)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background: rgba(255, 0, 0, 0.15); max-height: 1px;")
        content_layout.addWidget(separator)
        
        # Sectors section
        sectors_title = QLabel("SECTORS")
        sectors_title.setStyleSheet("""
            color: #666666;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
            margin-top: 10px;
        """)
        content_layout.addWidget(sectors_title)
        
        # Sector displays
        sectors_layout = QHBoxLayout()
        sectors_layout.setSpacing(15)
        
        for i in range(3):
            sector_display = SectorTimeDisplay(i)
            self._sector_displays.append(sector_display)
            sectors_layout.addWidget(sector_display)
        
        content_layout.addLayout(sectors_layout)
        content_layout.addStretch()
        
        layout.addWidget(content)
    
    def set_track_name(self, name: str, config: str = None):
        """Set track name."""
        if config and config != "default":
            self.track_name_label.setText(f"🏁 {name} ({config})")
        else:
            self.track_name_label.setText(f"🏁 {name}")
        
        self.track_name_label.setStyleSheet("""
            color: #ffffff;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
    
    def update_current_lap_time(self, time_ms: int):
        """Update current lap time."""
        if time_ms <= 0:
            self.current_lap_label.setText("--:--.---")
            return
        
        minutes = time_ms // 60000
        seconds = (time_ms % 60000) / 1000.0
        self.current_lap_label.setText(f"{minutes}:{seconds:06.3f}")
    
    def update_best_lap_time(self, time_ms: int):
        """Update best lap time."""
        if time_ms <= 0:
            self.best_lap_label.setText("--:--.---")
            return
        
        minutes = time_ms // 60000
        seconds = (time_ms % 60000) / 1000.0
        self.best_lap_label.setText(f"{minutes}:{seconds:06.3f}")
    
    def update_delta(self, delta_ms: int):
        """Update delta time."""
        if delta_ms == 0:
            self.delta_lap_label.setText("--")
            self.delta_lap_label.setStyleSheet("""
                color: #ffffff;
                font-family: 'Consolas', monospace;
                font-size: 16px;
                font-weight: bold;
            """)
            return
        
        sign = "+" if delta_ms > 0 else ""
        self.delta_lap_label.setText(f"{sign}{delta_ms / 1000.0:.3f}")
        
        color = "#ff0000" if delta_ms > 0 else "#00ff00"
        self.delta_lap_label.setStyleSheet(f"""
            color: {color};
            font-family: 'Consolas', monospace;
            font-size: 16px;
            font-weight: bold;
        """)
    
    def update_sector_time(self, sector_index: int, time_ms: int, is_best: bool = False):
        """Update sector time."""
        if sector_index < 0 or sector_index >= len(self._sector_displays):
            return
        
        status = SectorStatus.NONE
        delta_ms = None
        
        if is_best:
            status = SectorStatus.PERSONAL_BEST
            self._best_sector_times[sector_index] = time_ms
        elif self._best_sector_times[sector_index] > 0:
            delta_ms = time_ms - self._best_sector_times[sector_index]
            status = SectorStatus.SLOWER if delta_ms > 0 else SectorStatus.PERSONAL_BEST
        
        self._sector_displays[sector_index].set_time(time_ms, status, delta_ms)
    
    def reset(self):
        """Reset all displays."""
        self.track_name_label.setText("No track loaded")
        self.track_name_label.setStyleSheet("""
            color: #999999;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        self.current_lap_label.setText("--:--.---")
        self.best_lap_label.setText("--:--.---")
        self.delta_lap_label.setText("--")
        
        self._best_sector_times = [0, 0, 0]
        for display in self._sector_displays:
            display.set_time(0)
