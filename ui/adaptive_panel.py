"""
Adaptive Setup Panel V2 - Simplified UI with better visual hierarchy.
Reduced borders, cleaner layout, professional appearance.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QSlider, QComboBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal


class ConditionsWidget(QFrame):
    """Widget for adjusting track conditions - simplified design."""
    
    conditions_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.02);
                border: none;
                border-left: 3px solid #ff0000;
                border-radius: 0px;
                padding: 25px 30px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        
        # Title
        title = QLabel("CONDITIONS")
        title.setStyleSheet("""
            color: #ff0000;
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 2px;
            margin-bottom: 5px;
        """)
        layout.addWidget(title)
        
        # Temperature slider
        temp_layout = QHBoxLayout()
        temp_layout.setSpacing(15)
        
        temp_label = QLabel("Air Temp")
        temp_label.setStyleSheet("color: #999999; font-size: 12px;")
        temp_label.setFixedWidth(80)
        temp_layout.addWidget(temp_label)
        
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(0, 50)
        self.temp_slider.setValue(25)
        self.temp_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 0.08);
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ff0000;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)
        temp_layout.addWidget(self.temp_slider)
        
        self.temp_value = QLabel("25°C")
        self.temp_value.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold;")
        self.temp_value.setFixedWidth(50)
        self.temp_value.setAlignment(Qt.AlignRight)
        temp_layout.addWidget(self.temp_value)
        
        layout.addLayout(temp_layout)
        
        # Track temperature slider
        track_temp_layout = QHBoxLayout()
        track_temp_layout.setSpacing(15)
        
        track_temp_label = QLabel("Track Temp")
        track_temp_label.setStyleSheet("color: #999999; font-size: 12px;")
        track_temp_label.setFixedWidth(80)
        track_temp_layout.addWidget(track_temp_label)
        
        self.track_temp_slider = QSlider(Qt.Horizontal)
        self.track_temp_slider.setRange(10, 60)
        self.track_temp_slider.setValue(30)
        self.track_temp_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 0.08);
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ff0000;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)
        track_temp_layout.addWidget(self.track_temp_slider)
        
        self.track_temp_value = QLabel("30°C")
        self.track_temp_value.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold;")
        self.track_temp_value.setFixedWidth(50)
        self.track_temp_value.setAlignment(Qt.AlignRight)
        track_temp_layout.addWidget(self.track_temp_value)
        
        layout.addLayout(track_temp_layout)
        
        # Weather selector
        weather_layout = QHBoxLayout()
        weather_layout.setSpacing(15)
        
        weather_label = QLabel("Weather")
        weather_label.setStyleSheet("color: #999999; font-size: 12px;")
        weather_label.setFixedWidth(80)
        weather_layout.addWidget(weather_label)
        
        self.weather_combo = QComboBox()
        self.weather_combo.addItems(["☀️ Sec", "🌧️ Pluie légère", "⛈️ Pluie forte", "💧 Mouillé"])
        self.weather_combo.setStyleSheet("""
            QComboBox {
                background: rgba(0, 0, 0, 0.5);
                color: #ffffff;
                border: 1px solid rgba(255, 0, 0, 0.3);
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background: #1a1a1a;
                color: #ffffff;
                selection-background-color: #ff0000;
                border: 1px solid rgba(255, 0, 0, 0.3);
            }
        """)
        weather_layout.addWidget(self.weather_combo)
        
        layout.addLayout(weather_layout)
        
        # Connect signals
        self.temp_slider.valueChanged.connect(self._on_temp_changed)
        self.track_temp_slider.valueChanged.connect(self._on_track_temp_changed)
        self.weather_combo.currentIndexChanged.connect(self._on_conditions_changed)
    
    def _on_temp_changed(self, value):
        """Handle temperature change."""
        self.temp_value.setText(f"{value}°C")
        self._on_conditions_changed()
    
    def _on_track_temp_changed(self, value):
        """Handle track temperature change."""
        self.track_temp_value.setText(f"{value}°C")
        self._on_conditions_changed()
    
    def _on_conditions_changed(self):
        """Emit conditions changed signal."""
        weather_map = {
            0: "dry",
            1: "light_rain",
            2: "heavy_rain",
            3: "wet"
        }
        
        self.conditions_changed.emit({
            "temperature": self.temp_slider.value(),
            "track_temp": self.track_temp_slider.value(),
            "weather": weather_map.get(self.weather_combo.currentIndex(), "dry")
        })
    
    def get_conditions(self) -> dict:
        """Get current conditions."""
        weather_map = {
            0: "dry",
            1: "light_rain",
            2: "heavy_rain",
            3: "wet"
        }
        
        return {
            "temperature": self.temp_slider.value(),
            "track_temp": self.track_temp_slider.value(),
            "weather": weather_map.get(self.weather_combo.currentIndex(), "dry")
        }


class LearningStatsWidget(QFrame):
    """Widget showing AI learning statistics - cleaner design."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.02);
                border: none;
                border-left: 3px solid #ff0000;
                border-radius: 0px;
                padding: 25px 30px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("AI LEARNING")
        title.setStyleSheet("""
            color: #ff0000;
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 2px;
            margin-bottom: 5px;
        """)
        layout.addWidget(title)
        
        # Stats in compact format
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(10)
        
        # Laps
        laps_row = QHBoxLayout()
        laps_label = QLabel("Laps Recorded")
        laps_label.setStyleSheet("color: #999999; font-size: 12px;")
        laps_row.addWidget(laps_label)
        laps_row.addStretch()
        self.laps_value = QLabel("0")
        self.laps_value.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        laps_row.addWidget(self.laps_value)
        stats_layout.addLayout(laps_row)
        
        # Best time
        best_row = QHBoxLayout()
        best_label = QLabel("Best Time")
        best_label.setStyleSheet("color: #999999; font-size: 12px;")
        best_row.addWidget(best_label)
        best_row.addStretch()
        self.best_time_value = QLabel("--")
        self.best_time_value.setStyleSheet("color: #00ff00; font-size: 14px; font-weight: bold;")
        best_row.addWidget(self.best_time_value)
        stats_layout.addLayout(best_row)
        
        # Consistency
        cons_row = QHBoxLayout()
        cons_label = QLabel("Consistency")
        cons_label.setStyleSheet("color: #999999; font-size: 12px;")
        cons_row.addWidget(cons_label)
        cons_row.addStretch()
        self.consistency_value = QLabel("--")
        self.consistency_value.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        cons_row.addWidget(self.consistency_value)
        stats_layout.addLayout(cons_row)
        
        layout.addLayout(stats_layout)
        
        # Confidence bar
        layout.addSpacing(5)
        conf_label = QLabel("AI CONFIDENCE")
        conf_label.setStyleSheet("color: #666666; font-size: 11px; letter-spacing: 1px;")
        layout.addWidget(conf_label)
        
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setRange(0, 100)
        self.confidence_bar.setValue(0)
        self.confidence_bar.setTextVisible(True)
        self.confidence_bar.setFormat("%p%")
        self.confidence_bar.setFixedHeight(18)
        self.confidence_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 2px;
                text-align: center;
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff0000, stop:1 #ff4444);
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.confidence_bar)
    
    def update_stats(self, stats: dict):
        """Update displayed statistics."""
        if not stats.get("has_data", False):
            self.laps_value.setText("0")
            self.best_time_value.setText("--")
            self.consistency_value.setText("--")
            self.confidence_bar.setValue(0)
            return
        
        self.laps_value.setText(str(stats['total_laps']))
        self.best_time_value.setText(f"{stats['your_best']:.3f}s")
        self.consistency_value.setText(f"±{stats['consistency']:.3f}s")
        
        # Calculate confidence (0-100%)
        confidence = min(stats['total_laps'] / 50.0 * 100, 100)
        self.confidence_bar.setValue(int(confidence))


