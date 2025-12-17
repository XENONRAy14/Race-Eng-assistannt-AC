"""
Presets Panel - Save and load setup presets per car.
Modern Initial D black/red gradient design.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QListWidget, QListWidgetItem, QLineEdit,
    QMessageBox, QInputDialog, QComboBox, QGroupBox, QScrollArea
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
    
    stability: float = 0.5
    rotation: float = 0.5
    grip: float = 0.5
    drift: float = 0.0
    aggression: float = 0.5
    comfort: float = 0.5
    
    notes: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "SetupPreset":
        return cls(**data)


class PresetItem(QFrame):
    """A single preset item with Initial D styling."""
    
    clicked = Signal(str)
    delete_clicked = Signal(str)
    
    def __init__(self, preset: SetupPreset, parent=None):
        super().__init__(parent)
        self.preset = preset
        
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a0000, stop:1 #000000);
                border: 2px solid #ff0000;
                border-radius: 8px;
                padding: 10px;
            }
            QFrame:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #330000, stop:1 #000000);
                border: 2px solid #ff3333;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Name
        name_label = QLabel(preset.name)
        name_label.setStyleSheet("""
            color: #ffffff;
            font-family: 'Arial', sans-serif;
            font-size: 15px;
            font-weight: bold;
        """)
        info_layout.addWidget(name_label)
        
        # Behavior
        behavior_label = QLabel(f"Mode: {preset.behavior}")
        behavior_label.setStyleSheet("""
            color: #ff8800;
            font-family: 'Arial', sans-serif;
            font-size: 12px;
        """)
        info_layout.addWidget(behavior_label)
        
        # Date
        date_label = QLabel(f"Créé: {preset.created_at}")
        date_label.setStyleSheet("""
            color: #666;
            font-family: 'Arial', sans-serif;
            font-size: 10px;
        """)
        info_layout.addWidget(date_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Delete button
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(35, 35)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 0, 0, 0.3);
                border: 1px solid #ff0000;
                border-radius: 6px;
                color: #ff0000;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 0.5);
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(preset.name))
        layout.addWidget(delete_btn)
        
        self.setMinimumHeight(80)
    
    def mousePressEvent(self, event):
        """Handle click."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.preset.name)
        super().mousePressEvent(event)


class PresetsPanel(QWidget):
    """Main presets panel with Initial D design."""
    
    preset_loaded = Signal(SetupPreset)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.presets: Dict[str, SetupPreset] = {}
        self.current_car_id: Optional[str] = None
        self.presets_file = Path.home() / "Documents" / "Assetto Corsa" / "race_engineer_presets.json"
        
        self._setup_ui()
        self._load_presets()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("⭐ Mes Presets")
        title.setStyleSheet("""
            color: #ff0000;
            font-family: 'Arial', sans-serif;
            font-size: 22px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Save button
        self.save_button = QPushButton("💾 Sauvegarder")
        self.save_button.setMinimumHeight(40)
        self.save_button.clicked.connect(self._save_current_preset)
        header_layout.addWidget(self.save_button)
        
        layout.addLayout(header_layout)
        
        # Car selection info
        self.car_label = QLabel("Aucune voiture sélectionnée")
        self.car_label.setStyleSheet("""
            color: #888;
            font-family: 'Arial', sans-serif;
            font-size: 12px;
        """)
        layout.addWidget(self.car_label)
        
        # Presets list
        list_container = QFrame()
        list_container.setFrameStyle(QFrame.NoFrame)
        list_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a0000, stop:1 #000000);
                border: 2px solid #ff0000;
                border-radius: 12px;
            }
        """)
        
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(15, 15, 15, 15)
        list_layout.setSpacing(10)
        
        # Scroll area for presets
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)
        
        self.presets_container = QWidget()
        self.presets_layout = QVBoxLayout(self.presets_container)
        self.presets_layout.setSpacing(10)
        self.presets_layout.setContentsMargins(0, 0, 0, 0)
        
        # Empty state label
        self.empty_label = QLabel("Aucun preset sauvegardé\npour cette voiture")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("""
            color: #666;
            font-family: 'Arial', sans-serif;
            font-size: 14px;
            padding: 40px;
        """)
        self.presets_layout.addWidget(self.empty_label)
        
        self.presets_layout.addStretch()
        
        scroll.setWidget(self.presets_container)
        list_layout.addWidget(scroll)
        
        layout.addWidget(list_container)
    
    def set_current_car(self, car_id: str):
        """Set the current car and update display."""
        self.current_car_id = car_id
        self.car_label.setText(f"Voiture: {car_id}")
        self._update_presets_display()
    
    def _update_presets_display(self):
        """Update the presets list display."""
        # Clear existing items
        while self.presets_layout.count() > 0:
            item = self.presets_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Filter presets for current car
        car_presets = [p for p in self.presets.values() if p.car_id == self.current_car_id]
        
        if not car_presets:
            self.empty_label = QLabel("Aucun preset sauvegardé\npour cette voiture")
            self.empty_label.setAlignment(Qt.AlignCenter)
            self.empty_label.setStyleSheet("""
                color: #666;
                font-family: 'Arial', sans-serif;
                font-size: 14px;
                padding: 40px;
            """)
            self.presets_layout.addWidget(self.empty_label)
        else:
            for preset in car_presets:
                item = PresetItem(preset)
                item.clicked.connect(self._load_preset)
                item.delete_clicked.connect(self._delete_preset)
                self.presets_layout.addWidget(item)
        
        self.presets_layout.addStretch()
    
    def _save_current_preset(self):
        """Save current setup as a preset."""
        if not self.current_car_id:
            QMessageBox.warning(self, "Erreur", "Aucune voiture sélectionnée!")
            return
        
        name, ok = QInputDialog.getText(
            self,
            "Sauvegarder Preset",
            "Nom du preset:",
            QLineEdit.Normal,
            ""
        )
        
        if ok and name:
            # Create preset (values will be filled by main window)
            preset = SetupPreset(
                name=name,
                car_id=self.current_car_id,
                behavior="Balanced",
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M")
            )
            
            self.presets[name] = preset
            self._save_presets()
            self._update_presets_display()
            
            QMessageBox.information(self, "Succès", f"Preset '{name}' sauvegardé!")
    
    def _load_preset(self, name: str):
        """Load a preset."""
        if name in self.presets:
            self.preset_loaded.emit(self.presets[name])
            QMessageBox.information(self, "Succès", f"Preset '{name}' chargé!")
    
    def _delete_preset(self, name: str):
        """Delete a preset."""
        reply = QMessageBox.question(
            self,
            "Confirmer",
            f"Supprimer le preset '{name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if name in self.presets:
                del self.presets[name]
                self._save_presets()
                self._update_presets_display()
    
    def _load_presets(self):
        """Load presets from file."""
        if self.presets_file.exists():
            try:
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.presets = {
                        name: SetupPreset.from_dict(preset_data)
                        for name, preset_data in data.items()
                    }
            except Exception as e:
                print(f"Error loading presets: {e}")
    
    def _save_presets(self):
        """Save presets to file."""
        try:
            self.presets_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                data = {name: preset.to_dict() for name, preset in self.presets.items()}
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving presets: {e}")
    
    def update_preset_values(self, name: str, **values):
        """Update values for a preset."""
        if name in self.presets:
            for key, value in values.items():
                if hasattr(self.presets[name], key):
                    setattr(self.presets[name], key, value)
            self._save_presets()
