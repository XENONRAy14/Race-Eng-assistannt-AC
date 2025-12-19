"""
Telemetry Panel V2 - Professional HUD-style racing telemetry.
Redesigned for instant readability and professional sim racing aesthetic.

Design principles:
- Primary data (speed/RPM/gear) dominates the view
- Secondary data (temps/G-forces) in compact single row
- Minimal borders, maximum clarity
- True visual hierarchy
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from typing import Optional
from dataclasses import dataclass


@dataclass
class TelemetryData:
    """Live telemetry data from AC."""
    speed_kmh: float = 0.0
    rpm: int = 0
    max_rpm: int = 8000
    gear: int = 0
    
    tire_temp_fl: float = 0.0
    tire_temp_fr: float = 0.0
    tire_temp_rl: float = 0.0
    tire_temp_rr: float = 0.0
    
    g_lateral: float = 0.0
    g_longitudinal: float = 0.0
    
    throttle: float = 0.0
    brake: float = 0.0
    
    is_connected: bool = False


class PrimaryDataDisplay(QFrame):
    """
    Massive display for critical racing data: Speed, RPM, Gear.
    No borders, no clutter - just huge numbers you can read instantly.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.max_rpm = 8000
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        self.setStyleSheet("""
            QFrame {
                background: #000000;
                border: none;
                border-radius: 0px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(60)
        
        # Speed
        speed_container = QVBoxLayout()
        speed_container.setSpacing(0)
        
        self.speed_label = QLabel("0")
        self.speed_label.setAlignment(Qt.AlignCenter)
        self.speed_label.setStyleSheet("""
            color: #ffffff;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 96px;
            font-weight: bold;
            letter-spacing: -2px;
        """)
        speed_container.addWidget(self.speed_label)
        
        speed_unit = QLabel("km/h")
        speed_unit.setAlignment(Qt.AlignCenter)
        speed_unit.setStyleSheet("""
            color: #666666;
            font-family: 'Arial', sans-serif;
            font-size: 16px;
            font-weight: normal;
            letter-spacing: 2px;
        """)
        speed_container.addWidget(speed_unit)
        
        layout.addLayout(speed_container)
        
        # RPM
        rpm_container = QVBoxLayout()
        rpm_container.setSpacing(0)
        
        self.rpm_label = QLabel("0")
        self.rpm_label.setAlignment(Qt.AlignCenter)
        self.rpm_label.setStyleSheet("""
            color: #ffffff;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 96px;
            font-weight: bold;
            letter-spacing: -2px;
        """)
        rpm_container.addWidget(self.rpm_label)
        
        rpm_unit = QLabel("RPM")
        rpm_unit.setAlignment(Qt.AlignCenter)
        rpm_unit.setStyleSheet("""
            color: #666666;
            font-family: 'Arial', sans-serif;
            font-size: 16px;
            font-weight: normal;
            letter-spacing: 2px;
        """)
        rpm_container.addWidget(rpm_unit)
        
        layout.addLayout(rpm_container)
        
        # Gear
        gear_container = QVBoxLayout()
        gear_container.setSpacing(0)
        
        self.gear_label = QLabel("N")
        self.gear_label.setAlignment(Qt.AlignCenter)
        self.gear_label.setStyleSheet("""
            color: #ffffff;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 96px;
            font-weight: bold;
        """)
        gear_container.addWidget(self.gear_label)
        
        gear_unit = QLabel("GEAR")
        gear_unit.setAlignment(Qt.AlignCenter)
        gear_unit.setStyleSheet("""
            color: #666666;
            font-family: 'Arial', sans-serif;
            font-size: 16px;
            font-weight: normal;
            letter-spacing: 2px;
        """)
        gear_container.addWidget(gear_unit)
        
        layout.addLayout(gear_container)
    
    def update_data(self, speed: float, rpm: int, gear: int, max_rpm: int = 8000):
        """Update primary data."""
        self.max_rpm = max_rpm
        
        # Speed
        self.speed_label.setText(f"{int(speed)}")
        
        # RPM with color coding
        self.rpm_label.setText(f"{rpm}")
        rpm_percent = (rpm / max_rpm * 100) if max_rpm > 0 else 0
        
        if rpm_percent > 95:
            rpm_color = "#ff0000"  # Red zone
        elif rpm_percent > 85:
            rpm_color = "#ff8800"  # Warning
        else:
            rpm_color = "#ffffff"  # Normal
        
        self.rpm_label.setStyleSheet(f"""
            color: {rpm_color};
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 96px;
            font-weight: bold;
            letter-spacing: -2px;
        """)
        
        # Gear
        if gear == 0:
            gear_text = "N"
        elif gear == -1:
            gear_text = "R"
        else:
            gear_text = str(gear)
        
        self.gear_label.setText(gear_text)


class SecondaryDataRow(QFrame):
    """
    Compact single-row display for secondary data: tire temps and G-forces.
    All in one line for quick scanning.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.02);
                border: none;
                border-top: 1px solid rgba(255, 0, 0, 0.15);
                border-radius: 0px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(40)
        
        # Tire temperatures section
        tire_section = QHBoxLayout()
        tire_section.setSpacing(20)
        
        tire_label = QLabel("TIRES")
        tire_label.setStyleSheet("""
            color: #666666;
            font-family: 'Arial', sans-serif;
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        tire_section.addWidget(tire_label)
        
        # FL
        self.temp_fl = QLabel("--°")
        self.temp_fl.setStyleSheet("""
            color: #999999;
            font-family: 'Consolas', monospace;
            font-size: 18px;
            font-weight: bold;
        """)
        tire_section.addWidget(self.temp_fl)
        
        # FR
        self.temp_fr = QLabel("--°")
        self.temp_fr.setStyleSheet("""
            color: #999999;
            font-family: 'Consolas', monospace;
            font-size: 18px;
            font-weight: bold;
        """)
        tire_section.addWidget(self.temp_fr)
        
        tire_section.addSpacing(10)
        
        # RL
        self.temp_rl = QLabel("--°")
        self.temp_rl.setStyleSheet("""
            color: #999999;
            font-family: 'Consolas', monospace;
            font-size: 18px;
            font-weight: bold;
        """)
        tire_section.addWidget(self.temp_rl)
        
        # RR
        self.temp_rr = QLabel("--°")
        self.temp_rr.setStyleSheet("""
            color: #999999;
            font-family: 'Consolas', monospace;
            font-size: 18px;
            font-weight: bold;
        """)
        tire_section.addWidget(self.temp_rr)
        
        layout.addLayout(tire_section)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("background: rgba(255, 0, 0, 0.15);")
        separator.setFixedWidth(1)
        layout.addWidget(separator)
        
        # G-Forces section
        g_section = QHBoxLayout()
        g_section.setSpacing(20)
        
        g_label = QLabel("G-FORCE")
        g_label.setStyleSheet("""
            color: #666666;
            font-family: 'Arial', sans-serif;
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        g_section.addWidget(g_label)
        
        self.g_lat = QLabel("0.00")
        self.g_lat.setStyleSheet("""
            color: #999999;
            font-family: 'Consolas', monospace;
            font-size: 18px;
            font-weight: bold;
        """)
        g_section.addWidget(self.g_lat)
        
        g_lat_label = QLabel("LAT")
        g_lat_label.setStyleSheet("""
            color: #666666;
            font-family: 'Arial', sans-serif;
            font-size: 11px;
        """)
        g_section.addWidget(g_lat_label)
        
        g_section.addSpacing(10)
        
        self.g_lon = QLabel("0.00")
        self.g_lon.setStyleSheet("""
            color: #999999;
            font-family: 'Consolas', monospace;
            font-size: 18px;
            font-weight: bold;
        """)
        g_section.addWidget(self.g_lon)
        
        g_lon_label = QLabel("LON")
        g_lon_label.setStyleSheet("""
            color: #666666;
            font-family: 'Arial', sans-serif;
            font-size: 11px;
        """)
        g_section.addWidget(g_lon_label)
        
        layout.addLayout(g_section)
        layout.addStretch()
    
    def update_data(self, tire_temps: dict, g_lateral: float, g_longitudinal: float):
        """Update secondary data."""
        # Tire temperatures with color coding
        for tire_name, label in [
            ("fl", self.temp_fl),
            ("fr", self.temp_fr),
            ("rl", self.temp_rl),
            ("rr", self.temp_rr)
        ]:
            temp = tire_temps.get(tire_name, 0)
            if temp > 0:
                label.setText(f"{int(temp)}°")
                
                # Color based on temperature
                if temp < 60:
                    color = "#0088ff"  # Cold
                elif temp < 80:
                    color = "#00ff00"  # Optimal
                elif temp < 100:
                    color = "#ff8800"  # Hot
                else:
                    color = "#ff0000"  # Overheating
                
                label.setStyleSheet(f"""
                    color: {color};
                    font-family: 'Consolas', monospace;
                    font-size: 18px;
                    font-weight: bold;
                """)
            else:
                label.setText("--°")
        
        # G-forces
        self.g_lat.setText(f"{abs(g_lateral):.2f}")
        self.g_lon.setText(f"{abs(g_longitudinal):.2f}")


class InputsBar(QFrame):
    """
    Minimal horizontal bars for throttle and brake input.
    Full width, no boxes, just clean bars.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        self.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 15, 40, 15)
        layout.setSpacing(8)
        
        # Throttle
        throttle_layout = QHBoxLayout()
        throttle_layout.setSpacing(10)
        
        throttle_label = QLabel("GAS")
        throttle_label.setFixedWidth(50)
        throttle_label.setStyleSheet("""
            color: #666666;
            font-family: 'Arial', sans-serif;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        throttle_layout.addWidget(throttle_label)
        
        self.throttle_bar = QProgressBar()
        self.throttle_bar.setRange(0, 100)
        self.throttle_bar.setValue(0)
        self.throttle_bar.setTextVisible(False)
        self.throttle_bar.setFixedHeight(12)
        self.throttle_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff00, stop:1 #88ff00);
                border-radius: 2px;
            }
        """)
        throttle_layout.addWidget(self.throttle_bar)
        
        layout.addLayout(throttle_layout)
        
        # Brake
        brake_layout = QHBoxLayout()
        brake_layout.setSpacing(10)
        
        brake_label = QLabel("BRAKE")
        brake_label.setFixedWidth(50)
        brake_label.setStyleSheet("""
            color: #666666;
            font-family: 'Arial', sans-serif;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        brake_layout.addWidget(brake_label)
        
        self.brake_bar = QProgressBar()
        self.brake_bar.setRange(0, 100)
        self.brake_bar.setValue(0)
        self.brake_bar.setTextVisible(False)
        self.brake_bar.setFixedHeight(12)
        self.brake_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff0000, stop:1 #ff8800);
                border-radius: 2px;
            }
        """)
        brake_layout.addWidget(self.brake_bar)
        
        layout.addLayout(brake_layout)
    
    def update_data(self, throttle: float, brake: float):
        """Update input bars."""
        self.throttle_bar.setValue(int(throttle * 100))
        self.brake_bar.setValue(int(brake * 100))


class TelemetryPanel(QWidget):
    """
    Professional HUD-style telemetry panel.
    Redesigned for instant readability and racing credibility.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._request_update)
        self.update_timer.start(100)  # 10 Hz
        
        self.telemetry_callback = None
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with connection status
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: #000000;
                border-bottom: 1px solid rgba(255, 0, 0, 0.15);
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(40, 15, 40, 15)
        
        title = QLabel("TELEMETRY")
        title.setStyleSheet("""
            color: #ff0000;
            font-family: 'Arial', sans-serif;
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.status_label = QLabel("● CONNECTED")
        self.status_label.setStyleSheet("""
            color: #00ff00;
            font-family: 'Arial', sans-serif;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        header_layout.addWidget(self.status_label)
        
        layout.addWidget(header)
        
        # Primary data (huge)
        self.primary_display = PrimaryDataDisplay()
        layout.addWidget(self.primary_display)
        
        # Secondary data (compact row)
        self.secondary_row = SecondaryDataRow()
        layout.addWidget(self.secondary_row)
        
        # Inputs (minimal bars)
        self.inputs_bar = InputsBar()
        layout.addWidget(self.inputs_bar)
        
        layout.addStretch()
    
    def set_telemetry_callback(self, callback):
        """Set callback to get telemetry data."""
        self.telemetry_callback = callback
    
    def _request_update(self):
        """Request telemetry update."""
        if self.telemetry_callback:
            data = self.telemetry_callback()
            if data:
                self.update_telemetry(data)
    
    def update_telemetry(self, data: TelemetryData):
        """Update all telemetry displays."""
        # Update status
        if data.is_connected:
            self.status_label.setText("● CONNECTED")
            self.status_label.setStyleSheet("""
                color: #00ff00;
                font-family: 'Arial', sans-serif;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            """)
        else:
            self.status_label.setText("● DISCONNECTED")
            self.status_label.setStyleSheet("""
                color: #ff0000;
                font-family: 'Arial', sans-serif;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            """)
        
        # Update primary data
        self.primary_display.update_data(
            data.speed_kmh,
            data.rpm,
            data.gear,
            data.max_rpm
        )
        
        # Update secondary data
        tire_temps = {
            "fl": data.tire_temp_fl,
            "fr": data.tire_temp_fr,
            "rl": data.tire_temp_rl,
            "rr": data.tire_temp_rr
        }
        self.secondary_row.update_data(
            tire_temps,
            data.g_lateral,
            data.g_longitudinal
        )
        
        # Update inputs
        self.inputs_bar.update_data(data.throttle, data.brake)