class PerformanceComparisonWidget(QFrame):
    """Widget showing performance comparison - simplified."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.02);
                border: none;
                border-left: 3px solid #ff0000;
                border-radius: 0px;
                padding: 25px 30px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("PERFORMANCE")
        title.setStyleSheet("""
            color: #ff0000;
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 2px;
            margin-bottom: 5px;
        """)
        layout.addWidget(title)
        
        # Comparison info
        self.comparison_label = QLabel("Complete more laps to see comparison")
        self.comparison_label.setStyleSheet("""
            color: #666666;
            font-size: 12px;
            font-style: italic;
        """)
        self.comparison_label.setWordWrap(True)
        layout.addWidget(self.comparison_label)
        
        # Rank estimate
        self.rank_label = QLabel("")
        self.rank_label.setStyleSheet("""
            color: #ffffff;
            font-size: 16px;
            font-weight: bold;
        """)
        self.rank_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.rank_label)
    
    def update_comparison(self, stats: dict):
        """Update comparison display."""
        if not stats.get("has_data", False):
            self.comparison_label.setText("Complete more laps to see comparison")
            self.rank_label.setText("")
            return
        
        rank = stats.get("rank_estimate", "N/A")
        percentile = stats.get("percentile", 0)
        
        self.rank_label.setText(f"🏆 {rank}")
        self.comparison_label.setText(
            f"You're faster than {percentile:.0f}% of drivers on this combo"
        )


class AdaptivePanel(QWidget):
    """Main adaptive setup panel - simplified and cleaner."""
    
    apply_optimization = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
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
        
        title = QLabel("ADAPTIVE AI")
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
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)
        
        # Conditions widget
        self.conditions_widget = ConditionsWidget()
        content_layout.addWidget(self.conditions_widget)
        
        # Learning stats widget
        self.learning_stats = LearningStatsWidget()
        content_layout.addWidget(self.learning_stats)
        
        # Performance comparison
        self.performance_comparison = PerformanceComparisonWidget()
        content_layout.addWidget(self.performance_comparison)
        
        # Apply button
        self.apply_button = QPushButton("⚡ APPLY AI OPTIMIZATION")
        self.apply_button.clicked.connect(self.apply_optimization.emit)
        self.apply_button.setMinimumHeight(50)
        self.apply_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff0000, stop:1 #cc0000);
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff3333, stop:1 #ff0000);
            }
            QPushButton:pressed {
                background: #990000;
            }
            QPushButton:disabled {
                background: #333333;
                color: #666666;
            }
        """)
        content_layout.addWidget(self.apply_button)
        
        content_layout.addStretch()
        
        layout.addWidget(content)
    
    def update_stats(self, stats: dict):
        """Update learning statistics."""
        self.learning_stats.update_stats(stats)
        self.performance_comparison.update_comparison(stats)
        
        # Always enable apply button - conditions-based optimization works without learning data
        # Learning data just adds extra optimizations on top
        self.apply_button.setEnabled(True)
    
    def get_conditions(self) -> dict:
        """Get current track conditions."""
        return self.conditions_widget.get_conditions()
