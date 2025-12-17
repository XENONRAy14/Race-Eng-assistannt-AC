"""
Driving Style Widget - Displays detected driving style and recommendations.
Modern Initial D black/red gradient design.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from ai.driving_analyzer import DrivingMetrics, DrivingStyle


class StyleBadge(QFrame):
    """Badge showing detected driving style with Initial D styling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a0000, stop:1 #000000);
                border: 2px solid #ff0000;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)
        
        # Style icon and name
        self.style_label = QLabel("❓ Analyse en cours...")
        self.style_label.setAlignment(Qt.AlignCenter)
        self.style_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #888;
            font-family: 'Arial', sans-serif;
        """)
        layout.addWidget(self.style_label)
        
        # Confidence bar
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setRange(0, 100)
        self.confidence_bar.setValue(0)
        self.confidence_bar.setTextVisible(False)
        self.confidence_bar.setFixedHeight(8)
        self.confidence_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(0, 0, 0, 0.5);
                border: 1px solid #ff0000;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff0000, stop:1 #ff8800);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.confidence_bar)
        
        self.setMinimumHeight(90)
    
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
            font-size: 20px;
            font-weight: bold;
            color: {color};
            font-family: 'Arial', sans-serif;
        """)
        
        self.confidence_bar.setValue(int(confidence * 100))


class MetricBar(QFrame):
    """Bar showing a single metric with Initial D styling."""
    
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.label_text = label
        
        self.setFrameStyle(QFrame.NoFrame)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)
        
        # Label
        self.label = QLabel(label)
        self.label.setFixedWidth(120)
        self.label.setStyleSheet("""
            color: #ffffff;
            font-family: 'Arial', sans-serif;
            font-size: 14px;
            font-weight: bold;
        """)
        layout.addWidget(self.label)
        
        # Progress bar
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(24)
        self.bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(0, 0, 0, 0.5);
                border: 1px solid #ff0000;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff0000, stop:1 #ff8800);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.bar)
        
        # Value label
        self.value_label = QLabel("0%")
        self.value_label.setFixedWidth(50)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value_label.setStyleSheet("""
            color: #ffffff;
            font-family: 'Arial', sans-serif;
            font-size: 13px;
            font-weight: bold;
        """)
        layout.addWidget(self.value_label)
    
    def set_value(self, value: float):
        """Set the metric value (0.0 to 1.0)."""
        percent = int(value * 100)
        self.bar.setValue(percent)
        self.value_label.setText(f"{percent}%")


