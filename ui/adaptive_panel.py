"""
Adaptive Setup Panel - UI for adaptive AI features.
Shows learning progress, conditions adjustment, and performance comparison.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QSlider, QComboBox, QGroupBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class ConditionsWidget(QFrame):
    """Widget for adjusting track conditions."""
    
    conditions_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background: rgba(26, 0, 0, 0.3);
                border: none;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("CONDITIONS")
        title.setStyleSheet("""
            color: #ff0000;
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 2px;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)
        
        # Temperature slider
        temp_layout = QHBoxLayout()
        temp_label = QLabel("Air Temp")
        temp_label.setStyleSheet("color: #999999; font-size: 12px;")
        temp_label.setFixedWidth(100)
        temp_layout.addWidget(temp_label)
        
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(0, 50)
        self.temp_slider.setValue(25)
        self.temp_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 0.1);
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ff0000;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
        """)
        temp_layout.addWidget(self.temp_slider)
        
        self.temp_value = QLabel("25°C")
        self.temp_value.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        self.temp_value.setFixedWidth(60)
        self.temp_value.setAlignment(Qt.AlignRight)
        temp_layout.addWidget(self.temp_value)
        
        layout.addLayout(temp_layout)
        
        # Track temperature slider
        track_temp_layout = QHBoxLayout()
        track_temp_label = QLabel("Track Temp")
        track_temp_label.setStyleSheet("color: #999999; font-size: 12px;")
        track_temp_label.setFixedWidth(100)
        track_temp_layout.addWidget(track_temp_label)
        
        self.track_temp_slider = QSlider(Qt.Horizontal)
        self.track_temp_slider.setRange(10, 60)
        self.track_temp_slider.setValue(30)
        self.track_temp_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 0.1);
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ff0000;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
        """)
        track_temp_layout.addWidget(self.track_temp_slider)
        
        self.track_temp_value = QLabel("30°C")
        self.track_temp_value.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        self.track_temp_value.setFixedWidth(60)
        self.track_temp_value.setAlignment(Qt.AlignRight)
        track_temp_layout.addWidget(self.track_temp_value)
        
        layout.addLayout(track_temp_layout)
        
        # Weather selector
        weather_layout = QHBoxLayout()
        weather_label = QLabel("Weather")
        weather_label.setStyleSheet("color: #999999; font-size: 12px;")
        weather_label.setFixedWidth(100)
        weather_layout.addWidget(weather_label)
        
        self.weather_combo = QComboBox()
        self.weather_combo.addItems(["☀️ Sec", "🌧️ Pluie légère", "⛈️ Pluie forte", "💧 Mouillé"])
        self.weather_combo.setStyleSheet("""
            QComboBox {
                background: rgba(0, 0, 0, 0.5);
                color: #ffffff;
                border: 1px solid #ff0000;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background: #1a1a1a;
                color: #ffffff;
                selection-background-color: #ff0000;
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
    """Widget showing AI learning statistics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background: rgba(26, 0, 0, 0.3);
                border: none;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🤖 Apprentissage IA")
        title.setStyleSheet("""
            color: #ff0000;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)
        
        # Stats labels
        self.laps_label = QLabel("Tours enregistrés: 0")
        self.laps_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        layout.addWidget(self.laps_label)
        
        self.best_time_label = QLabel("Meilleur temps: --")
        self.best_time_label.setStyleSheet("color: #00ff00; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.best_time_label)
        
        self.consistency_label = QLabel("Constance: --")
        self.consistency_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        layout.addWidget(self.consistency_label)
        
        # Confidence bar
        conf_label = QLabel("Confiance IA:")
        conf_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(conf_label)
        
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setRange(0, 100)
        self.confidence_bar.setValue(0)
        self.confidence_bar.setTextVisible(True)
        self.confidence_bar.setFormat("%p%")
        self.confidence_bar.setFixedHeight(20)
        self.confidence_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background: #ff0000;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.confidence_bar)
    
    def update_stats(self, stats: dict):
        """Update displayed statistics."""
        if not stats.get("has_data", False):
            self.laps_label.setText("Tours enregistrés: 0")
            self.best_time_label.setText("Meilleur temps: --")
            self.consistency_label.setText("Constance: --")
            self.confidence_bar.setValue(0)
            return
        
        self.laps_label.setText(f"Tours enregistrés: {stats['total_laps']}")
        self.best_time_label.setText(f"Meilleur temps: {stats['your_best']:.3f}s")
        self.consistency_label.setText(f"Constance: ±{stats['consistency']:.3f}s")
        
        # Calculate confidence (0-100%)
        confidence = min(stats['total_laps'] / 50.0 * 100, 100)
        self.confidence_bar.setValue(int(confidence))


class PerformanceComparisonWidget(QFrame):
    """Widget showing performance comparison with community."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background: rgba(26, 0, 0, 0.3);
                border: none;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📊 Comparaison")
        title.setStyleSheet("""
            color: #ff0000;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)
        
        # Rank label
        self.rank_label = QLabel("Classement: --")
        self.rank_label.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold;")
        layout.addWidget(self.rank_label)
        
        # Percentile label
        self.percentile_label = QLabel("Percentile: --")
        self.percentile_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        layout.addWidget(self.percentile_label)
        
        # Improvement potential
        self.improvement_label = QLabel("Potentiel: --")
        self.improvement_label.setStyleSheet("color: #ffaa00; font-size: 14px;")
        layout.addWidget(self.improvement_label)
        
        # Info text
        info = QLabel("Basé sur tes performances enregistrées")
        info.setStyleSheet("color: #888; font-size: 11px; font-style: italic;")
        info.setWordWrap(True)
        layout.addWidget(info)
    
    def update_comparison(self, stats: dict):
        """Update comparison display."""
        if not stats.get("has_data", False):
            self.rank_label.setText("Classement: --")
            self.percentile_label.setText("Percentile: --")
            self.improvement_label.setText("Potentiel: --")
            return
        
        self.rank_label.setText(f"Classement: {stats['rank_estimate']}")
        self.percentile_label.setText(f"Percentile: {stats['percentile']:.1f}%")
        
        if stats['improvement_potential'] > 0:
            self.improvement_label.setText(
                f"Potentiel: -{stats['improvement_potential']:.3f}s"
            )
        else:
            self.improvement_label.setText("Potentiel: Tu es au top! 🏆")


class AdaptivePanel(QWidget):
    """Main panel for adaptive AI features."""
    
    apply_adaptive = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("🤖 IA Adaptive")
        title.setStyleSheet("""
            color: #ff0000;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "L'IA apprend de ton style de conduite et adapte les setups "
            "aux conditions de piste en temps réel."
        )
        desc.setStyleSheet("color: #cccccc; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Conditions widget
        self.conditions_widget = ConditionsWidget()
        layout.addWidget(self.conditions_widget)
        
        # Learning stats
        self.learning_stats = LearningStatsWidget()
        layout.addWidget(self.learning_stats)
        
        # Performance comparison
        self.performance_comparison = PerformanceComparisonWidget()
        layout.addWidget(self.performance_comparison)
        
        # Apply button
        self.apply_button = QPushButton("⚡ Appliquer l'Optimisation IA")
        self.apply_button.clicked.connect(self.apply_adaptive.emit)
        self.apply_button.setMinimumHeight(55)
        self.apply_button.setStyleSheet("""
            QPushButton {
                background: #ff0000;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                padding: 15px;
            }
            QPushButton:hover {
                background: #ff3333;
            }
            QPushButton:pressed {
                background: #cc0000;
            }
        """)
        layout.addWidget(self.apply_button)
        
        layout.addStretch()
    
    def update_stats(self, stats: dict):
        """Update all statistics."""
        self.learning_stats.update_stats(stats)
        self.performance_comparison.update_comparison(stats)
    
    def get_conditions(self) -> dict:
        """Get current conditions."""
        return self.conditions_widget.get_conditions()
