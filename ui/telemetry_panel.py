"""
Telemetry Panel - Live telemetry display from Assetto Corsa.
Shows speed, RPM, tire temps, G-forces in a clean, ergonomic layout.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QProgressBar, QGroupBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPalette, QColor
from typing import Optional
from dataclasses import dataclass


@dataclass
class TelemetryData:
    """Live telemetry data from AC."""
    speed_kmh: float = 0.0
    rpm: int = 0
    max_rpm: int = 8000
    gear: int = 0
    
    # Tire temps (°C)
    tire_temp_fl: float = 0.0
    tire_temp_fr: float = 0.0
    tire_temp_rl: float = 0.0
    tire_temp_rr: float = 0.0
    
    # G-forces
    g_lateral: float = 0.0
    g_longitudinal: float = 0.0
    
    # Brake/throttle
    throttle: float = 0.0
    brake: float = 0.0
    
    # Status
    is_connected: bool = False


class GaugeWidget(QFrame):
    """Simple circular-style gauge display."""
    
    def __init__(self, title: str, unit: str = "", max_value: float = 100, parent=None):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.max_value = max_value
        self.value = 0.0
        
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            GaugeWidget {
                background-color: #1a1a2e;
                border: 2px solid #16213e;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Title
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.title_label)
        
        # Value
        self.value_label = QLabel("0")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("color: #fff; font-size: 24px; font-weight: bold;")
        layout.addWidget(self.value_label)
        
        # Unit
        self.unit_label = QLabel(unit)
        self.unit_label.setAlignment(Qt.AlignCenter)
        self.unit_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.unit_label)
        
        self.setMinimumSize(80, 80)
    
    def set_value(self, value: float):
        """Update the gauge value."""
        self.value = value
        
        # Format based on value size
        if value >= 1000:
            self.value_label.setText(f"{int(value)}")
        elif value >= 100:
            self.value_label.setText(f"{int(value)}")
        elif value >= 10:
            self.value_label.setText(f"{value:.1f}")
        else:
            self.value_label.setText(f"{value:.2f}")
        
        # Color based on percentage of max
        pct = min(value / self.max_value, 1.0) if self.max_value > 0 else 0
        if pct > 0.9:
            color = "#ff4444"  # Red - danger
        elif pct > 0.7:
            color = "#ffaa00"  # Orange - warning
        else:
            color = "#44ff44"  # Green - good
        
        self.value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")


class TireTempsWidget(QFrame):
    """4-tire temperature display in car layout."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            TireTempsWidget {
                background-color: #1a1a2e;
                border: 2px solid #16213e;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("🏎️ Températures Pneus")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #aaa; font-size: 12px; font-weight: bold;")
        layout.addWidget(title)
        
        # Tire grid (car shape)
        tire_layout = QGridLayout()
        tire_layout.setSpacing(10)
        
        self.tire_fl = self._create_tire_label("AV-G")
        self.tire_fr = self._create_tire_label("AV-D")
        self.tire_rl = self._create_tire_label("AR-G")
        self.tire_rr = self._create_tire_label("AR-D")
        
        tire_layout.addWidget(self.tire_fl, 0, 0)
        tire_layout.addWidget(self.tire_fr, 0, 1)
        tire_layout.addWidget(self.tire_rl, 1, 0)
        tire_layout.addWidget(self.tire_rr, 1, 1)
        
        layout.addLayout(tire_layout)
        
        self.setMinimumSize(150, 120)
    
    def _create_tire_label(self, name: str) -> QLabel:
        """Create a tire temperature label."""
        label = QLabel(f"{name}\n--°C")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            background-color: #2a2a4e;
            border-radius: 5px;
            padding: 5px;
            color: #888;
            font-size: 11px;
        """)
        label.setMinimumSize(60, 45)
        return label
    
    def _get_temp_color(self, temp: float) -> str:
        """Get color based on tire temperature."""
        if temp < 60:
            return "#4444ff"  # Blue - cold
        elif temp < 80:
            return "#44ff44"  # Green - optimal
        elif temp < 100:
            return "#ffaa00"  # Orange - hot
        else:
            return "#ff4444"  # Red - overheating
    
    def set_temps(self, fl: float, fr: float, rl: float, rr: float):
        """Update tire temperatures."""
        for label, temp, name in [
            (self.tire_fl, fl, "AV-G"),
            (self.tire_fr, fr, "AV-D"),
            (self.tire_rl, rl, "AR-G"),
            (self.tire_rr, rr, "AR-D")
        ]:
            color = self._get_temp_color(temp)
            label.setText(f"{name}\n{temp:.0f}°C")
            label.setStyleSheet(f"""
                background-color: #2a2a4e;
                border-radius: 5px;
                padding: 5px;
                color: {color};
                font-size: 11px;
                font-weight: bold;
            """)


class GForceWidget(QFrame):
    """G-force indicator with visual dot."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.g_lat = 0.0
        self.g_lon = 0.0
        
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            GForceWidget {
                background-color: #1a1a2e;
                border: 2px solid #16213e;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("📊 G-Forces")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #aaa; font-size: 12px; font-weight: bold;")
        layout.addWidget(title)
        
        # G values
        values_layout = QHBoxLayout()
        
        self.lat_label = QLabel("Lat: 0.00g")
        self.lat_label.setStyleSheet("color: #44aaff; font-size: 11px;")
        values_layout.addWidget(self.lat_label)
        
        self.lon_label = QLabel("Lon: 0.00g")
        self.lon_label.setStyleSheet("color: #ff44aa; font-size: 11px;")
        values_layout.addWidget(self.lon_label)
        
        layout.addLayout(values_layout)
        
        # Max G indicator
        self.max_label = QLabel("Max: 0.00g")
        self.max_label.setAlignment(Qt.AlignCenter)
        self.max_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.max_label)
        
        self.max_g = 0.0
        self.setMinimumSize(150, 80)
    
    def set_g_forces(self, lateral: float, longitudinal: float):
        """Update G-force display."""
        self.g_lat = lateral
        self.g_lon = longitudinal
        
        self.lat_label.setText(f"Lat: {abs(lateral):.2f}g")
        self.lon_label.setText(f"Lon: {abs(longitudinal):.2f}g")
        
        # Track max G
        total_g = (lateral**2 + longitudinal**2)**0.5
        if total_g > self.max_g:
            self.max_g = total_g
            self.max_label.setText(f"Max: {self.max_g:.2f}g")


