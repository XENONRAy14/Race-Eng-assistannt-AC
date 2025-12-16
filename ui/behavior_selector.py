"""
Behavior Selector - UI for selecting driving behavior presets.
Displays behavior cards with descriptions and visual indicators.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QButtonGroup, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class BehaviorCard(QFrame):
    """A clickable card representing a behavior option."""
    
    clicked = Signal(str)
    
    def __init__(
        self,
        behavior_id: str,
        name: str,
        description: str,
        color: str = "#2196F3",
        parent=None
    ):
        super().__init__(parent)
        
        self.behavior_id = behavior_id
        self.color = color
        self._is_selected = False
        
        self._setup_ui(name, description)
        self._update_style()
    
    def _setup_ui(self, name: str, description: str) -> None:
        """Set up the card UI."""
        self.setFixedHeight(100)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)
        
        # Name label
        self.name_label = QLabel(name)
        self.name_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(self.name_label)
        
        # Description label
        self.desc_label = QLabel(description)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.desc_label)
        
        layout.addStretch()
    
    def _update_style(self) -> None:
        """Update card style based on selection state."""
        if self._is_selected:
            self.setStyleSheet(f"""
                BehaviorCard {{
                    background-color: {self.color}22;
                    border: 2px solid {self.color};
                    border-radius: 8px;
                }}
                BehaviorCard:hover {{
                    background-color: {self.color}33;
                }}
            """)
            self.name_label.setStyleSheet(f"color: {self.color}; font-weight: bold;")
        else:
            self.setStyleSheet(f"""
                BehaviorCard {{
                    background-color: #2a2a2a;
                    border: 1px solid #444;
                    border-radius: 8px;
                }}
                BehaviorCard:hover {{
                    background-color: #333;
                    border-color: {self.color};
                }}
            """)
            self.name_label.setStyleSheet("color: #fff; font-weight: bold;")
    
    def set_selected(self, selected: bool) -> None:
        """Set the selection state."""
        self._is_selected = selected
        self._update_style()
    
    def is_selected(self) -> bool:
        """Check if card is selected."""
        return self._is_selected
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.behavior_id)
        super().mousePressEvent(event)


class BehaviorSelector(QWidget):
    """
    Widget for selecting driving behavior.
    Displays behavior cards in a grid layout.
    """
    
    behaviorChanged = Signal(str)
    
    # Behavior definitions
    BEHAVIORS = {
        "safe": {
            "name": "Safe Touge",
            "description": "Stabilité maximale, setup prévisible et tolérant",
            "color": "#4CAF50"
        },
        "balanced": {
            "name": "Balanced Touge",
            "description": "Équilibre entre grip, rotation et stabilité",
            "color": "#2196F3"
        },
        "attack": {
            "name": "Attack Touge",
            "description": "Setup agressif pour performance maximale",
            "color": "#FF9800"
        },
        "drift": {
            "name": "Drift Touge",
            "description": "Optimisé pour le drift et les glisses contrôlées",
            "color": "#E91E63"
        }
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._selected_behavior = "balanced"
        self._cards: dict[str, BehaviorCard] = {}
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the selector UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Comportement")
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
        
        # Cards grid
        cards_layout = QGridLayout()
        cards_layout.setSpacing(10)
        
        row, col = 0, 0
        for behavior_id, data in self.BEHAVIORS.items():
            card = BehaviorCard(
                behavior_id=behavior_id,
                name=data["name"],
                description=data["description"],
                color=data["color"]
            )
            card.clicked.connect(self._on_card_clicked)
            
            self._cards[behavior_id] = card
            cards_layout.addWidget(card, row, col)
            
            col += 1
            if col > 1:
                col = 0
                row += 1
        
        layout.addLayout(cards_layout)
        
        # AI recommendation label
        self.recommendation_label = QLabel()
        self.recommendation_label.setStyleSheet("""
            color: #888;
            font-size: 11px;
            font-style: italic;
            padding: 5px;
        """)
        self.recommendation_label.setWordWrap(True)
        layout.addWidget(self.recommendation_label)
        
        layout.addStretch()
        
        # Select default
        self._update_selection("balanced")
    
    def _on_card_clicked(self, behavior_id: str) -> None:
        """Handle card click."""
        self._update_selection(behavior_id)
        self.behaviorChanged.emit(behavior_id)
    
    def _update_selection(self, behavior_id: str) -> None:
        """Update the selected behavior."""
        self._selected_behavior = behavior_id
        
        for bid, card in self._cards.items():
            card.set_selected(bid == behavior_id)
    
    def get_selected_behavior(self) -> str:
        """Get the currently selected behavior ID."""
        return self._selected_behavior
    
    def set_selected_behavior(self, behavior_id: str) -> None:
        """Set the selected behavior."""
        if behavior_id in self._cards:
            self._update_selection(behavior_id)
    
    def set_recommendation(self, behavior_id: str, confidence: float) -> None:
        """Show AI recommendation."""
        if behavior_id in self.BEHAVIORS:
            name = self.BEHAVIORS[behavior_id]["name"]
            self.recommendation_label.setText(
                f"💡 Recommandation IA: {name} (confiance: {confidence:.0%})"
            )
        else:
            self.recommendation_label.setText("")
    
    def clear_recommendation(self) -> None:
        """Clear the recommendation label."""
        self.recommendation_label.setText("")
    
    def get_behavior_info(self, behavior_id: str) -> dict:
        """Get information about a behavior."""
        return self.BEHAVIORS.get(behavior_id, {})
