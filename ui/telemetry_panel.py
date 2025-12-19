"""
Telemetry Panel - Live telemetry display from Assetto Corsa.
Modern Initial D black/red gradient design.
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
    
    tire_temp_fl: float = 0.0
    tire_temp_fr: float = 0.0
    tire_temp_rl: float = 0.0
    tire_temp_rr: float = 0.0
    
    g_lateral: float = 0.0
    g_longitudinal: float = 0.0
    
    throttle: float = 0.0
    brake: float = 0.0
    
    is_connected: bool = False


class ModernGaugeWidget(QFrame):
    """Modern gauge with Initial D styling."""
    
    def __init__(self, title: str, unit: str = "", max_value: float = 100, parent=None):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.max_value = max_value
        self.value = 0.0
        
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a0000, stop:1 #000000);
                border: 2px solid #ff0000;
                border-radius: 12px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(15, 12, 15, 12)
        
        # Title
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            color: #ff0000;
            font-family: 'Arial', sans-serif;
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        layout.addWidget(self.title_label)
        
        # Value
        self.value_label = QLabel("0")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("""
            color: #ffffff;
            font-family: 'Arial', sans-serif;
            font-size: 48px;
            font-weight: bold;
        """)
        layout.addWidget(self.value_label)
        
        # Unit
        self.unit_label = QLabel(unit)
        self.unit_label.setAlignment(Qt.AlignCenter)
        self.unit_label.setStyleSheet("""
            color: #888;
            font-family: 'Arial', sans-serif;
            font-size: 14px;
            font-weight: bold;
        """)
        layout.addWidget(self.unit_label)
        
        self.setMinimumSize(180, 140)
    
    def set_value(self, value: float):
        """Update the gauge value."""
        self.value = value
        
        if value >= 1000:
            self.value_label.setText(f"{int(value)}")
        elif value >= 100:
            self.value_label.setText(f"{int(value)}")
        elif value >= 10:
            self.value_label.setText(f"{value:.1f}")
        else:
            self.value_label.setText(f"{value:.2f}")
        
        # Color based on percentage
        percent = (value / self.max_value) * 100 if self.max_value > 0 else 0
        
        if percent > 90:
            self.value_label.setStyleSheet("""
                color: #ff0000;
                font-family: 'Arial', sans-serif;
                font-size: 32px;
                font-weight: bold;
            """)
        elif percent > 75:
            self.value_label.setStyleSheet("""
                color: #ff8800;
                font-family: 'Arial', sans-serif;
                font-size: 32px;
                font-weight: bold;
            """)
        else:
            self.value_label.setStyleSheet("""
                color: #ffffff;
                font-family: 'Arial', sans-serif;
                font-size: 32px;
                font-weight: bold;
            """)


class TireTempsWidget(QFrame):
    """Tire temperatures display with Initial D styling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a0000, stop:1 #000000);
                border: 2px solid #ff0000;
                border-radius: 12px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 12, 15, 12)
        
        # Title
        title = QLabel("🔥 Températures Pneus")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #ff0000;
            font-family: 'Arial', sans-serif;
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        layout.addWidget(title)
        
        # Grid layout for tires
        grid = QGridLayout()
        grid.setSpacing(8)
        
        # Create tire labels
        self.tire_labels = {}
        positions = [
            ("AVG", 0, 0), ("AVD", 0, 1),
            ("ARG", 1, 0), ("ARD", 1, 1)
        ]
        
        for name, row, col in positions:
            container = QFrame()
            container.setStyleSheet("""
                QFrame {
                    background-color: rgba(0, 0, 0, 0.5);
                    border: 1px solid #ff0000;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
            
            v_layout = QVBoxLayout(container)
            v_layout.setSpacing(3)
            v_layout.setContentsMargins(8, 6, 8, 6)
            
            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setStyleSheet("""
                color: #888;
                font-family: 'Arial', sans-serif;
                font-size: 12px;
                font-weight: bold;
            """)
            v_layout.addWidget(name_label)
            
            temp_label = QLabel("--°C")
            temp_label.setAlignment(Qt.AlignCenter)
            temp_label.setStyleSheet("""
                color: #ffffff;
                font-family: 'Arial', sans-serif;
                font-size: 20px;
                font-weight: bold;
            """)
            v_layout.addWidget(temp_label)
            
            self.tire_labels[name] = temp_label
            grid.addWidget(container, row, col)
        
        layout.addLayout(grid)
    
    def set_temps(self, fl: float, fr: float, rl: float, rr: float):
        """Update tire temperatures."""
        temps = {
            "AVG": fl,
            "AVD": fr,
            "ARG": rl,
            "ARD": rr
        }
        
        for name, temp in temps.items():
            if temp > 0:
                self.tire_labels[name].setText(f"{int(temp)}°C")
                
                # Color based on temp
                if temp < 60:
                    color = "#0088ff"  # Cold - blue
                elif temp < 80:
                    color = "#00ff00"  # Optimal - green
                elif temp < 100:
                    color = "#ff8800"  # Hot - orange
                else:
                    color = "#ff0000"  # Overheating - red
                
                self.tire_labels[name].setStyleSheet(f"""
                    color: {color};
                    font-family: 'Arial', sans-serif;
                    font-size: 16px;
                    font-weight: bold;
                """)
            else:
                self.tire_labels[name].setText("--°C")


class GForcesWidget(QFrame):
    """G-Forces display with Initial D styling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a0000, stop:1 #000000);
                border: 2px solid #ff0000;
                border-radius: 12px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 12, 15, 12)
        
        # Title
        title = QLabel("⚡ G-Forces")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #ff0000;
            font-family: 'Arial', sans-serif;
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        layout.addWidget(title)
        
        # Lateral G
        lat_container = QHBoxLayout()
        lat_label = QLabel("Lat:")
        lat_label.setStyleSheet("color: #888; font-size: 11px;")
        self.lat_value = QLabel("0.0 g")
        self.lat_value.setStyleSheet("""
            color: #ffffff;
            font-family: 'Arial', sans-serif;
            font-size: 16px;
            font-weight: bold;
        """)
        lat_container.addWidget(lat_label)
        lat_container.addWidget(self.lat_value)
        lat_container.addStretch()
        layout.addLayout(lat_container)
        
        # Longitudinal G
        lon_container = QHBoxLayout()
        lon_label = QLabel("Lon:")
        lon_label.setStyleSheet("color: #888; font-size: 11px;")
        self.lon_value = QLabel("0.0 g")
        self.lon_value.setStyleSheet("""
            color: #ffffff;
            font-family: 'Arial', sans-serif;
            font-size: 16px;
            font-weight: bold;
        """)
        lon_container.addWidget(lon_label)
        lon_container.addWidget(self.lon_value)
        lon_container.addStretch()
        layout.addLayout(lon_container)
        
        # Max G
        max_container = QHBoxLayout()
        max_label = QLabel("Max:")
        max_label.setStyleSheet("color: #888; font-size: 11px;")
        self.max_value = QLabel("0.0 g")
        self.max_value.setStyleSheet("""
            color: #ff0000;
            font-family: 'Arial', sans-serif;
            font-size: 16px;
            font-weight: bold;
        """)
        max_container.addWidget(max_label)
        max_container.addWidget(self.max_value)
        max_container.addStretch()
        layout.addLayout(max_container)
        
        self.max_g = 0.0
    
    def set_g_forces(self, lateral: float, longitudinal: float):
        """Update G-forces."""
        self.lat_value.setText(f"{lateral:.2f} g")
        self.lon_value.setText(f"{longitudinal:.2f} g")
        
        # Calculate total G
        total_g = (lateral**2 + longitudinal**2)**0.5
        if total_g > self.max_g:
            self.max_g = total_g
        
        self.max_value.setText(f"{self.max_g:.2f} g")


