"""
Driving Style Widget V2 - Professional driving analysis display.
Clean design with minimal borders and better visual hierarchy.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QPushButton
)
from PySide6.QtCore import Qt, Signal
from ai.driving_analyzer import DrivingMetrics, DrivingStyle


class StyleBadge(QFrame):
    """Badge showing detected driving style - professional minimal design."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.02);
                border: none;
                border-left: 4px solid #ff0000;
                border-radius: 0px;
                padding: 30px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Style icon and name
        self.style_label = QLabel("❓ Analyse en cours...")
        self.style_label.setAlignment(Qt.AlignCenter)
        self.style_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #ffffff;
            font-family: 'Arial', sans-serif;
        """)
        layout.addWidget(self.style_label)
        
        # Confidence label
        self.confidence_label = QLabel("Confiance: 0%")
        self.confidence_label.setAlignment(Qt.AlignCenter)
        self.confidence_label.setStyleSheet("""
            font-size: 13px;
            color: #999999;
            font-family: 'Arial', sans-serif;
            margin-top: 5px;
        """)
        layout.addWidget(self.confidence_label)
        
        self.setMinimumHeight(120)
    
    def set_style(self, style: DrivingStyle, confidence: float):
        """Update the displayed style."""
        style_info = {
            DrivingStyle.UNKNOWN: ("❓", "Analyse...", "#888888"),
            DrivingStyle.SMOOTH: ("🎯", "Fluide", "#00ff00"),
            DrivingStyle.BALANCED: ("⚖️", "Équilibré", "#ffffff"),
            DrivingStyle.AGGRESSIVE: ("🔥", "Agressif", "#ff8800"),
            DrivingStyle.DRIFT: ("💨", "Drift", "#ff0000")
        }
        
        icon, name, color = style_info.get(style, ("❓", "?", "#888"))
        
        self.style_label.setText(f"{icon} {name}")
        self.style_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {color};
            font-family: 'Arial', sans-serif;
        """)
        
        self.confidence_label.setText(f"Confiance: {int(confidence * 100)}%")


class MetricBar(QFrame):
    """Bar showing a single metric - professional minimal design."""
    
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.label_text = label
        
        self.setFrameStyle(QFrame.NoFrame)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(15)
        
        # Label
        self.label = QLabel(label)
        self.label.setFixedWidth(120)
        self.label.setStyleSheet("""
            color: #999999;
            font-family: 'Arial', sans-serif;
            font-size: 12px;
        """)
        layout.addWidget(self.label)
        
        # Progress bar
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)
        self.bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff0000, stop:1 #ff4444);
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.bar)
        
        # Value label
        self.value_label = QLabel("0%")
        self.value_label.setFixedWidth(50)
        self.value_label.setAlignment(Qt.AlignRight)
        self.value_label.setStyleSheet("""
            color: #ffffff;
            font-family: 'Consolas', monospace;
            font-size: 13px;
            font-weight: bold;
        """)
        layout.addWidget(self.value_label)
    
    def set_value(self, value: float):
        """Set metric value (0-1)."""
        percent = int(value * 100)
        self.bar.setValue(percent)
        self.value_label.setText(f"{percent}%")