class PedalWidget(QFrame):
    """Throttle and brake pedal display."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            PedalWidget {
                background-color: #1a1a2e;
                border: 2px solid #16213e;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("🎮 Pédales")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #aaa; font-size: 12px; font-weight: bold;")
        layout.addWidget(title)
        
        # Throttle
        throttle_layout = QHBoxLayout()
        throttle_label = QLabel("Gaz")
        throttle_label.setStyleSheet("color: #44ff44; font-size: 10px;")
        throttle_label.setFixedWidth(35)
        self.throttle_bar = QProgressBar()
        self.throttle_bar.setRange(0, 100)
        self.throttle_bar.setTextVisible(False)
        self.throttle_bar.setFixedHeight(12)
        self.throttle_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2a2a4e;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #44ff44;
                border-radius: 3px;
            }
        """)
        throttle_layout.addWidget(throttle_label)
        throttle_layout.addWidget(self.throttle_bar)
        layout.addLayout(throttle_layout)
        
        # Brake
        brake_layout = QHBoxLayout()
        brake_label = QLabel("Frein")
        brake_label.setStyleSheet("color: #ff4444; font-size: 10px;")
        brake_label.setFixedWidth(35)
        self.brake_bar = QProgressBar()
        self.brake_bar.setRange(0, 100)
        self.brake_bar.setTextVisible(False)
        self.brake_bar.setFixedHeight(12)
        self.brake_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2a2a4e;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #ff4444;
                border-radius: 3px;
            }
        """)
        brake_layout.addWidget(brake_label)
        brake_layout.addWidget(self.brake_bar)
        layout.addLayout(brake_layout)
        
        self.setMinimumSize(150, 80)
    
    def set_pedals(self, throttle: float, brake: float):
        """Update pedal display (0-1 range)."""
        self.throttle_bar.setValue(int(throttle * 100))
        self.brake_bar.setValue(int(brake * 100))


class TelemetryPanel(QFrame):
    """
    Main telemetry panel - clean, ergonomic display of live AC data.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            TelemetryPanel {
                background-color: #0f0f1a;
                border: 1px solid #16213e;
                border-radius: 12px;
            }
        """)
        
        self._setup_ui()
        self._telemetry = TelemetryData()
    
    def _setup_ui(self):
        """Setup the telemetry UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QLabel("📡 Télémétrie Live")
        header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #fff;
            padding: 5px;
        """)
        layout.addWidget(header)
        
        # Connection status
        self.status_label = QLabel("⚫ Non connecté")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        # Main gauges row
        gauges_layout = QHBoxLayout()
        gauges_layout.setSpacing(10)
        
        self.speed_gauge = GaugeWidget("Vitesse", "km/h", max_value=300)
        self.rpm_gauge = GaugeWidget("RPM", "tr/min", max_value=9000)
        self.gear_gauge = GaugeWidget("Rapport", "", max_value=7)
        
        gauges_layout.addWidget(self.speed_gauge)
        gauges_layout.addWidget(self.rpm_gauge)
        gauges_layout.addWidget(self.gear_gauge)
        
        layout.addLayout(gauges_layout)
        
        # Second row: Tires, G-Force, Pedals
        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)
        
        self.tire_widget = TireTempsWidget()
        self.gforce_widget = GForceWidget()
        self.pedal_widget = PedalWidget()
        
        info_layout.addWidget(self.tire_widget)
        info_layout.addWidget(self.gforce_widget)
        info_layout.addWidget(self.pedal_widget)
        
        layout.addLayout(info_layout)
        
        layout.addStretch()
    
    def update_telemetry(self, data: TelemetryData):
        """Update all telemetry displays."""
        self._telemetry = data
        
        # Update connection status
        if data.is_connected:
            self.status_label.setText("🟢 Connecté à AC")
            self.status_label.setStyleSheet("color: #44ff44; font-size: 11px;")
        else:
            self.status_label.setText("⚫ Non connecté")
            self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        
        # Update gauges
        self.speed_gauge.set_value(data.speed_kmh)
        self.rpm_gauge.max_value = data.max_rpm if data.max_rpm > 0 else 8000
        self.rpm_gauge.set_value(data.rpm)
        
        # Gear display
        gear_text = "N" if data.gear == 0 else ("R" if data.gear < 0 else str(data.gear))
        self.gear_gauge.value_label.setText(gear_text)
        self.gear_gauge.value_label.setStyleSheet("color: #fff; font-size: 24px; font-weight: bold;")
        
        # Update tire temps
        self.tire_widget.set_temps(
            data.tire_temp_fl, data.tire_temp_fr,
            data.tire_temp_rl, data.tire_temp_rr
        )
        
        # Update G-forces
        self.gforce_widget.set_g_forces(data.g_lateral, data.g_longitudinal)
        
        # Update pedals
        self.pedal_widget.set_pedals(data.throttle, data.brake)
    
    def get_telemetry(self) -> TelemetryData:
        """Get current telemetry data."""
        return self._telemetry
