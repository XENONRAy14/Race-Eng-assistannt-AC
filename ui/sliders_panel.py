"""
Sliders Panel - Driver profile preference sliders.
Provides interactive sliders for adjusting driving style preferences.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSlider, QGroupBox, QFrame
)
from PySide6.QtCore import Qt, Signal

from models.driver_profile import DriverProfile


class LabeledSlider(QWidget):
    """A slider with left/right labels and value display."""
    
    valueChanged = Signal(float)
    
    def __init__(
        self,
        label_left: str,
        label_right: str,
        initial_value: float = 50.0,
        tooltip: str = "",
        parent=None
    ):
        super().__init__(parent)
        
        self.label_left_text = label_left
        self.label_right_text = label_right
        
        self._setup_ui(initial_value, tooltip)
    
    def _setup_ui(self, initial_value: float, tooltip: str) -> None:
        """Set up the slider UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        
        # Labels row
        labels_layout = QHBoxLayout()
        
        self.left_label = QLabel(self.label_left_text)
        self.left_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        
        self.value_label = QLabel(f"{initial_value:.0f}%")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 12px; color: #888;")
        
        self.right_label = QLabel(self.label_right_text)
        self.right_label.setAlignment(Qt.AlignRight)
        self.right_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        
        labels_layout.addWidget(self.left_label)
        labels_layout.addStretch()
        labels_layout.addWidget(self.value_label)
        labels_layout.addStretch()
        labels_layout.addWidget(self.right_label)
        
        layout.addLayout(labels_layout)
        
        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(int(initial_value))
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(25)
        
        if tooltip:
            self.slider.setToolTip(tooltip)
        
        self.slider.valueChanged.connect(self._on_value_changed)
        
        # Style the slider
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #444;
                height: 8px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:0.5 #888, stop:1 #2196F3);
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #fff;
                border: 2px solid #666;
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #eee;
                border-color: #2196F3;
            }
        """)
        
        layout.addWidget(self.slider)
    
    def _on_value_changed(self, value: int) -> None:
        """Handle slider value change."""
        self.value_label.setText(f"{value}%")
        self.valueChanged.emit(float(value))
    
    def value(self) -> float:
        """Get current slider value."""
        return float(self.slider.value())
    
    def setValue(self, value: float) -> None:
        """Set slider value."""
        self.slider.setValue(int(value))


class SlidersPanel(QWidget):
    """
    Panel containing all driver preference sliders.
    Emits signal when any slider changes.
    """
    
    profileChanged = Signal(DriverProfile)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._profile: DriverProfile = DriverProfile()
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the sliders panel UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Profil Pilote")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #fff;
            padding: 5px;
        """)
        layout.addWidget(title)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #444;")
        layout.addWidget(separator)
        
        # Sliders group
        sliders_group = QGroupBox("Préférences de conduite")
        sliders_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        sliders_layout = QVBoxLayout(sliders_group)
        
        # Stability ↔ Rotation
        self.stability_rotation_slider = LabeledSlider(
            label_left="Stabilité",
            label_right="Rotation",
            initial_value=self._profile.stability_rotation,
            tooltip="Équilibre entre stabilité et agilité de la voiture"
        )
        self.stability_rotation_slider.valueChanged.connect(
            lambda v: self._on_slider_changed("stability_rotation", v)
        )
        sliders_layout.addWidget(self.stability_rotation_slider)
        
        # Grip ↔ Slide
        self.grip_slide_slider = LabeledSlider(
            label_left="Grip",
            label_right="Glisse",
            initial_value=self._profile.grip_slide,
            tooltip="Préférence entre grip maximum et glisse contrôlée"
        )
        self.grip_slide_slider.valueChanged.connect(
            lambda v: self._on_slider_changed("grip_slide", v)
        )
        sliders_layout.addWidget(self.grip_slide_slider)
        
        # Safety ↔ Aggression
        self.safety_aggression_slider = LabeledSlider(
            label_left="Sécurité",
            label_right="Agressivité",
            initial_value=self._profile.safety_aggression,
            tooltip="Style de conduite prudent vs agressif"
        )
        self.safety_aggression_slider.valueChanged.connect(
            lambda v: self._on_slider_changed("safety_aggression", v)
        )
        sliders_layout.addWidget(self.safety_aggression_slider)
        
        # Drift ↔ Grip
        self.drift_grip_slider = LabeledSlider(
            label_left="Drift",
            label_right="Grip",
            initial_value=self._profile.drift_grip,
            tooltip="Setup orienté drift vs grip pur"
        )
        self.drift_grip_slider.valueChanged.connect(
            lambda v: self._on_slider_changed("drift_grip", v)
        )
        sliders_layout.addWidget(self.drift_grip_slider)
        
        # Comfort ↔ Performance
        self.comfort_performance_slider = LabeledSlider(
            label_left="Confort",
            label_right="Performance",
            initial_value=self._profile.comfort_performance,
            tooltip="Suspensions souples (confort) vs rigides (performance)"
        )
        self.comfort_performance_slider.valueChanged.connect(
            lambda v: self._on_slider_changed("comfort_performance", v)
        )
        sliders_layout.addWidget(self.comfort_performance_slider)
        
        layout.addWidget(sliders_group)
        
        # Profile summary
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("""
            color: #888;
            font-size: 11px;
            padding: 5px;
        """)
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
        
        layout.addStretch()
        
        self._update_summary()
    
    def _on_slider_changed(self, slider_name: str, value: float) -> None:
        """Handle slider value change."""
        setattr(self._profile, slider_name, value)
        self._update_summary()
        self.profileChanged.emit(self._profile)
    
    def _update_summary(self) -> None:
        """Update the profile summary text."""
        factors = self._profile.get_all_factors()
        
        traits = []
        
        if factors["stability"] > 0.6:
            traits.append("stable")
        elif factors["rotation"] > 0.6:
            traits.append("agile")
        
        if factors["grip"] > 0.7:
            traits.append("grip-focused")
        elif factors["slide"] > 0.6:
            traits.append("slide-friendly")
        
        if factors["aggression"] > 0.6:
            traits.append("aggressive")
        elif factors["safety"] > 0.7:
            traits.append("safe")
        
        if factors["drift"] > 0.5:
            traits.append("drift-oriented")
        
        if factors["performance"] > 0.6:
            traits.append("performance")
        elif factors["comfort"] > 0.6:
            traits.append("comfortable")
        
        if traits:
            summary = f"Style: {', '.join(traits)}"
        else:
            summary = "Style: balanced"
        
        self.summary_label.setText(summary)
    
    def get_profile(self) -> DriverProfile:
        """Get the current driver profile."""
        return self._profile
    
    def set_profile(self, profile: DriverProfile) -> None:
        """Set the driver profile and update sliders."""
        self._profile = profile
        
        # Update sliders without triggering signals
        self.stability_rotation_slider.slider.blockSignals(True)
        self.grip_slide_slider.slider.blockSignals(True)
        self.safety_aggression_slider.slider.blockSignals(True)
        self.drift_grip_slider.slider.blockSignals(True)
        self.comfort_performance_slider.slider.blockSignals(True)
        
        self.stability_rotation_slider.setValue(profile.stability_rotation)
        self.grip_slide_slider.setValue(profile.grip_slide)
        self.safety_aggression_slider.setValue(profile.safety_aggression)
        self.drift_grip_slider.setValue(profile.drift_grip)
        self.comfort_performance_slider.setValue(profile.comfort_performance)
        
        self.stability_rotation_slider.slider.blockSignals(False)
        self.grip_slide_slider.slider.blockSignals(False)
        self.safety_aggression_slider.slider.blockSignals(False)
        self.drift_grip_slider.slider.blockSignals(False)
        self.comfort_performance_slider.slider.blockSignals(False)
        
        self._update_summary()
    
    def reset_to_defaults(self) -> None:
        """Reset all sliders to default values."""
        self.set_profile(DriverProfile())
        self.profileChanged.emit(self._profile)
