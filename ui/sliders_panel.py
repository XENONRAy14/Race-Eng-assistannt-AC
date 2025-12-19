"""
Sliders Panel V2 - Professional driver preference sliders.
Cleaner design, reduced borders, better visual hierarchy.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSlider, QFrame, QPushButton
)
from PySide6.QtCore import Qt, Signal

from models.driver_profile import DriverProfile


class LabeledSlider(QWidget):
    """A slider with left/right labels - professional minimal design."""
    
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
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(8)
        
        # Labels row
        labels_layout = QHBoxLayout()
        labels_layout.setSpacing(15)
        
        self.left_label = QLabel(self.label_left_text)
        self.left_label.setStyleSheet("""
            color: #999999;
            font-size: 12px;
            font-weight: normal;
        """)
        
        self.value_label = QLabel(f"{initial_value:.0f}%")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("""
            color: #ffffff;
            font-size: 13px;
            font-weight: bold;
            font-family: 'Consolas', monospace;
        """)
        
        self.right_label = QLabel(self.label_right_text)
        self.right_label.setAlignment(Qt.AlignRight)
        self.right_label.setStyleSheet("""
            color: #999999;
            font-size: 12px;
            font-weight: normal;
        """)
        
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
        self.slider.setTickPosition(QSlider.NoTicks)
        
        if tooltip:
            self.slider.setToolTip(tooltip)
        
        self.slider.valueChanged.connect(self._on_value_changed)
        
        # Professional minimal slider style
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 0.08);
                height: 4px;
                border-radius: 2px;
                border: none;
            }
            QSlider::handle:horizontal {
                background: #ff0000;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
                border: none;
            }
            QSlider::handle:horizontal:hover {
                background: #ff3333;
            }
            QSlider::handle:horizontal:pressed {
                background: #cc0000;
            }
        """)
        
        layout.addWidget(self.slider)
    
    def _on_value_changed(self, value: int) -> None:
        """Handle slider value change."""
        self.value_label.setText(f"{value}%")
        self.valueChanged.emit(float(value))
    
    def get_value(self) -> float:
        """Get current slider value."""
        return float(self.slider.value())
    
    def set_value(self, value: float) -> None:
        """Set slider value."""
        self.slider.setValue(int(value))