class DrivingStyleWidget(QWidget):
    """Widget displaying driving style analysis - professional design."""
    
    apply_recommendation = Signal()
    
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
        
        title = QLabel("DRIVING ANALYSIS")
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
        
        # Style badge
        self.style_badge = StyleBadge()
        content_layout.addWidget(self.style_badge)
        
        # Metrics section
        metrics_title = QLabel("METRICS")
        metrics_title.setStyleSheet("""
            color: #666666;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
            margin-top: 10px;
        """)
        content_layout.addWidget(metrics_title)
        
        # Metric bars
        self.aggression_bar = MetricBar("Agressivité")
        content_layout.addWidget(self.aggression_bar)
        
        self.smoothness_bar = MetricBar("Fluidité")
        content_layout.addWidget(self.smoothness_bar)
        
        self.consistency_bar = MetricBar("Constance")
        content_layout.addWidget(self.consistency_bar)
        
        self.braking_bar = MetricBar("Freinage")
        content_layout.addWidget(self.braking_bar)
        
        self.cornering_bar = MetricBar("Virage")
        content_layout.addWidget(self.cornering_bar)
        
        # Recommendation section
        content_layout.addSpacing(15)
        
        rec_title = QLabel("RECOMMENDATION")
        rec_title.setStyleSheet("""
            color: #666666;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        content_layout.addWidget(rec_title)
        
        self.recommendation_label = QLabel("Roulez quelques tours pour obtenir une analyse...")
        self.recommendation_label.setWordWrap(True)
        self.recommendation_label.setStyleSheet("""
            color: #999999;
            font-size: 13px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.02);
            border-left: 3px solid #666666;
        """)
        content_layout.addWidget(self.recommendation_label)
        
        # Apply button
        self.apply_button = QPushButton("⚡ APPLY RECOMMENDATION")
        self.apply_button.clicked.connect(self.apply_recommendation.emit)
        self.apply_button.setEnabled(False)
        self.apply_button.setMinimumHeight(50)
        self.apply_button.setStyleSheet("""
            QPushButton {
                background: #333333;
                color: #666666;
                border: none;
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
                letter-spacing: 1px;
                margin-top: 10px;
            }
            QPushButton:enabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff0000, stop:1 #cc0000);
                color: #ffffff;
            }
            QPushButton:enabled:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff3333, stop:1 #ff0000);
            }
            QPushButton:enabled:pressed {
                background: #990000;
            }
        """)
        content_layout.addWidget(self.apply_button)
        
        content_layout.addStretch()
        
        layout.addWidget(content)
    
    def update_analysis(self, metrics: DrivingMetrics, style: DrivingStyle, confidence: float):
        """Update the displayed analysis."""
        # Update style badge
        self.style_badge.set_style(style, confidence)
        
        # Update metric bars
        self.aggression_bar.set_value(metrics.aggression)
        self.smoothness_bar.set_value(metrics.smoothness)
        self.consistency_bar.set_value(metrics.consistency)
        self.braking_bar.set_value(metrics.braking_efficiency)
        self.cornering_bar.set_value(metrics.cornering_speed)
        
        # Update recommendation
        if confidence > 0.5:
            rec_text = self._generate_recommendation(style, metrics)
            self.recommendation_label.setText(rec_text)
            self.recommendation_label.setStyleSheet("""
                color: #ffffff;
                font-size: 13px;
                padding: 15px;
                background: rgba(255, 255, 255, 0.02);
                border-left: 3px solid #ff0000;
            """)
            self.apply_button.setEnabled(True)
        else:
            self.recommendation_label.setText("Continuez à rouler pour une analyse plus précise...")
            self.recommendation_label.setStyleSheet("""
                color: #999999;
                font-size: 13px;
                padding: 15px;
                background: rgba(255, 255, 255, 0.02);
                border-left: 3px solid #666666;
            """)
            self.apply_button.setEnabled(False)
    
    def _generate_recommendation(self, style: DrivingStyle, metrics: DrivingMetrics) -> str:
        """Generate recommendation text based on style."""
        recommendations = {
            DrivingStyle.SMOOTH: "Style fluide détecté. Setup recommandé: stabilité élevée, aérodynamique équilibrée.",
            DrivingStyle.BALANCED: "Style équilibré détecté. Setup recommandé: configuration polyvalente.",
            DrivingStyle.AGGRESSIVE: "Style agressif détecté. Setup recommandé: réactivité élevée, freins puissants.",
            DrivingStyle.DRIFT: "Style drift détecté. Setup recommandé: sur-virage prononcé, différentiel ouvert."
        }
        
        return recommendations.get(style, "Analyse en cours...")
