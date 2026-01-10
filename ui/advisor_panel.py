"""
Race Engineer Advisor Panel
Displays real-time driving advice based on car, track, and setup.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from typing import List, Optional
from core.race_engineer_advisor import RaceEngineerAdvisor, Advice, AdviceType
from models.car import Car
from models.track import Track
from models.setup import Setup


class AdviceCard(QFrame):
    """A single advice card widget."""
    
    def __init__(self, advice: Advice, parent=None):
        super().__init__(parent)
        self.advice = advice
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the card UI."""
        # Card styling based on advice type
        colors = {
            AdviceType.STRENGTH: ("#1a3d1a", "#4CAF50"),    # Green
            AdviceType.WARNING: ("#3d1a1a", "#f44336"),     # Red
            AdviceType.STRATEGY: ("#1a2d3d", "#2196F3"),    # Blue
            AdviceType.SETUP: ("#3d2d1a", "#FF9800"),       # Orange
            AdviceType.OVERTAKE: ("#2d1a3d", "#9C27B0"),    # Purple
        }
        
        bg_color, accent_color = colors.get(self.advice.type, ("#2d2d2d", "#888888"))
        
        self.setStyleSheet(f"""
            AdviceCard {{
                background-color: {bg_color};
                border-left: 3px solid {accent_color};
                border-radius: 4px;
                padding: 8px;
                margin: 2px 0px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)
        
        # Header with icon and title
        header = QHBoxLayout()
        header.setSpacing(6)
        
        icon_label = QLabel(self.advice.icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 14))
        icon_label.setFixedWidth(24)
        header.addWidget(icon_label)
        
        title_label = QLabel(self.advice.title)
        title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        title_label.setStyleSheet(f"color: {accent_color};")
        title_label.setWordWrap(True)
        header.addWidget(title_label, 1)
        
        layout.addLayout(header)
        
        # Description
        desc_label = QLabel(self.advice.description)
        desc_label.setFont(QFont("Segoe UI", 9))
        desc_label.setStyleSheet("color: #cccccc;")
        desc_label.setWordWrap(True)
        desc_label.setTextFormat(Qt.PlainText)
        layout.addWidget(desc_label)


class AdvisorPanel(QWidget):
    """
    Main advisor panel widget.
    Displays driving advice based on current car, track, and setup.
    """
    
    # Signal emitted when advice is updated
    adviceUpdated = Signal(int)  # Number of advice items
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.advisor = RaceEngineerAdvisor()
        self._current_car: Optional[Car] = None
        self._current_track: Optional[Track] = None
        self._current_setup: Optional[Setup] = None
        self._advice_cards: List[AdviceCard] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the panel UI."""
        self.setMinimumWidth(280)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-bottom: 1px solid #333;
                padding: 8px;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        
        title = QLabel("🎯 RACE ENGINEER")
        title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title.setStyleSheet("color: #ff4444;")
        header_layout.addWidget(title)
        
        self.advice_count = QLabel("0 conseils")
        self.advice_count.setFont(QFont("Segoe UI", 9))
        self.advice_count.setStyleSheet("color: #888;")
        header_layout.addWidget(self.advice_count, 0, Qt.AlignRight)
        
        main_layout.addWidget(header)
        
        # Scroll area for advice cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #0d0d0d;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #444;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #555;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Container for advice cards
        self.advice_container = QWidget()
        self.advice_container.setStyleSheet("background-color: #0d0d0d;")
        self.advice_layout = QVBoxLayout(self.advice_container)
        self.advice_layout.setContentsMargins(8, 8, 8, 8)
        self.advice_layout.setSpacing(6)
        self.advice_layout.addStretch()
        
        scroll.setWidget(self.advice_container)
        main_layout.addWidget(scroll, 1)
        
        # Footer with status
        footer = QFrame()
        footer.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-top: 1px solid #333;
            }
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(12, 6, 12, 6)
        
        self.status_label = QLabel("En attente de sélection...")
        self.status_label.setFont(QFont("Segoe UI", 8))
        self.status_label.setStyleSheet("color: #666;")
        footer_layout.addWidget(self.status_label)
        
        main_layout.addWidget(footer)
        
        # Show placeholder
        self._show_placeholder()
    
    def _show_placeholder(self):
        """Show placeholder when no car/track selected."""
        self._clear_advice()
        
        placeholder = QLabel(
            "Sélectionne une voiture et un circuit\n"
            "pour recevoir des conseils personnalisés."
        )
        placeholder.setFont(QFont("Segoe UI", 9))
        placeholder.setStyleSheet("color: #666;")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setWordWrap(True)
        placeholder.setContentsMargins(20, 40, 20, 40)
        
        self.advice_layout.insertWidget(0, placeholder)
        self._advice_cards.append(placeholder)
    
    def _clear_advice(self):
        """Clear all advice cards."""
        for card in self._advice_cards:
            self.advice_layout.removeWidget(card)
            card.deleteLater()
        self._advice_cards.clear()
    
    def update_advice(
        self,
        car: Optional[Car] = None,
        track: Optional[Track] = None,
        setup: Optional[Setup] = None
    ):
        """
        Update advice based on new car, track, or setup.
        Call this when any of these change.
        """
        print(f"[ADVISOR_PANEL] update_advice called: car={car.car_id if car else None}, track={track.track_id if track else None}")
        
        # Update stored values
        if car is not None:
            self._current_car = car
        if track is not None:
            self._current_track = track
        if setup is not None:
            self._current_setup = setup
        
        print(f"[ADVISOR_PANEL] Current state: car={self._current_car.car_id if self._current_car else None}, track={self._current_track.track_id if self._current_track else None}")
        
        # Need at least car to generate advice
        if self._current_car is None:
            print("[ADVISOR_PANEL] No car, showing placeholder")
            self._show_placeholder()
            self.advice_count.setText("0 conseils")
            self.status_label.setText("En attente de sélection...")
            return
        
        # Generate advice
        print(f"[ADVISOR_PANEL] Generating advice...")
        advice_list = self.advisor.generate_advice(
            car=self._current_car,
            track=self._current_track,
            setup=self._current_setup
        )
        print(f"[ADVISOR_PANEL] Generated {len(advice_list)} advice items")
        
        # Clear and rebuild
        self._clear_advice()
        
        if not advice_list:
            self._show_placeholder()
            self.advice_count.setText("0 conseils")
            return
        
        # Add advice cards
        for advice in advice_list[:10]:  # Limit to 10 items
            card = AdviceCard(advice)
            self.advice_layout.insertWidget(len(self._advice_cards), card)
            self._advice_cards.append(card)
        
        # Update counts
        self.advice_count.setText(f"{len(advice_list)} conseils")
        
        # Update status
        car_name = self._current_car.name if self._current_car else "?"
        track_name = self._current_track.name if self._current_track else "?"
        setup_status = "✓ Setup" if self._current_setup else ""
        self.status_label.setText(f"{car_name} @ {track_name} {setup_status}")
        
        # Emit signal
        self.adviceUpdated.emit(len(advice_list))
    
    def set_car(self, car: Car):
        """Set current car and update advice."""
        self.update_advice(car=car)
    
    def set_track(self, track: Track):
        """Set current track and update advice."""
        self.update_advice(track=track)
    
    def set_setup(self, setup: Setup):
        """Set current setup and update advice."""
        self.update_advice(setup=setup)
    
    def refresh(self):
        """Force refresh of advice."""
        self.update_advice()
