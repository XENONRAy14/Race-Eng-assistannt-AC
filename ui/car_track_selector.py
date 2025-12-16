"""
Car/Track Selector - UI for selecting car and track.
Provides searchable dropdowns for car and track selection.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QGroupBox, QFrame,
    QPushButton, QCompleter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem

from typing import Optional
from models.car import Car
from models.track import Track


class SearchableComboBox(QComboBox):
    """A combo box with search/filter functionality."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        
        # Set up completer for filtering
        self.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.completer().setFilterMode(Qt.MatchContains)
        
        # Style
        self.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #444;
                border-radius: 4px;
                background-color: #2a2a2a;
                color: #fff;
                min-width: 200px;
            }
            QComboBox:hover {
                border-color: #2196F3;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox QAbstractItemView {
                background-color: #2a2a2a;
                color: #fff;
                selection-background-color: #2196F3;
            }
        """)


class CarTrackSelector(QWidget):
    """
    Widget for selecting car and track.
    Provides searchable dropdowns and displays selection info.
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
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Sélection Voiture / Piste")
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
        
        # Car selection group
        car_group = QGroupBox("Voiture")
        car_group.setStyleSheet("""
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
        car_layout = QVBoxLayout(car_group)
        
        self.car_combo = SearchableComboBox()
        self.car_combo.setPlaceholderText("Rechercher une voiture...")
        self.car_combo.currentIndexChanged.connect(self._on_car_changed)
        car_layout.addWidget(self.car_combo)
        
        # Car info label
        self.car_info_label = QLabel()
        self.car_info_label.setStyleSheet("color: #888; font-size: 11px;")
        self.car_info_label.setWordWrap(True)
        car_layout.addWidget(self.car_info_label)
        
        layout.addWidget(car_group)
        
        # Track selection group
        track_group = QGroupBox("Piste")
        track_group.setStyleSheet("""
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
        track_layout = QVBoxLayout(track_group)
        
        self.track_combo = SearchableComboBox()
        self.track_combo.setPlaceholderText("Rechercher une piste...")
        self.track_combo.currentIndexChanged.connect(self._on_track_changed)
        track_layout.addWidget(self.track_combo)
        
        # Track info label
        self.track_info_label = QLabel()
        self.track_info_label.setStyleSheet("color: #888; font-size: 11px;")
        self.track_info_label.setWordWrap(True)
        track_layout.addWidget(self.track_info_label)
        
        layout.addWidget(track_group)
        
        # Filter buttons
        filter_layout = QHBoxLayout()
        
        self.touge_filter_btn = QPushButton("🏔️ Touge uniquement")
        self.touge_filter_btn.setCheckable(True)
        self.touge_filter_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                border: 1px solid #444;
                border-radius: 4px;
                background-color: #2a2a2a;
                color: #888;
            }
            QPushButton:checked {
                background-color: #4CAF50;
                color: #fff;
                border-color: #4CAF50;
            }
            QPushButton:hover {
                border-color: #4CAF50;
            }
        """)
        self.touge_filter_btn.clicked.connect(self._apply_track_filter)
        filter_layout.addWidget(self.touge_filter_btn)
        
        self.rwd_filter_btn = QPushButton("🚗 RWD uniquement")
        self.rwd_filter_btn.setCheckable(True)
        self.rwd_filter_btn.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                border: 1px solid #444;
                border-radius: 4px;
                background-color: #2a2a2a;
                color: #888;
            }
            QPushButton:checked {
                background-color: #2196F3;
                color: #fff;
                border-color: #2196F3;
            }
            QPushButton:hover {
                border-color: #2196F3;
            }
        """)
        self.rwd_filter_btn.clicked.connect(self._apply_car_filter)
        filter_layout.addWidget(self.rwd_filter_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                border: 1px solid #444;
                border-radius: 4px;
                background-color: #2a2a2a;
                color: #fff;
            }
            QPushButton:hover {
                background-color: #333;
                border-color: #2196F3;
            }
        """)
        refresh_btn.clicked.connect(self._on_refresh_clicked)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
    
    def _on_car_changed(self, index: int) -> None:
        """Handle car selection change."""
        if index < 0 or index >= len(self._filtered_cars):
            self._selected_car = None
            self.car_info_label.setText("")
        else:
            self._selected_car = self._filtered_cars[index]
            self._update_car_info()
        
        self.carChanged.emit(self._selected_car)
        self.selectionChanged.emit(self._selected_car, self._selected_track)
    
    def _on_track_changed(self, index: int) -> None:
        """Handle track selection change."""
        if index < 0 or index >= len(self._filtered_tracks):
            self._selected_track = None
            self.track_info_label.setText("")
        else:
            self._selected_track = self._filtered_tracks[index]
            self._update_track_info()
        
        self.trackChanged.emit(self._selected_track)
        self.selectionChanged.emit(self._selected_car, self._selected_track)
    
    def _update_car_info(self) -> None:
        """Update car info label."""
        if not self._selected_car:
            self.car_info_label.setText("")
            return
        
        car = self._selected_car
        info_parts = []
        
        if car.brand:
            info_parts.append(car.brand)
        if car.drivetrain:
            info_parts.append(car.drivetrain)
        if car.power_hp > 0:
            info_parts.append(f"{car.power_hp} HP")
        if car.weight_kg > 0:
            info_parts.append(f"{car.weight_kg} kg")
        
        self.car_info_label.setText(" | ".join(info_parts))
    
    def _update_track_info(self) -> None:
        """Update track info label."""
        if not self._selected_track:
            self.track_info_label.setText("")
            return
        
        track = self._selected_track
        info_parts = []
        
        if track.track_type:
            info_parts.append(track.track_type.title())
        if track.length_m > 0:
            if track.length_m >= 1000:
                info_parts.append(f"{track.length_m / 1000:.1f} km")
            else:
                info_parts.append(f"{track.length_m} m")
        if track.config:
            info_parts.append(f"Layout: {track.config}")
        
        self.track_info_label.setText(" | ".join(info_parts))
    
    def _apply_car_filter(self) -> None:
        """Apply car filter and refresh list."""
        self._populate_cars()
    
    def _apply_track_filter(self) -> None:
        """Apply track filter and refresh list."""
        self._populate_tracks()
    
    def _on_refresh_clicked(self) -> None:
        """Handle refresh button click."""
        # This will be connected to the main window to refresh from AC
        pass
    
    def set_cars(self, cars: list[Car]) -> None:
        """Set the list of available cars."""
        self._cars = cars
        self._populate_cars()
    
    def set_tracks(self, tracks: list[Track]) -> None:
        """Set the list of available tracks."""
        self._tracks = tracks
        self._populate_tracks()
    
    def _populate_cars(self) -> None:
        """Populate the car combo box."""
        self.car_combo.blockSignals(True)
        self.car_combo.clear()
        
        # Apply filter
        if self.rwd_filter_btn.isChecked():
            self._filtered_cars = [c for c in self._cars if c.drivetrain == "RWD"]
        else:
            self._filtered_cars = self._cars.copy()
        
        # Sort by name
        self._filtered_cars.sort(key=lambda c: c.name)
        
        for car in self._filtered_cars:
            display_name = car.name
            if car.brand:
                display_name = f"{car.brand} {car.name}"
            self.car_combo.addItem(display_name)
        
        self.car_combo.setCurrentIndex(-1)
        self.car_combo.blockSignals(False)
        
        self._selected_car = None
        self.car_info_label.setText(f"{len(self._filtered_cars)} voitures disponibles")
    
    def _populate_tracks(self) -> None:
        """Populate the track combo box."""
        self.track_combo.blockSignals(True)
        self.track_combo.clear()
        
        # Apply filter
        if self.touge_filter_btn.isChecked():
            self._filtered_tracks = [t for t in self._tracks if t.track_type == "touge"]
        else:
            self._filtered_tracks = self._tracks.copy()
        
        # Sort by name
        self._filtered_tracks.sort(key=lambda t: t.name)
        
        for track in self._filtered_tracks:
            display_name = track.name
            if track.config:
                display_name = f"{track.name} ({track.config})"
            self.track_combo.addItem(display_name)
        
        self.track_combo.setCurrentIndex(-1)
        self.track_combo.blockSignals(False)
        
        self._selected_track = None
        self.track_info_label.setText(f"{len(self._filtered_tracks)} pistes disponibles")
    
    def get_selected_car(self) -> Optional[Car]:
        """Get the currently selected car."""
        return self._selected_car
    
    def get_selected_track(self) -> Optional[Track]:
        """Get the currently selected track."""
        return self._selected_track
    
    def set_selected_car(self, car_id: str) -> None:
        """Set the selected car by ID."""
        for i, car in enumerate(self._filtered_cars):
            if car.car_id == car_id:
                self.car_combo.setCurrentIndex(i)
                return
    
    def set_selected_track(self, track_id: str, config: str = "") -> None:
        """Set the selected track by ID."""
        full_id = f"{track_id}/{config}" if config else track_id
        for i, track in enumerate(self._filtered_tracks):
            if track.full_id == full_id or track.track_id == track_id:
                self.track_combo.setCurrentIndex(i)
                return
    
    def has_valid_selection(self) -> bool:
        """Check if both car and track are selected."""
        return self._selected_car is not None and self._selected_track is not None