class PedalsWidget(QFrame):
    """Pedals display with Initial D styling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a0000, stop:1 #000000);
                border: 2px solid #ff0000;
                border-radius: 12px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 12, 15, 12)
        
        # Title
        title = QLabel("🚗 Pédales")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #ff0000;
            font-family: 'Arial', sans-serif;
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        layout.addWidget(title)
        
        # Throttle
        throttle_layout = QVBoxLayout()
        throttle_label = QLabel("Gaz")
        throttle_label.setStyleSheet("color: #888; font-size: 11px;")
        throttle_layout.addWidget(throttle_label)
        
        self.throttle_bar = QProgressBar()
        self.throttle_bar.setRange(0, 100)
        self.throttle_bar.setValue(0)
        self.throttle_bar.setTextVisible(False)
        self.throttle_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ff0000;
                border-radius: 4px;
                background-color: rgba(0, 0, 0, 0.5);
                height: 20px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff00, stop:1 #88ff00);
                border-radius: 3px;
            }
        """)
        throttle_layout.addWidget(self.throttle_bar)
        layout.addLayout(throttle_layout)
        
        # Brake
        brake_layout = QVBoxLayout()
        brake_label = QLabel("Frein")
        brake_label.setStyleSheet("color: #888; font-size: 11px;")
        brake_layout.addWidget(brake_label)
        
        self.brake_bar = QProgressBar()
        self.brake_bar.setRange(0, 100)
        self.brake_bar.setValue(0)
        self.brake_bar.setTextVisible(False)
        self.brake_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ff0000;
                border-radius: 4px;
                background-color: rgba(0, 0, 0, 0.5);
                height: 20px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff0000, stop:1 #ff8800);
                border-radius: 3px;
            }
        """)
        brake_layout.addWidget(self.brake_bar)
        layout.addLayout(brake_layout)
    
    def set_pedals(self, throttle: float, brake: float):
        """Update pedal positions (0.0 to 1.0)."""
        self.throttle_bar.setValue(int(throttle * 100))
        self.brake_bar.setValue(int(brake * 100))


class TelemetryPanel(QWidget):
    """Main telemetry panel with modern Initial D design."""
    
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
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📊 Télémétrie Live")
        title.setStyleSheet("""
            color: #ff0000;
            font-family: 'Arial', sans-serif;
            font-size: 22px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        layout.addWidget(title)
        
        # Connection status
        self.status_label = QLabel("● Connecté à AC")
        self.status_label.setStyleSheet("""
            color: #00ff00;
            font-family: 'Arial', sans-serif;
            font-size: 12px;
        """)
        layout.addWidget(self.status_label)
        
        # Main gauges row
        gauges_row = QHBoxLayout()
        gauges_row.setSpacing(15)
        
        self.speed_gauge = ModernGaugeWidget("Vitesse", "km/h", 400)
        self.rpm_gauge = ModernGaugeWidget("RPM", "tr/min", 8000)
        self.gear_gauge = ModernGaugeWidget("Rapport", "", 6)
        
        gauges_row.addWidget(self.speed_gauge)
        gauges_row.addWidget(self.rpm_gauge)
        gauges_row.addWidget(self.gear_gauge)
        
        layout.addLayout(gauges_row)
        
        # Second row
        second_row = QHBoxLayout()
        second_row.setSpacing(15)
        
        self.tire_temps = TireTempsWidget()
        self.g_forces = GForcesWidget()
        self.pedals = PedalsWidget()
        
        second_row.addWidget(self.tire_temps)
        second_row.addWidget(self.g_forces)
        second_row.addWidget(self.pedals)
        
        layout.addLayout(second_row)
        
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
            self.status_label.setText("● Connecté à AC")
            self.status_label.setStyleSheet("""
                color: #00ff00;
                font-family: 'Arial', sans-serif;
                font-size: 12px;
            """)
        else:
            self.status_label.setText("● Déconnecté")
            self.status_label.setStyleSheet("""
                color: #ff0000;
                font-family: 'Arial', sans-serif;
                font-size: 12px;
            """)
        
        # Update gauges
        self.speed_gauge.set_value(data.speed_kmh)
        self.rpm_gauge.set_value(data.rpm)
        self.rpm_gauge.max_value = data.max_rpm
        self.gear_gauge.set_value(data.gear)
        
        # Update tire temps
        self.tire_temps.set_temps(
            data.tire_temp_fl,
            data.tire_temp_fr,
            data.tire_temp_rl,
            data.tire_temp_rr
        )
        
        # Update G-forces
        self.g_forces.set_g_forces(data.g_lateral, data.g_longitudinal)
        
        # Update pedals
        self.pedals.set_pedals(data.throttle, data.brake)
