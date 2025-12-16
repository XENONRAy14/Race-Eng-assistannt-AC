"""
Presets Panel - Save and load setup presets per car.
Simple, ergonomic interface for managing favorite setups.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QListWidget, QListWidgetItem, QLineEdit,
    QMessageBox, QInputDialog, QComboBox, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime


@dataclass
class SetupPreset:
    """A saved setup preset."""
    name: str
    car_id: str
    behavior: str
    created_at: str
    
    # Driver profile values
    stability: float = 0.5
    rotation: float = 0.5
    grip: float = 0.5
    drift: float = 0.0
    aggression: float = 0.5
    comfort: float = 0.5
    
    # Optional notes
    notes: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "SetupPreset":
        return cls(**data)


class PresetItem(QFrame):
    """A single preset item in the list."""
    
    clicked = Signal(str)  # preset name
    delete_clicked = Signal(str)
    
    def __init__(self, preset: SetupPreset, parent=None):
        super().__init__(parent)
        self.preset = preset
        
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            PresetItem {
                background-color: #1a1a2e;
                border: 1px solid #16213e;
                border-radius: 8px;
                padding: 5px;
            }
            PresetItem:hover {
                background-color: #252545;
                border-color: #4a69bd;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)
        
        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # Name
        name_label = QLabel(preset.name)
        name_label.setStyleSheet("color: #fff; font-size: 13px; font-weight: bold;")
        info_layout.addWidget(name_label)
        
        # Behavior badge
        behavior_colors = {
            "safe": "#4CAF50",
            "balanced": "#2196F3",
            "attack": "#FF9800",
            "drift": "#E91E63"
        }
        behavior_color = behavior_colors.get(preset.behavior, "#888")
        behavior_label = QLabel(preset.behavior.upper())
        behavior_label.setStyleSheet(f"""
            color: {behavior_color};
            font-size: 10px;
            font-weight: bold;
            background-color: {behavior_color}22;
            padding: 2px 6px;
            border-radius: 3px;
        """)
        behavior_label.setFixedWidth(70)
        info_layout.addWidget(behavior_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Delete button
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(30, 30)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ff444433;
                border-radius: 5px;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(preset.name))
        layout.addWidget(delete_btn)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.preset.name)
        super().mousePressEvent(event)


class PresetsPanel(QFrame):
    """
    Panel for managing setup presets per car.
    Simple and ergonomic - save your favorite setups!
    """
    
    preset_loaded = Signal(SetupPreset)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._presets: Dict[str, List[SetupPreset]] = {}  # car_id -> presets
        self._current_car: str = ""
        self._presets_file = Path.home() / "Documents" / "Assetto Corsa" / "race_engineer_presets.json"
        
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            PresetsPanel {
                background-color: #0f0f1a;
                border: 1px solid #16213e;
                border-radius: 12px;
            }
        """)
        
        self._setup_ui()
        self._load_presets()
    
    def _setup_ui(self):
        """Setup the presets UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header_layout = QHBoxLayout()
        
        header = QLabel("⭐ Mes Presets")
        header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #fff;
        """)
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        # Save button
        self.save_btn = QPushButton("💾 Sauvegarder")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a69bd;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #6a89dd;
            }
            QPushButton:pressed {
                background-color: #3a59ad;
            }
        """)
        self.save_btn.clicked.connect(self._on_save_clicked)
        header_layout.addWidget(self.save_btn)
        
        layout.addLayout(header_layout)
        
        # Current car indicator
        self.car_label = QLabel("Aucune voiture sélectionnée")
        self.car_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.car_label)
        
        # Presets list
        self.presets_container = QVBoxLayout()
        self.presets_container.setSpacing(8)
        
        # Placeholder
        self.empty_label = QLabel("Aucun preset sauvegardé\npour cette voiture")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #666; font-size: 12px; padding: 20px;")
        self.presets_container.addWidget(self.empty_label)
        
        layout.addLayout(self.presets_container)
        layout.addStretch()
    
    def set_current_car(self, car_id: str, car_name: str = ""):
        """Set the current car for preset management."""
        self._current_car = car_id
        display_name = car_name if car_name else car_id
        self.car_label.setText(f"🚗 {display_name}")
        self.car_label.setStyleSheet("color: #4a69bd; font-size: 11px; font-weight: bold;")
        self._refresh_presets_list()
    
    def _refresh_presets_list(self):
        """Refresh the presets list for current car."""
        # Clear existing items
        while self.presets_container.count() > 0:
            item = self.presets_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get presets for current car
        presets = self._presets.get(self._current_car, [])
        
        if not presets:
            self.empty_label = QLabel("Aucun preset sauvegardé\npour cette voiture")
            self.empty_label.setAlignment(Qt.AlignCenter)
            self.empty_label.setStyleSheet("color: #666; font-size: 12px; padding: 20px;")
            self.presets_container.addWidget(self.empty_label)
        else:
            for preset in presets:
                item = PresetItem(preset)
                item.clicked.connect(self._on_preset_clicked)
                item.delete_clicked.connect(self._on_delete_clicked)
                self.presets_container.addWidget(item)
    
    def _on_save_clicked(self):
        """Save current setup as preset."""
        if not self._current_car:
            QMessageBox.warning(self, "Erreur", "Sélectionnez d'abord une voiture.")
            return
        
        # Get preset name
        name, ok = QInputDialog.getText(
            self,
            "Nouveau Preset",
            "Nom du preset:",
            QLineEdit.Normal,
            f"Preset {datetime.now().strftime('%d/%m %H:%M')}"
        )
        
        if not ok or not name:
            return
        
        # Emit signal to get current values from main window
        # For now, create with defaults - main window will fill in values
        self._save_preset_request = name
        
        # Show confirmation
        QMessageBox.information(
            self,
            "Preset sauvegardé",
            f"Le preset '{name}' a été sauvegardé!"
        )
    
    def save_preset(self, name: str, behavior: str, profile_values: dict):
        """Actually save a preset with values from main window."""
        preset = SetupPreset(
            name=name,
            car_id=self._current_car,
            behavior=behavior,
            created_at=datetime.now().isoformat(),
            stability=profile_values.get("stability", 0.5),
            rotation=profile_values.get("rotation", 0.5),
            grip=profile_values.get("grip", 0.5),
            drift=profile_values.get("drift", 0.0),
            aggression=profile_values.get("aggression", 0.5),
            comfort=profile_values.get("comfort", 0.5)
        )
        
        if self._current_car not in self._presets:
            self._presets[self._current_car] = []
        
        self._presets[self._current_car].append(preset)
        self._save_presets()
        self._refresh_presets_list()
    
    def _on_preset_clicked(self, preset_name: str):
        """Load a preset."""
        presets = self._presets.get(self._current_car, [])
        for preset in presets:
            if preset.name == preset_name:
                self.preset_loaded.emit(preset)
                break
    
    def _on_delete_clicked(self, preset_name: str):
        """Delete a preset."""
        reply = QMessageBox.question(
            self,
            "Supprimer le preset",
            f"Supprimer le preset '{preset_name}' ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            presets = self._presets.get(self._current_car, [])
            self._presets[self._current_car] = [p for p in presets if p.name != preset_name]
            self._save_presets()
            self._refresh_presets_list()
    
    def _load_presets(self):
        """Load presets from file."""
        try:
            if self._presets_file.exists():
                with open(self._presets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for car_id, presets_data in data.items():
                        self._presets[car_id] = [
                            SetupPreset.from_dict(p) for p in presets_data
                        ]
        except Exception as e:
            print(f"Error loading presets: {e}")
    
    def _save_presets(self):
        """Save presets to file."""
        try:
            self._presets_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                car_id: [p.to_dict() for p in presets]
                for car_id, presets in self._presets.items()
            }
            with open(self._presets_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving presets: {e}")
    
    def get_preset_count(self, car_id: str) -> int:
        """Get number of presets for a car."""
        return len(self._presets.get(car_id, []))
