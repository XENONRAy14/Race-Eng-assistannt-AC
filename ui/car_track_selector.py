"""
Car/Track Selector V2 - Professional minimal design.
Cleaner layout, reduced borders, better visual hierarchy.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QFrame, QCompleter
)
from PySide6.QtCore import Qt, Signal

from typing import Optional
from models.car import Car
from models.track import Track


class SearchableComboBox(QComboBox):
    """A combo box with search/filter functionality - minimal design."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        
        # Set up completer for filtering
        self.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.completer().setFilterMode(Qt.MatchContains)
        
        # Professional minimal style
        self.setStyleSheet("""
            QComboBox {
                padding: 10px 15px;
                border: 1px solid rgba(255, 0, 0, 0.3);
                border-radius: 4px;
                background-color: rgba(0, 0, 0, 0.5);
                color: #ffffff;
                min-width: 250px;
                font-size: 13px;
            }
            QComboBox:hover {
                border-color: #ff0000;
                background-color: rgba(0, 0, 0, 0.7);
            }
            QComboBox:focus {
                border-color: #ff0000;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #999999;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a1a;
                color: #ffffff;
                selection-background-color: #ff0000;
                border: 1px solid rgba(255, 0, 0, 0.3);
                outline: none;
            }
        """)


class CarTrackSelector(QWidget):
    """
    Widget for selecting car and track - professional design.
    Clean layout with minimal borders.
    """
    
    carChanged = Signal(object)  # Emits Car or None
    trackChanged = Signal(object)  # Emits Track or None
    selectionChanged = Signal(object, object)  # Emits (Car, Track)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._cars: list[Car] = []
        self._tracks: list[Track] = []
        self._selected_car: Optional[Car] = None
        self._selected_track: Optional[Track] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the selector UI."""
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
        
        title = QLabel("CAR & TRACK")
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
        
        # Car selection
        car_section = QVBoxLayout()
        car_section.setSpacing(10)
        
        car_label = QLabel("VEHICLE")
        car_label.setStyleSheet("""
            color: #666666;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        car_section.addWidget(car_label)
        
        self.car_combo = SearchableComboBox()
        self.car_combo.currentIndexChanged.connect(self._on_car_changed)
        car_section.addWidget(self.car_combo)
        
        # Car info
        self.car_info = QLabel("No car selected")
        self.car_info.setStyleSheet("""
            color: #999999;
            font-size: 12px;
            margin-top: 5px;
        """)
        self.car_info.setWordWrap(True)
        car_section.addWidget(self.car_info)
        
        content_layout.addLayout(car_section)
        
        # Track selection
        track_section = QVBoxLayout()
        track_section.setSpacing(10)
        
        track_label = QLabel("CIRCUIT")
        track_label.setStyleSheet("""
            color: #666666;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        track_section.addWidget(track_label)
        
        self.track_combo = SearchableComboBox()
        self.track_combo.currentIndexChanged.connect(self._on_track_changed)
        track_section.addWidget(self.track_combo)
        
        # Track info
        self.track_info = QLabel("No track selected")
        self.track_info.setStyleSheet("""
            color: #999999;
            font-size: 12px;
            margin-top: 5px;
        """)
        self.track_info.setWordWrap(True)
        track_section.addWidget(self.track_info)
        
        content_layout.addLayout(track_section)
        content_layout.addStretch()
        
        layout.addWidget(content)
    
    def set_cars(self, cars: list[Car]) -> None:
        """Set available cars."""
        self._cars = cars
        self.car_combo.clear()
        self.car_combo.addItem("-- Select Car --", None)
        
        for car in cars:
            self.car_combo.addItem(car.name, car)
    
    def set_tracks(self, tracks: list[Track]) -> None:
        """Set available tracks."""
        self._tracks = tracks
        self.track_combo.clear()
        self.track_combo.addItem("-- Select Track --", None)
        
        for track in tracks:
            display_name = f"{track.name}"
            if track.config and track.config != "default":
                display_name += f" ({track.config})"
            self.track_combo.addItem(display_name, track)
    
    def _on_car_changed(self, index: int) -> None:
        """Handle car selection change."""
        car = self.car_combo.itemData(index)
        
        # Only update if we got a valid car (not None from placeholder or typing)
        if car is not None:
            self._selected_car = car
            info = f"🏎️ {car.name}"
            if hasattr(car, 'power_hp') and car.power_hp:
                info += f" • {car.power_hp}hp"
            if hasattr(car, 'weight_kg') and car.weight_kg:
                info += f" • {car.weight_kg}kg"
            self.car_info.setText(info)
            self.car_info.setStyleSheet("color: #ffffff; font-size: 12px; margin-top: 5px;")
            self.carChanged.emit(car)
        elif index == 0:
            # Placeholder selected
            self._selected_car = None
            self.car_info.setText("No car selected")
            self.car_info.setStyleSheet("color: #999999; font-size: 12px; margin-top: 5px;")
            self.carChanged.emit(None)
        # If index > 0 but car is None, user is typing - don't clear selection
        
        self.selectionChanged.emit(self._selected_car, self._selected_track)
    
    def _on_track_changed(self, index: int) -> None:
        """Handle track selection change."""
        track = self.track_combo.itemData(index)
        
        # Only update if we got a valid track (not None from placeholder or typing)
        if track is not None:
            self._selected_track = track
            info = f"🏁 {track.name}"
            if track.config and track.config != "default":
                info += f" ({track.config})"
            if hasattr(track, 'length_km') and track.length_km:
                info += f" • {track.length_km:.2f}km"
            self.track_info.setText(info)
            self.track_info.setStyleSheet("color: #ffffff; font-size: 12px; margin-top: 5px;")
            self.trackChanged.emit(track)
        elif index == 0:
            # Placeholder selected
            self._selected_track = None
            self.track_info.setText("No track selected")
            self.track_info.setStyleSheet("color: #999999; font-size: 12px; margin-top: 5px;")
            self.trackChanged.emit(None)
        # If index > 0 but track is None, user is typing - don't clear selection
        
        self.selectionChanged.emit(self._selected_car, self._selected_track)
    
    def get_selected_car(self) -> Optional[Car]:
        """Get currently selected car."""
        return self._selected_car
    
    def get_selected_track(self) -> Optional[Track]:
        """Get currently selected track."""
        return self._selected_track
    
    def has_valid_selection(self) -> bool:
        """Check if both car and track are selected."""
        return self._selected_car is not None and self._selected_track is not None
    
    def select_car_by_id(self, car_id: str) -> bool:
        """Select car by ID."""
        for i in range(self.car_combo.count()):
            car = self.car_combo.itemData(i)
            if car and car.car_id == car_id:
                self.car_combo.setCurrentIndex(i)
                # Force update internal state in case signal doesn't fire
                self._selected_car = car
                print(f"[CAR_SELECTOR] Selected car: {car.name} (index {i})")
                return True
        print(f"[CAR_SELECTOR] Car not found: {car_id}")
        return False
    
    def set_selected_car(self, car_id: str) -> bool:
        """Set selected car by ID (alias for select_car_by_id)."""
        return self.select_car_by_id(car_id)
    
    def select_track_by_id(self, track_id: str, config: str = None) -> bool:
        """Select track by ID and optional config."""
        # Normalize config: treat None and "" as equivalent
        config_normalized = config if config else ""
        
        for i in range(self.track_combo.count()):
            track = self.track_combo.itemData(i)
            if track and track.track_id == track_id:
                track_config_normalized = track.config if track.config else ""
                
                # Match if config is None/empty, or if configs match
                if not config_normalized or track_config_normalized == config_normalized:
                    self.track_combo.setCurrentIndex(i)
                    # Force update internal state in case signal doesn't fire
                    self._selected_track = track
                    print(f"[TRACK_SELECTOR] Selected track: {track.name} (config='{track.config}', index {i})")
                    return True
                else:
                    print(f"[TRACK_SELECTOR] Track {track_id} found but config mismatch: '{track_config_normalized}' != '{config_normalized}'")
        
        print(f"[TRACK_SELECTOR] Track not found: {track_id} (config={config})")
        return False
    
    def set_selected_track(self, track_id: str, config: str = None) -> bool:
        """Set selected track by ID (alias for select_track_by_id)."""
        return self.select_track_by_id(track_id, config)
