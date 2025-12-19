"""
Quick Start Widget - Simplified one-click interface for beginners.
Automates the entire setup generation process.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont


class QuickStartWidget(QWidget):
    """
    Ultra-simplified interface for quick setup generation.
    One-click solution for beginners.
    """
    
    generate_auto_setup = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._status = "waiting"
        self._progress_timer = None
        self._progress_value = 0
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # Title
        title = QLabel("🚀 Démarrage Rapide")
        title.setStyleSheet("""
            color: #ff0000;
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 20px;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Lance Assetto Corsa et l'assistant fera le reste !")
        subtitle.setStyleSheet("""
            color: #cccccc;
            font-size: 16px;
            margin-bottom: 30px;
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        
        # Status card
        self.status_card = QFrame()
        self.status_card.setStyleSheet("""
            QFrame {
                background: rgba(26, 0, 0, 0.5);
                border: 2px solid #ff0000;
                border-radius: 12px;
                padding: 30px;
            }
        """)
        
        status_layout = QVBoxLayout(self.status_card)
        status_layout.setSpacing(20)
        
        # Status icon and text
        self.status_icon = QLabel("⏳")
        self.status_icon.setStyleSheet("font-size: 64px;")
        self.status_icon.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_icon)
        
        self.status_label = QLabel("En attente d'Assetto Corsa...")
        self.status_label.setStyleSheet("""
            color: #ffffff;
            font-size: 20px;
            font-weight: bold;
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        self.status_detail = QLabel("Lance le jeu et sélectionne une voiture et une piste")
        self.status_detail.setStyleSheet("""
            color: #888888;
            font-size: 14px;
        """)
        self.status_detail.setAlignment(Qt.AlignCenter)
        self.status_detail.setWordWrap(True)
        status_layout.addWidget(self.status_detail)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: #ff0000;
                border-radius: 4px;
            }
        """)
        self.progress_bar.hide()
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(self.status_card)
        
        # Big GO button
        self.go_button = QPushButton("⚡ GÉNÉRER MON SETUP")
        self.go_button.clicked.connect(self.generate_auto_setup.emit)
        self.go_button.setMinimumHeight(80)
        self.go_button.setEnabled(False)
        self.go_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #666666, stop:1 #444444);
                color: #888888;
                border: none;
                border-radius: 12px;
                font-size: 24px;
                font-weight: bold;
                padding: 20px;
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
        layout.addWidget(self.go_button)
        
        # Info boxes
        info_layout = QHBoxLayout()
        info_layout.setSpacing(15)
        
        # Auto-detect box
        auto_box = self._create_info_box(
            "🎯",
            "Détection Auto",
            "Voiture et piste détectées automatiquement"
        )
        info_layout.addWidget(auto_box)
        
        # Smart setup box
        smart_box = self._create_info_box(
            "🤖",
            "Setup Intelligent",
            "Adapté à ton style de conduite"
        )
        info_layout.addWidget(smart_box)
        
        # One-click box
        click_box = self._create_info_box(
            "⚡",
            "Un Clic",
            "Tout est appliqué automatiquement"
        )
        info_layout.addWidget(click_box)
        
        layout.addLayout(info_layout)
        layout.addStretch()
    
    def _create_info_box(self, icon: str, title: str, description: str) -> QFrame:
        """Create an info box."""
        box = QFrame()
        box.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(box)
        layout.setSpacing(8)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            color: #888888;
            font-size: 11px;
        """)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        return box
    
    def set_status(self, status: str, car: str = "", track: str = ""):
        """
        Update the status display.
        
        Args:
            status: waiting, detecting, ready, generating, done
            car: Car name (optional)
            track: Track name (optional)
        """
        self._status = status
        
        if status == "waiting":
            self.status_icon.setText("⏳")
            self.status_label.setText("En attente d'Assetto Corsa...")
            self.status_detail.setText("Lance le jeu et sélectionne une voiture et une piste")
            self.go_button.setEnabled(False)
            self.progress_bar.hide()
            self.status_card.setStyleSheet("""
                QFrame {
                    background: rgba(26, 0, 0, 0.5);
                    border: 2px solid #ff0000;
                    border-radius: 12px;
                    padding: 30px;
                }
            """)
        
        elif status == "detecting":
            self.status_icon.setText("🔍")
            self.status_label.setText("Détection en cours...")
            self.status_detail.setText("Connexion à Assetto Corsa")
            self.go_button.setEnabled(False)
            self._start_progress_animation()
            self.status_card.setStyleSheet("""
                QFrame {
                    background: rgba(26, 13, 0, 0.5);
                    border: 2px solid #ff8800;
                    border-radius: 12px;
                    padding: 30px;
                }
            """)
        
        elif status == "ready":
            self.status_icon.setText("✅")
            self.status_label.setText(f"Prêt à générer !")
            detail = ""
            if car:
                detail += f"🏎️ {car}"
            if track:
                if detail:
                    detail += "\n"
                detail += f"🏁 {track}"
            self.status_detail.setText(detail if detail else "Voiture et piste détectées")
            self.go_button.setEnabled(True)
            self._stop_progress_animation()
            self.status_card.setStyleSheet("""
                QFrame {
                    background: rgba(0, 26, 0, 0.5);
                    border: 2px solid #00ff00;
                    border-radius: 12px;
                    padding: 30px;
                }
            """)
        
        elif status == "generating":
            self.status_icon.setText("⚙️")
            self.status_label.setText("Génération du setup...")
            self.status_detail.setText("Optimisation en cours avec l'IA")
            self.go_button.setEnabled(False)
            self._start_progress_animation()
            self.status_card.setStyleSheet("""
                QFrame {
                    background: rgba(0, 0, 26, 0.5);
                    border: 2px solid #0088ff;
                    border-radius: 12px;
                    padding: 30px;
                }
            """)
        
        elif status == "done":
            self.status_icon.setText("🎉")
            self.status_label.setText("Setup appliqué avec succès !")
            self.status_detail.setText("Tu peux maintenant rouler avec ton setup optimisé")
            self.go_button.setEnabled(True)
            self.go_button.setText("⚡ RÉGÉNÉRER")
            self._stop_progress_animation()
            self.status_card.setStyleSheet("""
                QFrame {
                    background: rgba(0, 26, 0, 0.5);
                    border: 2px solid #00ff00;
                    border-radius: 12px;
                    padding: 30px;
                }
            """)
    
    def _start_progress_animation(self):
        """Start animated progress bar."""
        self.progress_bar.show()
        self._progress_value = 0
        self.progress_bar.setValue(0)
        
        if self._progress_timer:
            self._progress_timer.stop()
        
        self._progress_timer = QTimer(self)
        self._progress_timer.timeout.connect(self._update_progress)
        self._progress_timer.start(50)  # Update every 50ms
    
    def _stop_progress_animation(self):
        """Stop animated progress bar."""
        if self._progress_timer:
            self._progress_timer.stop()
            self._progress_timer = None
        self.progress_bar.hide()
        self._progress_value = 0
    
    def _update_progress(self):
        """Update progress bar animation."""
        self._progress_value = (self._progress_value + 2) % 101
        self.progress_bar.setValue(self._progress_value)