class DrivingStyleWidget(QWidget):
    """Main driving style analysis widget with Initial D design."""
    
    apply_recommendation = Signal(str)  # Emit behavior string
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._recommended_behavior = "balanced"  # Default
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🎯 Analyse de Conduite")
        title.setStyleSheet("""
            color: #ff0000;
            font-family: 'Arial', sans-serif;
            font-size: 22px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        layout.addWidget(title)
        
        # Style badge
        self.style_badge = StyleBadge()
        layout.addWidget(self.style_badge)
        
        # Metrics group
        metrics_group = QFrame()
        metrics_group.setFrameStyle(QFrame.NoFrame)
        metrics_group.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a0000, stop:1 #000000);
                border: 2px solid #ff0000;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        
        metrics_layout = QVBoxLayout(metrics_group)
        metrics_layout.setSpacing(8)
        
        # Metrics title
        metrics_title = QLabel("📊 Métriques de Conduite")
        metrics_title.setStyleSheet("""
            color: #ff0000;
            font-family: 'Arial', sans-serif;
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 1px;
            margin-bottom: 5px;
        """)
        metrics_layout.addWidget(metrics_title)
        
        # Metric bars
        self.aggression_bar = MetricBar("Agressivité")
        self.smoothness_bar = MetricBar("Fluidité")
        self.drift_bar = MetricBar("Drift")
        
        metrics_layout.addWidget(self.aggression_bar)
        metrics_layout.addWidget(self.smoothness_bar)
        metrics_layout.addWidget(self.drift_bar)
        
        layout.addWidget(metrics_group)
        
        # Recommendation section
        rec_group = QFrame()
        rec_group.setFrameStyle(QFrame.NoFrame)
        rec_group.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a0000, stop:1 #000000);
                border: 2px solid #ff0000;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        
        rec_layout = QVBoxLayout(rec_group)
        rec_layout.setSpacing(10)
        
        # Recommendation icon and text
        self.rec_icon = QLabel("💡")
        self.rec_icon.setAlignment(Qt.AlignCenter)
        self.rec_icon.setStyleSheet("font-size: 32px;")
        rec_layout.addWidget(self.rec_icon)
        
        self.rec_label = QLabel("Style fluide détecté!")
        self.rec_label.setAlignment(Qt.AlignCenter)
        self.rec_label.setWordWrap(True)
        self.rec_label.setStyleSheet("""
            color: #ffffff;
            font-family: 'Arial', sans-serif;
            font-size: 16px;
            font-weight: bold;
        """)
        rec_layout.addWidget(self.rec_label)
        
        self.rec_detail = QLabel("Je recommande le mode 'Safe' ou 'Balanced' pour maximiser ton grip et ta constance.")
        self.rec_detail.setAlignment(Qt.AlignCenter)
        self.rec_detail.setWordWrap(True)
        self.rec_detail.setStyleSheet("""
            color: #cccccc;
            font-family: 'Arial', sans-serif;
            font-size: 14px;
            line-height: 1.5;
        """)
        rec_layout.addWidget(self.rec_detail)
        
        # Apply button
        self.apply_button = QPushButton("⚡ Appliquer la recommandation")
        self.apply_button.clicked.connect(self._on_apply_clicked)
        self.apply_button.setMinimumHeight(50)
        self.apply_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff0000, stop:1 #cc0000);
                color: #ffffff;
                border: 2px solid #ff0000;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Arial', sans-serif;
                padding: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff3333, stop:1 #ff0000);
                border: 2px solid #ff3333;
            }
            QPushButton:pressed {
                background: #990000;
            }
        """)
        rec_layout.addWidget(self.apply_button)
        
        layout.addWidget(rec_group)
        layout.addStretch()
    
    def _on_apply_clicked(self):
        """Handle apply button click."""
        self.apply_recommendation.emit(self._recommended_behavior)
    
    def update_analysis(self, metrics: DrivingMetrics, style: DrivingStyle, confidence: float):
        """Update the analysis display."""
        # Update style badge
        self.style_badge.set_style(style, confidence)
        
        # Update metric bars
        self.aggression_bar.set_value(metrics.aggression)
        self.smoothness_bar.set_value(metrics.smoothness)
        self.drift_bar.set_value(metrics.drift_tendency)
        
        # Update recommendation and store behavior
        recommendations = {
            DrivingStyle.SMOOTH: (
                "🎯 Style fluide détecté!",
                "Je recommande le mode 'Safe' ou 'Balanced' pour maximiser ton grip et ta constance.",
                "safe"
            ),
            DrivingStyle.BALANCED: (
                "⚖️ Style équilibré détecté!",
                "Le mode 'Balanced' est parfait pour toi. Tu peux aussi essayer 'Attack' pour plus de performance.",
                "balanced"
            ),
            DrivingStyle.AGGRESSIVE: (
                "🔥 Style agressif détecté!",
                "Le mode 'Attack' est fait pour toi! Attention à ne pas trop abîmer les pneus.",
                "attack"
            ),
            DrivingStyle.DRIFT: (
                "💨 Style drift détecté!",
                "Le mode 'Drift' est optimal pour ton style. Profite des glissades contrôlées!",
                "drift"
            )
        }
        
        label, detail, behavior = recommendations.get(style, ("❓", "Analyse en cours...", "balanced"))
        self.rec_label.setText(label)
        self.rec_detail.setText(detail)
        self._recommended_behavior = behavior