class SlidersPanel(QWidget):
    """Panel containing all driver preference sliders - professional design."""
    
    preferences_changed = Signal(dict)
    profileChanged = Signal()  # For compatibility with main_window
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
        # Mode toggle
        self._expert_mode = False
    
    def _setup_ui(self) -> None:
        """Set up the sliders panel UI."""
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
        
        title = QLabel("DRIVING STYLE")
        title.setStyleSheet("""
            color: #ff0000;
            font-family: 'Arial', sans-serif;
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Mode toggle button
        self.mode_button = QPushButton("EXPERT MODE")
        self.mode_button.setCheckable(True)
        self.mode_button.clicked.connect(self._toggle_mode)
        self.mode_button.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                color: #999999;
                border: 1px solid rgba(255, 0, 0, 0.2);
                border-radius: 4px;
                padding: 6px 15px;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:checked {
                background: rgba(255, 0, 0, 0.2);
                color: #ff0000;
                border-color: #ff0000;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.08);
            }
        """)
        header_layout.addWidget(self.mode_button)
        
        layout.addWidget(header)
        
        # Content area
        content = QWidget()
        content.setStyleSheet("background: #0a0a0a;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setSpacing(25)
        
        # Basic sliders (always visible)
        basic_section = self._create_section("BASIC PREFERENCES")
        
        self.aggression_slider = LabeledSlider(
            "Confort", "Agressif",
            50.0,
            "🎯 AGRESSIVITÉ\n\nConfort (←): Setup doux, suspension souple, conduite facile\nAgressif (→): Setup nerveux, suspension rigide, performance maximale\n\nInfluence: Rigidité suspension, amortisseurs, barres anti-roulis"
        )
        self.aggression_slider.valueChanged.connect(self._on_preferences_changed)
        basic_section.addWidget(self.aggression_slider)
        
        self.stability_slider = LabeledSlider(
            "Nerveux", "Stable",
            50.0,
            "⚖️ STABILITÉ\n\nNerveux (←): Voiture réactive, changements de direction rapides\nStable (→): Voiture prévisible, facile à contrôler en ligne droite\n\nInfluence: Géométrie suspension, toe, camber, hauteur de caisse"
        )
        self.stability_slider.valueChanged.connect(self._on_preferences_changed)
        basic_section.addWidget(self.stability_slider)
        
        self.downforce_slider = LabeledSlider(
            "Vitesse max", "Appui",
            50.0,
            "🏎️ AÉRODYNAMIQUE\n\nVitesse max (←): Moins d'appui, vitesse de pointe élevée, moins de grip en virage\nAppui (→): Plus d'appui, meilleure tenue de route, vitesse de pointe réduite\n\nInfluence: Aileron avant/arrière, rake (inclinaison voiture)"
        )
        self.downforce_slider.valueChanged.connect(self._on_preferences_changed)
        basic_section.addWidget(self.downforce_slider)
        
        content_layout.addLayout(basic_section)
        
        # Advanced sliders (expert mode only)
        self.advanced_container = QWidget()
        advanced_layout = QVBoxLayout(self.advanced_container)
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        advanced_layout.setSpacing(25)
        
        advanced_section = self._create_section("ADVANCED TUNING")
        
        self.oversteer_slider = LabeledSlider(
            "Sous-virage", "Sur-virage",
            50.0,
            "🔄 COMPORTEMENT EN VIRAGE\n\nSous-virage (←): L'avant glisse, la voiture ne tourne pas assez\nÉquilibré (50%): Comportement neutre, idéal pour la plupart des circuits\nSur-virage (→): L'arrière glisse, la voiture tourne trop (drift)\n\nInfluence: Répartition des masses, pression pneus, différentiel"
        )
        self.oversteer_slider.valueChanged.connect(self._on_preferences_changed)
        advanced_section.addWidget(self.oversteer_slider)
        
        self.brake_bias_slider = LabeledSlider(
            "Arrière", "Avant",
            50.0,
            "🛑 RÉPARTITION FREINAGE\n\nArrière (←): Plus de freinage à l'arrière, risque de sur-virage au freinage\nÉquilibré (50%): Freinage équilibré, bon compromis\nAvant (→): Plus de freinage à l'avant, risque de sous-virage, plus stable\n\nInfluence: Balance de frein (brake bias), pression maître-cylindre"
        )
        self.brake_bias_slider.valueChanged.connect(self._on_preferences_changed)
        advanced_section.addWidget(self.brake_bias_slider)
        
        self.diff_aggression_slider = LabeledSlider(
            "Ouvert", "Fermé",
            50.0,
            "⚙️ DIFFÉRENTIEL\n\nOuvert (←): Roues indépendantes, bon en entrée de virage, risque de perte de traction\nÉquilibré (50%): Compromis polyvalent\nFermé (→): Roues liées, meilleure traction en sortie, sous-virage possible\n\nInfluence: Preload, power lock, coast lock du différentiel"
        )
        self.diff_aggression_slider.valueChanged.connect(self._on_preferences_changed)
        advanced_section.addWidget(self.diff_aggression_slider)
        
        advanced_layout.addLayout(advanced_section)
        self.advanced_container.hide()
        
        content_layout.addWidget(self.advanced_container)
        content_layout.addStretch()
        
        layout.addWidget(content)
    
    def _create_section(self, title: str) -> QVBoxLayout:
        """Create a section with title."""
        section = QVBoxLayout()
        section.setSpacing(15)
        
        section_title = QLabel(title)
        section_title.setStyleSheet("""
            color: #666666;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
            margin-bottom: 5px;
        """)
        section.addWidget(section_title)
        
        return section
    
    def _toggle_mode(self, checked: bool):
        """Toggle between simple and expert mode."""
        self._expert_mode = checked
        self.advanced_container.setVisible(checked)
        
        if checked:
            self.mode_button.setText("SIMPLE MODE")
        else:
            self.mode_button.setText("EXPERT MODE")
    
    def _on_preferences_changed(self, value: float) -> None:
        """Handle preference change."""
        prefs = self.get_preferences()
        self.preferences_changed.emit(prefs)
        self.profileChanged.emit()  # For compatibility
    
    def get_preferences(self) -> dict:
        """Get current preference values."""
        prefs = {
            "aggression": self.aggression_slider.get_value(),
            "stability": self.stability_slider.get_value(),
            "downforce": self.downforce_slider.get_value(),
        }
        
        if self._expert_mode:
            prefs.update({
                "oversteer_tendency": self.oversteer_slider.get_value(),
                "brake_bias": self.brake_bias_slider.get_value(),
                "diff_aggression": self.diff_aggression_slider.get_value(),
            })
        
        return prefs
    
    def set_preferences(self, prefs: dict) -> None:
        """Set preference values."""
        if "aggression" in prefs:
            self.aggression_slider.set_value(prefs["aggression"])
        if "stability" in prefs:
            self.stability_slider.set_value(prefs["stability"])
        if "downforce" in prefs:
            self.downforce_slider.set_value(prefs["downforce"])
        if "oversteer_tendency" in prefs:
            self.oversteer_slider.set_value(prefs["oversteer_tendency"])
        if "brake_bias" in prefs:
            self.brake_bias_slider.set_value(prefs["brake_bias"])
        if "diff_aggression" in prefs:
            self.diff_aggression_slider.set_value(prefs["diff_aggression"])
    
    def set_profile(self, profile: DriverProfile) -> None:
        """Set sliders from driver profile."""
        # Map DriverProfile attributes to slider values
        # DriverProfile uses different attribute names, so we'll use safe defaults
        self.aggression_slider.set_value(profile.safety_aggression if hasattr(profile, 'safety_aggression') else 50.0)
        self.stability_slider.set_value(profile.stability_rotation if hasattr(profile, 'stability_rotation') else 50.0)
        self.downforce_slider.set_value(profile.comfort_performance if hasattr(profile, 'comfort_performance') else 50.0)
        
        # Advanced sliders
        if hasattr(profile, 'grip_slide'):
            self.oversteer_slider.set_value(profile.grip_slide)
        if hasattr(profile, 'drift_grip'):
            self.brake_bias_slider.set_value(100 - profile.drift_grip)  # Invert for brake bias
        self.diff_aggression_slider.set_value(50.0)  # Default
    
    def load_from_profile(self, profile: DriverProfile) -> None:
        """Load preferences from driver profile (alias for set_profile)."""
        self.set_profile(profile)
    
    def apply_to_profile(self, profile: DriverProfile) -> None:
        """Apply current preferences to driver profile."""
        profile.aggression = self.aggression_slider.get_value() / 100.0
        profile.stability = self.stability_slider.get_value() / 100.0
        profile.downforce_preference = self.downforce_slider.get_value() / 100.0
        profile.oversteer_tendency = self.oversteer_slider.get_value() / 100.0
        profile.brake_bias = self.brake_bias_slider.get_value() / 100.0
        profile.diff_aggression = self.diff_aggression_slider.get_value() / 100.0
