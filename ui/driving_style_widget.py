"""
Driving Style Widget - Displays detected driving style and recommendations.
Clean, simple interface showing analysis results.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from ai.driving_analyzer import DrivingMetrics, DrivingStyle


class StyleBadge(QFrame):
    """Badge showing detected driving style."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            StyleBadge {
                background-color: #1a1a2e;
                border: 2px solid #16213e;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)
        
        # Style icon and name
        self.style_label = QLabel("❓ Analyse en cours...")
        self.style_label.setAlignment(Qt.AlignCenter)
        self.style_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #888;
        """)
        layout.addWidget(self.style_label)
        
        # Confidence bar
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setRange(0, 100)
        self.confidence_bar.setValue(0)
        self.confidence_bar.setTextVisible(False)
        self.confidence_bar.setFixedHeight(6)
        self.confidence_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2a2a4e;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #4a69bd;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.confidence_bar)
        
        self.setMinimumHeight(70)
    
    def set_style(self, style: DrivingStyle, confidence: float):
        """Update the displayed style."""
        style_info = {
            DrivingStyle.UNKNOWN: ("❓", "Analyse...", "#888888"),
            DrivingStyle.SMOOTH: ("🎯", "Fluide", "#4CAF50"),
            DrivingStyle.BALANCED: ("⚖️", "Équilibré", "#2196F3"),
            DrivingStyle.AGGRESSIVE: ("🔥", "Agressif", "#FF9800"),
            DrivingStyle.DRIFT: ("💨", "Drift", "#E91E63")
        }
        
        icon, name, color = style_info.get(style, ("❓", "?", "#888"))
        
        self.style_label.setText(f"{icon} {name}")
        self.style_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {color};
        """)
        
        self.confidence_bar.setValue(int(confidence * 100))
        self.confidence_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #2a2a4e;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
        
        self.setStyleSheet(f"""
            StyleBadge {{
                background-color: #1a1a2e;
                border: 2px solid {color}44;
                border-radius: 10px;
            }}
        """)


class MetricBar(QFrame):
    """A single metric display bar."""
    
    def __init__(self, name: str, color: str = "#4a69bd", parent=None):
        super().__init__(parent)
        
        self.color = color
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)
        
        # Name
        self.name_label = QLabel(name)
        self.name_label.setFixedWidth(80)
        self.name_label.setStyleSheet("color: #aaa; font-size: 11px;")
        layout.addWidget(self.name_label)
        
        # Bar
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(50)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)
        self.bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #2a2a4e;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self.bar)
        
        # Value
        self.value_label = QLabel("50%")
        self.value_label.setFixedWidth(35)
        self.value_label.setAlignment(Qt.AlignRight)
        self.value_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        layout.addWidget(self.value_label)
    
    def set_value(self, value: float):
        """Set value (0-1 range)."""
        pct = int(value * 100)
        self.bar.setValue(pct)
        self.value_label.setText(f"{pct}%")


class DrivingStyleWidget(QFrame):
    """
    Widget displaying driving style analysis.
    Shows detected style, metrics, and recommendations.
    """
    
    apply_recommendation = Signal(str)  # Emits recommended behavior
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            DrivingStyleWidget {
                background-color: #0f0f1a;
                border: 1px solid #16213e;
                border-radius: 12px;
            }
        """)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QLabel("🧠 Analyse de Conduite")
        header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #fff;
        """)
        layout.addWidget(header)
        
        # Style badge
        self.style_badge = StyleBadge()
        layout.addWidget(self.style_badge)
        
        # Metrics section
        metrics_label = QLabel("Métriques")
        metrics_label.setStyleSheet("color: #888; font-size: 11px; margin-top: 5px;")
        layout.addWidget(metrics_label)
        
        # Metric bars
        self.aggression_bar = MetricBar("Agressivité", "#FF9800")
        self.smoothness_bar = MetricBar("Fluidité", "#4CAF50")
        self.drift_bar = MetricBar("Drift", "#E91E63")
        
        layout.addWidget(self.aggression_bar)
        layout.addWidget(self.smoothness_bar)
        layout.addWidget(self.drift_bar)
        
        # Recommendation
        self.recommendation_label = QLabel("Continue à rouler pour l'analyse...")
        self.recommendation_label.setWordWrap(True)
        self.recommendation_label.setStyleSheet("""
            color: #aaa;
            font-size: 11px;
            padding: 10px;
            background-color: #1a1a2e;
            border-radius: 6px;
            margin-top: 5px;
        """)
        layout.addWidget(self.recommendation_label)
        
        # Apply button
        self.apply_btn = QPushButton("✨ Appliquer la recommandation")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a69bd;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #6a89dd;
            }
            QPushButton:pressed {
                background-color: #3a59ad;
            }
            QPushButton:disabled {
                background-color: #333;
                color: #666;
            }
        """)
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._on_apply_clicked)
        layout.addWidget(self.apply_btn)
        
        layout.addStretch()
        
        self._current_style = DrivingStyle.UNKNOWN
    
    def update_metrics(self, metrics: DrivingMetrics):
        """Update display with new metrics."""
        # Update style badge
        self.style_badge.set_style(metrics.style, metrics.confidence)
        
        # Update metric bars
        self.aggression_bar.set_value(metrics.aggression_score)
        self.smoothness_bar.set_value(metrics.smoothness_score)
        self.drift_bar.set_value(metrics.drift_score)
        
        # Update recommendation
        recommendation = self._get_recommendation(metrics.style)
        self.recommendation_label.setText(recommendation)
        
        # Enable apply button if we have a clear style
        self._current_style = metrics.style
        self.apply_btn.setEnabled(metrics.style != DrivingStyle.UNKNOWN)
    
    def _get_recommendation(self, style: DrivingStyle) -> str:
        """Get recommendation text for style."""
        recommendations = {
            DrivingStyle.UNKNOWN: "🔄 Continue à rouler pour que j'analyse ton style de conduite...",
            DrivingStyle.SMOOTH: "🎯 Style fluide détecté!\n\nJe recommande le mode 'Safe' ou 'Balanced' pour maximiser ton grip et ta constance.",
            DrivingStyle.BALANCED: "⚖️ Style équilibré détecté!\n\nLe mode 'Balanced' est parfait pour toi - bon compromis grip/réactivité.",
            DrivingStyle.AGGRESSIVE: "🔥 Style agressif détecté!\n\nLe mode 'Attack' avec suspension ferme te donnera la réactivité que tu cherches.",
            DrivingStyle.DRIFT: "💨 Style drift détecté!\n\nLe mode 'Drift' avec diff serré et arrière glissant est fait pour toi!"
        }
        return recommendations.get(style, "")
    
    def _on_apply_clicked(self):
        """Apply the recommended behavior."""
        style_to_behavior = {
            DrivingStyle.SMOOTH: "safe",
            DrivingStyle.BALANCED: "balanced",
            DrivingStyle.AGGRESSIVE: "attack",
            DrivingStyle.DRIFT: "drift"
        }
        
        behavior = style_to_behavior.get(self._current_style, "balanced")
        self.apply_recommendation.emit(behavior)
    
    def reset(self):
        """Reset the display."""
        self.style_badge.set_style(DrivingStyle.UNKNOWN, 0.0)
        self.aggression_bar.set_value(0.5)
        self.smoothness_bar.set_value(0.5)
        self.drift_bar.set_value(0.0)
        self.recommendation_label.setText("🔄 Continue à rouler pour l'analyse...")
        self.apply_btn.setEnabled(False)
        self._current_style = DrivingStyle.UNKNOWN
