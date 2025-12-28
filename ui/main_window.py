"""
Main Window - Primary application window.
Orchestrates all UI components and connects to backend services.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QSplitter, QStatusBar,
    QMessageBox, QTextEdit, QGroupBox, QScrollArea,
    QProgressBar, QInputDialog, QFileDialog, QMenuBar, QMenu,
    QTabWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QPalette

from typing import Optional
from pathlib import Path

from ui.car_track_selector import CarTrackSelector
from ui.behavior_selector import BehaviorSelector
from ui.sliders_panel import SlidersPanel
from ui.telemetry_panel import TelemetryPanel, TelemetryData
from ui.presets_panel import PresetsPanel
from ui.driving_style_widget import DrivingStyleWidget
from ui.track_map_widget import TrackMapWidget

from models.driver_profile import DriverProfile
from models.setup import Setup
from models.car import Car
from models.track import Track

from core.setup_engine import SetupEngine
from core.setup_engine_v2 import SetupEngineV2, CATEGORY_TARGETS
from core.physics_refiner import PhysicsRefiner
from core.ac_monitor_v2 import ACMonitorV2
from ai.decision_engine import DecisionEngine
from ai.driving_analyzer import DrivingAnalyzer
from assetto.ac_connector import ACConnector
from assetto.ac_shared_memory import ACSharedMemory, ACStatus
from data.setup_repository import SetupRepository
from config.user_settings import get_user_settings
import json


class MainWindow(QMainWindow):
    """
    Main application window.
    Provides the primary interface for the Race Engineer Assistant.
    """
    
    def __init__(
        self,
        repository: SetupRepository,
        detector=None,
        parent=None
    ):
        super().__init__(parent)
        
        # Services
        self.repository = repository
        # Pass the pre-configured detector to ACConnector
        self.connector = ACConnector(detector=detector)
        self.setup_engine = SetupEngine()
        self.setup_engine_v2 = SetupEngineV2()  # V2 engine
        self.physics_refiner = PhysicsRefiner()  # V2.1 refiner
        self.ac_monitor_v2 = ACMonitorV2()  # V2 thermal monitor
        self.decision_engine = DecisionEngine(self.setup_engine)
        self.shared_memory = ACSharedMemory()
        self.driving_analyzer = DrivingAnalyzer()
        
        # Try to connect AC Monitor V2
        try:
            self.ac_monitor_v2.connect()
        except Exception as e:
            print(f"[AC MONITOR V2] Could not connect: {e}")
        
        # Adaptive AI engine
        from ai.adaptive_setup_engine import AdaptiveSetupEngine, TrackConditions
        self.adaptive_engine = AdaptiveSetupEngine()
        self.current_conditions = TrackConditions()  # Default conditions
        
        # State
        self._current_profile: Optional[DriverProfile] = None
        self._current_setup: Optional[Setup] = None
        self._last_score = None
        self._ac_polling_timer: Optional[QTimer] = None
        self._telemetry_timer: Optional[QTimer] = None
        self._last_detected_car: str = ""
        self._last_detected_track: str = ""
        self._auto_generate_enabled: bool = True  # Auto-generate on detection
        self._cars_cache: list[Car] = []
        self._tracks_cache: list[Track] = []
        self._last_sector_index: int = -1
        self._track_map_initialized: bool = False
        self._last_completed_laps: int = 0  # Track lap completion for AI learning
        
        # UI setup
        self._setup_window()
        self._setup_menubar()
        self._setup_ui()
        self._setup_statusbar()
        self._apply_dark_theme()
        
        # Initialize
        QTimer.singleShot(100, self._initialize)
    
    def _setup_window(self) -> None:
        """Configure window properties."""
        self.setWindowTitle("Race Engineer Assistant - Assetto Corsa")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
    
    def _setup_menubar(self) -> None:
        """Create the menu bar."""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #000000;
                color: #ffffff;
                padding: 5px;
                border-bottom: 1px solid rgba(255, 0, 0, 0.15);
            }
            QMenuBar::item {
                padding: 6px 12px;
                background: transparent;
            }
            QMenuBar::item:selected {
                background-color: rgba(255, 0, 0, 0.2);
            }
            QMenu {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid rgba(255, 0, 0, 0.3);
            }
            QMenu::item {
                padding: 8px 25px;
            }
            QMenu::item:selected {
                background-color: #ff0000;
            }
        """)
        
        # File menu
        file_menu = menubar.addMenu("Fichier")
        
        # Settings menu
        settings_menu = menubar.addMenu("Paramètres")
        
        # AC folder action
        ac_folder_action = settings_menu.addAction("📁 Dossier Assetto Corsa...")
        ac_folder_action.triggered.connect(self._on_select_ac_folder)
        
        # Refresh action
        refresh_action = settings_menu.addAction("🔄 Actualiser voitures/pistes")
        refresh_action.triggered.connect(self._on_refresh_content)
        
        # Help menu
        help_menu = menubar.addMenu("Aide")
        about_action = help_menu.addAction("À propos")
        about_action.triggered.connect(self._on_about)
    
    def _on_select_ac_folder(self) -> None:
        """Let user select AC installation folder manually."""
        try:
            print("[DEBUG] Opening folder selection dialog...")
            folder = QFileDialog.getExistingDirectory(
                self,
                "Sélectionner le dossier d'installation Assetto Corsa",
                "",
                QFileDialog.ShowDirsOnly
            )
            
            print(f"[DEBUG] Selected folder: {folder}")
            
            if not folder:
                print("[DEBUG] No folder selected, user cancelled")
                QMessageBox.information(
                    self,
                    "Sélection annulée",
                    "Aucun dossier sélectionné.\n\nVous pouvez réessayer via Paramètres > Sélectionner dossier AC."
                )
                return
            
            folder_path = Path(folder)
            print(f"[DEBUG] Checking folder: {folder_path}")
            
            # Validate it's an AC folder - check for content/cars and content/tracks
            cars_path = folder_path / "content" / "cars"
            tracks_path = folder_path / "content" / "tracks"
            
            print(f"[DEBUG] Checking cars path: {cars_path.exists()}")
            print(f"[DEBUG] Checking tracks path: {tracks_path.exists()}")
            
            if not cars_path.exists() or not tracks_path.exists():
                error_msg = f"Dossier invalide!\n\n"
                error_msg += f"Dossier sélectionné: {folder_path}\n\n"
                error_msg += f"❌ content/cars existe: {cars_path.exists()}\n"
                error_msg += f"❌ content/tracks existe: {tracks_path.exists()}\n\n"
                error_msg += "Cherchez le dossier contenant 'content/cars' et 'content/tracks'.\n"
                error_msg += "Exemple: C:\\Steam\\steamapps\\common\\assettocorsa"
                
                print(f"[ERROR] Invalid folder: {error_msg}")
                
                QMessageBox.warning(
                    self,
                    "Dossier invalide",
                    error_msg
                )
                return
            
            print("[DEBUG] Folder validated successfully")
            
            # Update detector with custom path
            from assetto.ac_detector import ACInstallation
            
            # Find or create documents path
            docs_path = Path.home() / "Documents" / "Assetto Corsa"
            print(f"[DEBUG] Documents path: {docs_path}")
            
            if not docs_path.exists():
                print("[DEBUG] Creating Documents folder...")
                docs_path.mkdir(parents=True, exist_ok=True)
            
            print("[DEBUG] Creating installation object...")
            
            # Create or update installation
            self.connector.detector._installation = ACInstallation(documents_path=docs_path)
            self.connector.detector._installation.game_path = folder_path
            self.connector.detector._installation.cars_path = cars_path
            self.connector.detector._installation.tracks_path = tracks_path
            self.connector.detector._installation.is_valid = True
            self.connector.detector._installation.can_write_setups = True
            
            print("[DEBUG] Setting up writer...")
            
            # Setup writer needs the setups path
            self.connector.writer.set_base_path(docs_path / "setups")
            
            print("[DEBUG] Saving path to settings...")
            
            # Save the path for next launch
            user_settings = get_user_settings()
            user_settings.set_ac_game_path(folder_path)
            
            print("[DEBUG] Reconnecting to AC...")
            
            # Force reconnect to update status
            self.statusbar.showMessage("Reconnexion à Assetto Corsa...")
            self.repaint()  # Force UI update
            
            status = self.connector.connect()
            
            print(f"[DEBUG] Connection status: {status.is_connected}")
            print(f"[DEBUG] Cars count: {status.cars_count}")
            print(f"[DEBUG] Tracks count: {status.tracks_count}")
            
            if status.is_connected:
                print("[DEBUG] Connection successful, loading content...")
                
                # Update connection status in UI
                self.connection_label.setText("● CONNECTED")
                self.connection_label.setStyleSheet("color: #00ff00; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
                
                # Load cars and tracks
                cars = self.connector.get_cars(force_refresh=True)
                tracks = self.connector.get_tracks(force_refresh=True)
                
                print(f"[DEBUG] Loaded {len(cars)} cars and {len(tracks)} tracks")
                
                self._cars_cache = cars
                self._tracks_cache = tracks
                
                self.car_track_selector.set_cars(cars)
                self.car_track_selector.set_tracks(tracks)
                
                self.statusbar.showMessage(
                    f"✅ Connecté - {len(cars)} voitures, {len(tracks)} pistes"
                )
                
                success_msg = f"✅ Assetto Corsa détecté avec succès!\n\n"
                success_msg += f"📁 Dossier: {folder_path}\n\n"
                success_msg += f"🚗 Voitures trouvées: {len(cars)}\n"
                success_msg += f"🏁 Pistes trouvées: {len(tracks)}\n\n"
                success_msg += f"💾 Ce chemin sera mémorisé pour les prochains lancements.\n\n"
                success_msg += f"Vous pouvez maintenant générer des setups!"
                
                print("[DEBUG] Showing success message...")
                
                QMessageBox.information(
                    self,
                    "✅ Connexion réussie",
                    success_msg
                )
                
                print("[DEBUG] Folder selection completed successfully")
            else:
                print(f"[ERROR] Connection failed: {status.error_message}")
                
                self.connection_label.setText("🔴 Erreur de connexion")
                self.connection_label.setStyleSheet("color: #f44336;")
                self.statusbar.showMessage("Erreur lors de la connexion")
                
                error_msg = f"❌ La connexion a échoué!\n\n"
                error_msg += f"Dossier configuré: {folder_path}\n\n"
                error_msg += f"Erreur: {status.error_message}\n\n"
                error_msg += f"Vérifiez que le dossier contient bien:\n"
                error_msg += f"- content/cars\n"
                error_msg += f"- content/tracks\n\n"
                error_msg += f"Contactez le support si le problème persiste."
                
                QMessageBox.critical(
                    self,
                    "❌ Erreur de connexion",
                    error_msg
                )
        
        except Exception as e:
            print(f"[CRITICAL ERROR] Exception in folder selection: {e}")
            import traceback
            traceback.print_exc()
            
            QMessageBox.critical(
                self,
                "❌ Erreur critique",
                f"Une erreur inattendue s'est produite:\n\n{str(e)}\n\n"
                f"Veuillez réessayer ou contacter le support."
            )
    
    def _apply_saved_ac_path(self, folder_path: Path) -> None:
        """Apply a saved AC path to the connector."""
        from assetto.ac_detector import ACInstallation
        
        # Find documents path
        docs_path = Path.home() / "Documents" / "Assetto Corsa"
        if not docs_path.exists():
            docs_path.mkdir(parents=True, exist_ok=True)
        
        # Create installation object
        self.connector.detector._installation = ACInstallation(documents_path=docs_path)
        self.connector.detector._installation.game_path = folder_path
        self.connector.detector._installation.cars_path = folder_path / "content" / "cars"
        self.connector.detector._installation.tracks_path = folder_path / "content" / "tracks"
        self.connector.detector._installation.is_valid = True
        self.connector.detector._installation.can_write_setups = True
        
        # Setup writer needs the setups path
        self.connector.writer.set_base_path(docs_path / "setups")
    
    def _on_refresh_content(self) -> None:
        """Refresh cars and tracks from AC folder."""
        cars = self.connector.get_cars(force_refresh=True)
        tracks = self.connector.get_tracks(force_refresh=True)
        
        self._cars_cache = cars
        self._tracks_cache = tracks
        
        self.car_track_selector.set_cars(cars)
        self.car_track_selector.set_tracks(tracks)
        
        self.statusbar.showMessage(f"Actualisé: {len(cars)} voitures, {len(tracks)} pistes")
    
    def _on_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "À propos",
            "Race Engineer Assistant v1.0.0\n\n"
            "Ingénieur de course virtuel pour Assetto Corsa\n"
            "Optimisé pour le Touge\n\n"
            "Génère automatiquement des setups basés sur votre style de conduite.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Developed by XENONRAy\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    
    def _setup_ui(self) -> None:
        """Set up the main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Car/Track selection
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Center panel - Behavior and Sliders
        center_panel = self._create_center_panel()
        splitter.addWidget(center_panel)
        
        # Right panel - Output and Actions
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([350, 400, 450])
        
        main_layout.addWidget(splitter, 1)
        
        # Bottom action bar
        action_bar = self._create_action_bar()
        main_layout.addWidget(action_bar)
    
    def _create_header(self) -> QWidget:
        """Create the header widget."""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(header)
        
        # Logo/Title
        title = QLabel("🏎️ Race Engineer Assistant")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #fff;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Connection status
        self.connection_label = QLabel("⚪ Connexion...")
        self.connection_label.setStyleSheet("color: #888;")
        layout.addWidget(self.connection_label)
        
        # Live game status
        self.game_status_label = QLabel("🎮 Jeu: Non détecté")
        self.game_status_label.setStyleSheet("color: #888; margin-left: 20px;")
        layout.addWidget(self.game_status_label)
        
        return header
    
    def _create_left_panel(self) -> QWidget:
        """Create the left panel with car/track selection."""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Car/Track selector
        self.car_track_selector = CarTrackSelector()
        self.car_track_selector.selectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.car_track_selector)
        
        return panel
    
    def _create_center_panel(self) -> QWidget:
        """Create the center panel with behavior and sliders."""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Behavior selector
        self.behavior_selector = BehaviorSelector()
        self.behavior_selector.behaviorChanged.connect(self._on_behavior_changed)
        scroll_layout.addWidget(self.behavior_selector)
        
        # Sliders panel
        self.sliders_panel = SlidersPanel()
        self.sliders_panel.profileChanged.connect(self._on_profile_changed)
        scroll_layout.addWidget(self.sliders_panel)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        
        layout.addWidget(scroll)
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """Create the right panel with tabs for different features."""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Tab widget for different panels
        self.right_tabs = QTabWidget()
        self.right_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #888;
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #4a69bd;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3a3a4a;
            }
        """)
        
        # Tab 0: Quick Start (NEW - First tab for simplicity)
        from ui.quick_start_widget import QuickStartWidget
        self.quick_start_widget = QuickStartWidget()
        self.quick_start_widget.generate_auto_setup.connect(self._on_quick_start_generate)
        self.right_tabs.addTab(self.quick_start_widget, "🚀 Démarrage Rapide")
        
        # Tab 1: Setup Preview (original)
        setup_tab = self._create_setup_preview_tab()
        self.right_tabs.addTab(setup_tab, "📊 Setup")
        
        # Tab 2: Live Telemetry
        self.telemetry_panel = TelemetryPanel()
        self.right_tabs.addTab(self.telemetry_panel, "📡 Télémétrie")
        
        # Tab 3: Track Map with sector times
        self.track_map_widget = TrackMapWidget()
        self.right_tabs.addTab(self.track_map_widget, "🗺️ Piste")
        
        # Tab 4: Driving Analysis
        self.driving_style_widget = DrivingStyleWidget()
        self.driving_style_widget.apply_recommendation.connect(self._on_apply_style_recommendation)
        self.right_tabs.addTab(self.driving_style_widget, "🧠 Analyse")
        
        # Tab 5: Presets
        self.presets_panel = PresetsPanel()
        self.presets_panel.preset_loaded.connect(self._on_preset_loaded)
        self.right_tabs.addTab(self.presets_panel, "⭐ Presets")
        
        # Tab 6: Adaptive IA
        from ui.adaptive_panel import AdaptivePanel
        self.adaptive_panel = AdaptivePanel()
        self.adaptive_panel.apply_optimization.connect(self._on_apply_adaptive)
        self.right_tabs.addTab(self.adaptive_panel, "🤖 IA Adaptive")
        
        layout.addWidget(self.right_tabs)
        
        return panel
    
    def _create_setup_preview_tab(self) -> QWidget:
        """Create the setup preview tab content."""
        tab = QWidget()
        tab.setStyleSheet("background: #0a0a0a;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(25)
        
        # Score display
        score_section = QFrame()
        score_section.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.02);
                border: none;
                border-left: 3px solid #ff0000;
                padding: 25px 30px;
            }
        """)
        score_layout = QVBoxLayout(score_section)
        score_layout.setSpacing(10)
        
        score_title = QLabel("AI SCORE")
        score_title.setStyleSheet("""
            color: #666666;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        score_layout.addWidget(score_title)
        
        self.score_label = QLabel("--/100")
        self.score_label.setFont(QFont("Consolas", 32, QFont.Bold))
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setStyleSheet("color: #ffffff;")
        score_layout.addWidget(self.score_label)
        
        self.confidence_label = QLabel("Confiance: --%")
        self.confidence_label.setAlignment(Qt.AlignCenter)
        self.confidence_label.setStyleSheet("color: #999999; font-size: 13px;")
        score_layout.addWidget(self.confidence_label)
        
        layout.addWidget(score_section)
        
        # Setup preview
        preview_title = QLabel("KEY VALUES")
        preview_title.setStyleSheet("""
            color: #666666;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        layout.addWidget(preview_title)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.02);
                color: #ffffff;
                border: none;
                border-left: 3px solid #666666;
                font-family: Consolas, monospace;
                font-size: 12px;
                padding: 15px;
            }
        """)
        self.preview_text.setMaximumHeight(200)
        layout.addWidget(self.preview_text)
        
        # AI Notes
        notes_title = QLabel("AI NOTES")
        notes_title.setStyleSheet("""
            color: #666666;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        layout.addWidget(notes_title)
        
        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)
        self.notes_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.02);
                color: #999999;
                border: none;
                border-left: 3px solid #666666;
                font-size: 12px;
                padding: 15px;
            }
        """)
        self.notes_text.setMaximumHeight(120)
        layout.addWidget(self.notes_text)
        
        layout.addStretch()
        
        return tab
    
    def _on_apply_style_recommendation(self, behavior: str) -> None:
        """Apply the recommended behavior from driving analysis."""
        from PySide6.QtWidgets import QMessageBox
        
        # Map behavior to display name
        behavior_names = {
            "safe": "Safe (Sécuritaire)",
            "balanced": "Balanced (Équilibré)",
            "attack": "Attack (Agressif)",
            "drift": "Drift"
        }
        
        behavior_name = behavior_names.get(behavior, behavior)
        
        # Apply the behavior
        self.behavior_selector.set_behavior(behavior)
        self._on_behavior_changed(behavior)
        
        # Show confirmation
        self.statusbar.showMessage(f"✨ Mode '{behavior_name}' appliqué selon ton style de conduite!")
        
        QMessageBox.information(
            self,
            "✅ Recommandation appliquée",
            f"Le mode '{behavior_name}' a été appliqué avec succès!\n\n"
            f"Ce mode est adapté à ton style de conduite détecté.\n\n"
            f"Tu peux maintenant générer un setup optimisé."
        )
    
    def _on_preset_loaded(self, preset) -> None:
        """Load a preset into the current settings."""
        # Set behavior
        self.behavior_selector.set_behavior(preset.behavior)
        
        # Set profile values
        if self._current_profile:
            self._current_profile.stability_factor = preset.stability
            self._current_profile.rotation_factor = preset.rotation
            self._current_profile.grip_factor = preset.grip
            self._current_profile.drift_factor = preset.drift
            self._current_profile.aggression_factor = preset.aggression
            self._current_profile.comfort_factor = preset.comfort
            self.sliders_panel.set_profile(self._current_profile)
        
        self._update_preview()
        self.statusbar.showMessage(f"✨ Preset '{preset.name}' chargé!")
    
    def _on_apply_adaptive(self) -> None:
        """Apply adaptive AI optimization to current setup."""
        from PySide6.QtWidgets import QMessageBox
        from ai.adaptive_setup_engine import TrackConditions
        
        # Check if AC is connected and cars/tracks are loaded
        if not self._cars_cache or not self._tracks_cache:
            # Try to load cars/tracks if not already loaded
            if self.connector.is_connected():
                cars = self.connector.get_cars()
                tracks = self.connector.get_tracks()
                if cars and tracks:
                    self._cars_cache = cars
                    self._tracks_cache = tracks
                    self.car_track_selector.set_cars(cars)
                    self.car_track_selector.set_tracks(tracks)
                    self.statusbar.showMessage(f"Chargé: {len(cars)} voitures, {len(tracks)} pistes")
            
            # If still empty, show error
            if not self._cars_cache or not self._tracks_cache:
                QMessageBox.warning(
                    self,
                    "Assetto Corsa non connecté",
                    "Impossible de charger les voitures et pistes.\n\n"
                    "Assurez-vous que :\n"
                    "1. Assetto Corsa est installé\n"
                    "2. Le chemin d'installation est configuré dans Paramètres\n\n"
                    "Allez dans Paramètres → Sélectionner le dossier AC"
                )
                return
        
        car = self.car_track_selector.get_selected_car()
        track = self.car_track_selector.get_selected_track()
        
        if not car or not track:
            QMessageBox.warning(
                self,
                "Sélection manquante",
                "Veuillez sélectionner une voiture et une piste dans les listes déroulantes."
            )
            return
        
        # Get current conditions from adaptive panel
        conditions_dict = self.adaptive_panel.get_conditions()
        conditions = TrackConditions(
            temperature=conditions_dict["temperature"],
            track_temp=conditions_dict["track_temp"],
            weather=conditions_dict["weather"]
        )
        
        # Generate base setup
        behavior_id = self.behavior_selector.get_selected_behavior()
        base_setup, _ = self.setup_engine.generate_setup(
            profile=self._current_profile,
            behavior_id=behavior_id,
            car=car,
            track=track
        )
        
        # Apply adaptive adjustments
        adapted_setup = self.adaptive_engine.adapt_setup_to_conditions(
            base_setup, conditions, car, track
        )
        
        # Apply learned optimizations
        optimized_setup = self.adaptive_engine.apply_learned_adjustments(adapted_setup)
        
        # Update current setup
        self._current_setup = optimized_setup
        
        # Save to AC
        success, message, file_path = self.connector.save_setup(
            setup=optimized_setup,
            car_id=car.car_id,
            track_id=track.full_id,
            overwrite=True
        )
        
        if not success:
            QMessageBox.warning(
                self,
                "Erreur de sauvegarde",
                f"Le setup n'a pas pu être sauvegardé.\n\n{message}"
            )
            return
        
        # Get performance stats - use full_id to match what's recorded in _record_lap_data
        stats = self.adaptive_engine.get_performance_stats(car.car_id, track.full_id)
        self.adaptive_panel.update_stats(stats)
        
        # Show success message
        msg = "✅ Setup optimisé par l'IA!\n\n"
        msg += f"🌡️ Conditions appliquées:\n"
        msg += f"  - Température: {conditions.temperature}°C\n"
        msg += f"  - Piste: {conditions.track_temp}°C\n"
        msg += f"  - Météo: {conditions.weather}\n\n"
        
        if stats.get("has_data", False):
            confidence = min(stats['total_laps'] / 50.0 * 100, 100)
            msg += f"🤖 Optimisations IA (confiance: {confidence:.0f}%):\n"
            msg += f"  - Basé sur {stats['total_laps']} tours\n"
            msg += f"  - Meilleur temps: {stats['your_best']:.3f}s\n"
            msg += f"  - Classement: {stats['rank_estimate']}\n"
        else:
            msg += "ℹ️ Pas encore de données d'apprentissage.\n"
            msg += "Roule quelques tours pour que l'IA apprenne!"
        
        QMessageBox.information(
            self,
            "🤖 IA Adaptive",
            msg
        )
        
        self.statusbar.showMessage("🤖 Setup optimisé par l'IA adaptive!")
        
        # Update preview
        self._update_preview()
    
    def _start_telemetry_polling(self) -> None:
        """Start polling telemetry data."""
        self._telemetry_timer = QTimer(self)
        self._telemetry_timer.timeout.connect(self._poll_telemetry)
        self._telemetry_timer.start(50)  # 20Hz for smooth display
    
    def _poll_telemetry(self) -> None:
        """Poll telemetry data from AC shared memory."""
        try:
            live_data = self.shared_memory.get_live_data()
            if not live_data.is_connected:
                return
            if live_data:
                # Update telemetry panel
                # Tire temps are in tyre_temp_core tuple (FL, FR, RL, RR)
                tire_temps = live_data.tyre_temp_core if live_data.tyre_temp_core else (0, 0, 0, 0)
                
                telemetry = TelemetryData(
                    speed_kmh=live_data.speed_kmh,
                    rpm=live_data.rpm,
                    max_rpm=live_data.max_rpm,
                    gear=live_data.gear,
                    tire_temp_fl=tire_temps[0] if len(tire_temps) > 0 else 0,
                    tire_temp_fr=tire_temps[1] if len(tire_temps) > 1 else 0,
                    tire_temp_rl=tire_temps[2] if len(tire_temps) > 2 else 0,
                    tire_temp_rr=tire_temps[3] if len(tire_temps) > 3 else 0,
                    g_lateral=live_data.g_lateral,
                    g_longitudinal=live_data.g_longitudinal,
                    throttle=live_data.gas,
                    brake=live_data.brake,
                    is_connected=True
                )
                self.telemetry_panel.update_telemetry(telemetry)
                
                # Feed data to driving analyzer
                metrics = self.driving_analyzer.add_sample(
                    speed=live_data.speed_kmh,
                    throttle=live_data.gas,
                    brake=live_data.brake,
                    steering=live_data.steer_angle,
                    g_lat=live_data.g_lateral,
                    g_lon=live_data.g_longitudinal
                )
                
                # Update driving style widget if we got new analysis
                if metrics:
                    self.driving_style_widget.update_analysis(metrics, metrics.style, metrics.confidence)
        except Exception:
            pass
    
    def _create_action_bar(self) -> QWidget:
        """Create the bottom action bar."""
        bar = QFrame()
        bar.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(bar)
        
        # Preview button
        preview_btn = QPushButton("👁️ Prévisualiser")
        preview_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 25px;
                border: 1px solid #444;
                border-radius: 6px;
                background-color: #2a2a2a;
                color: #fff;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #333;
                border-color: #2196F3;
            }
        """)
        preview_btn.clicked.connect(self._on_preview_clicked)
        layout.addWidget(preview_btn)
        
        # Reset button
        reset_btn = QPushButton("🔄 Réinitialiser")
        reset_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 25px;
                border: 1px solid #444;
                border-radius: 6px;
                background-color: #2a2a2a;
                color: #fff;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #333;
                border-color: #FF9800;
            }
        """)
        reset_btn.clicked.connect(self._on_reset_clicked)
        layout.addWidget(reset_btn)
        
        layout.addStretch()
        
        # Generate button
        self.generate_btn = QPushButton("⚡ Générer et Appliquer le Setup")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                padding: 15px 40px;
                border: none;
                border-radius: 6px;
                background-color: #4CAF50;
                color: #fff;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #444;
                color: #888;
            }
        """)
        self.generate_btn.clicked.connect(self._on_generate_clicked)
        layout.addWidget(self.generate_btn)
        
        return bar
    
    def _setup_statusbar(self) -> None:
        """Set up the status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        self.statusbar.setStyleSheet("""
            QStatusBar {
                background-color: #1a1a1a;
                color: #888;
            }
        """)
        
        # Add developer credit on the right side
        credit_label = QLabel("Developed by XENONRAy")
        credit_label.setStyleSheet("color: #666; font-size: 11px; padding-right: 10px;")
        self.statusbar.addPermanentWidget(credit_label)
        
        self.statusbar.showMessage("Prêt")
    
    def _apply_dark_theme(self) -> None:
        """Apply dark theme to the application."""
        palette = QPalette()
        
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(42, 42, 42))
        palette.setColor(QPalette.AlternateBase, QColor(50, 50, 50))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(42, 42, 42))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(33, 150, 243))
        palette.setColor(QPalette.Highlight, QColor(33, 150, 243))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        self.setPalette(palette)
    
    def _initialize(self) -> None:
        """Initialize the application after UI is ready."""
        self.statusbar.showMessage("Connexion à Assetto Corsa...")
        
        # Connect to AC (saved path is already loaded in main.py)
        status = self.connector.connect()
        
        if status.is_connected:
            self.connection_label.setText("🟢 Connecté à Assetto Corsa")
            self.connection_label.setStyleSheet("color: #4CAF50;")
            
            # Load cars and tracks
            cars = self.connector.get_cars()
            tracks = self.connector.get_tracks()
            self._cars_cache = cars
            self._tracks_cache = tracks
            
            self.car_track_selector.set_cars(cars)
            self.car_track_selector.set_tracks(tracks)
            
            self.statusbar.showMessage(
                f"Connecté - {status.cars_count} voitures, {status.tracks_count} pistes"
            )
        else:
            self.connection_label.setText("🟠 AC non détecté")
            self.connection_label.setStyleSheet("color: #FF9800;")
            self.statusbar.showMessage("Assetto Corsa non détecté - Allez dans Paramètres pour configurer")
            
            # Show helpful dialog with solution
            result = QMessageBox.question(
                self,
                "Assetto Corsa non détecté",
                "Le dossier d'installation d'Assetto Corsa n'a pas été trouvé automatiquement.\n\n"
                "Voulez-vous sélectionner le dossier manuellement ?\n\n"
                "Cherchez le dossier contenant 'content/cars' et 'content/tracks'\n"
                "(Ex: C:\\Steam\\steamapps\\common\\assettocorsa)",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if result == QMessageBox.Yes:
                self._on_select_ac_folder()
        
        # Load profile
        self._current_profile = self.repository.get_active_profile()
        if self._current_profile:
            self.sliders_panel.set_profile(self._current_profile)
        else:
            self._current_profile = DriverProfile()
        
        # Start AC live polling
        self._start_ac_polling()
        
        # Start telemetry polling for live data
        self._start_telemetry_polling()
    
    def _on_selection_changed(self, car: Optional[Car], track: Optional[Track]) -> None:
        """Handle car/track selection change."""
        self._update_recommendation()
        
        # Update presets panel with selected car
        if car:
            self.presets_panel.set_current_car(car.car_id)
    
    def _on_behavior_changed(self, behavior_id: str) -> None:
        """Handle behavior selection change."""
        self._update_preview()
    
    def _on_profile_changed(self) -> None:
        """Handle profile slider changes."""
        # Get current preferences from sliders and update profile
        prefs = self.sliders_panel.get_preferences()
        # Update recommendation based on new preferences
        self._update_recommendation()
        self._update_preview()
    
    def _update_recommendation(self) -> None:
        """Update AI recommendation based on current profile."""
        if not self._current_profile:
            return
        
        recommended = self.decision_engine.get_quick_recommendation(self._current_profile)
        self.behavior_selector.set_recommendation(recommended, 0.75)
    
    def _update_preview(self) -> None:
        """Update the setup preview."""
        if not self._current_profile:
            return
        
        behavior_id = self.behavior_selector.get_selected_behavior()
        car = self.car_track_selector.get_selected_car()
        track = self.car_track_selector.get_selected_track()
        
        # Generate preview
        preview = self.setup_engine.preview_setup(
            profile=self._current_profile,
            behavior_id=behavior_id,
            car=car,
            track=track
        )
        
        # Update score display
        score = preview["score"]
        confidence = preview["confidence"]
        
        self.score_label.setText(f"{score:.0f}/100")
        self.confidence_label.setText(f"Confiance: {confidence:.0%}")
        
        # Color based on score
        if score >= 80:
            self.score_label.setStyleSheet("color: #4CAF50;")
        elif score >= 60:
            self.score_label.setStyleSheet("color: #2196F3;")
        elif score >= 40:
            self.score_label.setStyleSheet("color: #FF9800;")
        else:
            self.score_label.setStyleSheet("color: #f44336;")
        
        # Update preview text
        key_values = preview["key_values"]
        preview_lines = [
            f"Différentiel Power: {key_values.get('diff_power', 0):.0f}%",
            f"Différentiel Coast: {key_values.get('diff_coast', 0):.0f}%",
            f"Répartition freins: {key_values.get('brake_bias', 0):.0f}%",
            f"Carrossage avant: {key_values.get('front_camber', 0):.1f}°",
            f"Carrossage arrière: {key_values.get('rear_camber', 0):.1f}°",
            f"Barre anti-roulis AV: {key_values.get('front_arb', 0)}",
            f"Barre anti-roulis AR: {key_values.get('rear_arb', 0)}",
        ]
        self.preview_text.setText("\n".join(preview_lines))
        
        # Update notes
        notes = preview.get("notes", [])
        self.notes_text.setText("\n".join(f"• {note}" for note in notes))
    
    def _on_preview_clicked(self) -> None:
        """Handle preview button click."""
        self._update_preview()
        self.statusbar.showMessage("Aperçu mis à jour")
    
    def _on_reset_clicked(self) -> None:
        """Handle reset button click."""
        self.sliders_panel.reset_to_defaults()
        self.behavior_selector.set_selected_behavior("balanced")
        self.statusbar.showMessage("Paramètres réinitialisés")
    
    def _on_generate_clicked(self) -> None:
        """Handle generate button click."""
        print(f"[GENERATE] _cars_cache: {len(self._cars_cache) if self._cars_cache else 0}")
        print(f"[GENERATE] _tracks_cache: {len(self._tracks_cache) if self._tracks_cache else 0}")
        
        # Check if AC is connected and cars/tracks are loaded
        if not self._cars_cache or not self._tracks_cache:
            # Try to load cars/tracks if not already loaded
            print(f"[GENERATE] Caches empty, checking connection...")
            is_conn = self.connector.is_connected()
            print(f"[GENERATE] connector.is_connected(): {is_conn}")
            
            if is_conn:
                print(f"[GENERATE] Loading cars and tracks...")
                cars = self.connector.get_cars()
                tracks = self.connector.get_tracks()
                print(f"[GENERATE] Loaded {len(cars) if cars else 0} cars, {len(tracks) if tracks else 0} tracks")
                
                if cars and tracks:
                    self._cars_cache = cars
                    self._tracks_cache = tracks
                    self.car_track_selector.set_cars(cars)
                    self.car_track_selector.set_tracks(tracks)
                    self.statusbar.showMessage(f"Chargé: {len(cars)} voitures, {len(tracks)} pistes")
                else:
                    print(f"[GENERATE] WARNING: get_cars or get_tracks returned empty!")
            else:
                print(f"[GENERATE] Not connected to AC")
            
            # If still empty, show error
            if not self._cars_cache or not self._tracks_cache:
                status = self.connector.get_status()
                error_details = f"Status: is_connected={status.is_connected}\n"
                error_details += f"Game path: {status.game_path}\n"
                error_details += f"Cars count: {status.cars_count}\n"
                error_details += f"Tracks count: {status.tracks_count}\n"
                print(f"[GENERATE] Error details:\n{error_details}")
                
                QMessageBox.warning(
                    self,
                    "Assetto Corsa non connecté",
                    "Impossible de charger les voitures et pistes.\n\n"
                    "Assurez-vous que :\n"
                    "1. Assetto Corsa est installé\n"
                    "2. Le chemin d'installation est configuré dans Paramètres\n\n"
                    "Allez dans Paramètres → Sélectionner le dossier AC\n\n"
                    f"Debug:\n{error_details}"
                )
                return
        
        # Validate selection
        if not self.car_track_selector.has_valid_selection():
            QMessageBox.warning(
                self,
                "Sélection incomplète",
                "Veuillez sélectionner une voiture et une piste dans les listes déroulantes."
            )
            return
        
        car = self.car_track_selector.get_selected_car()
        track = self.car_track_selector.get_selected_track()
        behavior_id = self.behavior_selector.get_selected_behavior()
        
        # Ask user for setup name
        default_name = f"{behavior_id.title()}_Touge"
        setup_name, ok = QInputDialog.getText(
            self,
            "Nom du Setup",
            "Entrez un nom pour votre setup:",
            text=default_name
        )
        
        if not ok or not setup_name.strip():
            return  # User cancelled
        
        setup_name = setup_name.strip()
        
        self.statusbar.showMessage("Génération du setup...")
        self.generate_btn.setEnabled(False)
        
        try:
            # Generate setup
            setup, score = self.setup_engine.generate_setup(
                profile=self._current_profile,
                behavior_id=behavior_id,
                car=car,
                track=track,
                setup_name=setup_name
            )
            
            self._current_setup = setup
            self._last_score = score
            
            # Save to AC
            success, message, file_path = self.connector.save_setup(
                setup=setup,
                car_id=car.car_id,
                track_id=track.full_id
            )
            
            if success:
                # Save to database
                self.repository.save_setup(
                    setup,
                    profile_id=self._current_profile.profile_id,
                    file_path=str(file_path) if file_path else None
                )
                
                # Save profile
                self.repository.save_profile(self._current_profile)
                
                QMessageBox.information(
                    self,
                    "Setup généré",
                    f"Le setup a été généré et sauvegardé avec succès!\n\n"
                    f"Score: {score.total_score:.0f}/100\n"
                    f"Fichier: {file_path}\n\n"
                    f"Le setup est maintenant disponible dans Assetto Corsa."
                )
                
                self.statusbar.showMessage(f"Setup sauvegardé: {file_path}")
            else:
                QMessageBox.warning(
                    self,
                    "Erreur de sauvegarde",
                    f"Le setup a été généré mais n'a pas pu être sauvegardé.\n\n{message}"
                )
                self.statusbar.showMessage(f"Erreur: {message}")
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Une erreur est survenue lors de la génération du setup.\n\n{str(e)}"
            )
            self.statusbar.showMessage(f"Erreur: {str(e)}")
        
        finally:
            self.generate_btn.setEnabled(True)
    
    def _start_ac_polling(self) -> None:
        """Start polling AC shared memory for live detection."""
        self._ac_polling_timer = QTimer(self)
        self._ac_polling_timer.timeout.connect(self._poll_ac_status)
        self._ac_polling_timer.start(1000)  # Poll every second
        
        self.statusbar.showMessage("Détection automatique activée - Lancez Assetto Corsa")
    
    def _poll_ac_status(self) -> None:
        """Poll AC shared memory for game status and car/track detection."""
        try:
            # Try to connect if not connected
            if not self.shared_memory.is_connected:
                self.shared_memory.connect()
            
            live_data = self.shared_memory.get_live_data()
            
            # Debug logging
            print(f"[DEBUG] is_connected: {live_data.is_connected}")
            print(f"[DEBUG] car_model: '{live_data.car_model}'")
            print(f"[DEBUG] track: '{live_data.track}'")
            print(f"[DEBUG] status: {live_data.status}")
            print(f"[DEBUG] rpm: {live_data.rpm}")
            
            # Check if we're actually in a session:
            # - Must be connected to shared memory
            # - Must have car and track loaded
            # - Either status is LIVE/PAUSE/REPLAY OR we have active telemetry (RPM > 0)
            is_in_session = (
                live_data.is_connected and 
                live_data.car_model and 
                live_data.track and
                (live_data.status in [ACStatus.AC_LIVE, ACStatus.AC_PAUSE, ACStatus.AC_REPLAY] or live_data.rpm > 0)
            )
            
            print(f"[DEBUG] is_in_session: {is_in_session}")
            
            # Check for car/track change FIRST (works in menu or in session)
            if live_data.is_connected and live_data.car_model and live_data.track:
                print(f"[DEBUG] Checking car/track change:")
                print(f"[DEBUG]   Current: car='{live_data.car_model}', track='{live_data.track}'")
                print(f"[DEBUG]   Last: car='{self._last_detected_car}', track='{self._last_detected_track}'")
                print(f"[DEBUG]   Changed? {live_data.car_model != self._last_detected_car or live_data.track != self._last_detected_track}")
                
                if (live_data.car_model != self._last_detected_car or 
                    live_data.track != self._last_detected_track):
                    
                    print(f"[DEBUG] CAR/TRACK CHANGED! Calling _auto_select_car_track...")
                    self._last_detected_car = live_data.car_model
                    self._last_detected_track = live_data.track
                    
                    # Reset track map for new track
                    self._track_map_initialized = False
                    self._last_sector_index = -1
                    
                    # Auto-select in UI
                    self._auto_select_car_track(
                        live_data.car_model, 
                        live_data.track,
                        live_data.track_config
                    )
                else:
                    print(f"[DEBUG] No change detected, skipping auto-select")
            
            if is_in_session:
                # Game is running (live, paused, or replay)
                self._update_game_status(live_data)
                
                # Update track map widget
                self._update_track_map(live_data)
                
                # Record lap data for AI learning
                self._record_lap_data(live_data)
            elif live_data.is_connected and live_data.car_model and live_data.track:
                # Connected, car/track loaded but not in session (menu/loading)
                self.game_status_label.setText(f"🎮 AC: {live_data.car_model[:20]} @ {live_data.track[:20]}")
                self.game_status_label.setStyleSheet("color: #FF9800;")
            elif live_data.is_connected:
                # Connected but no car/track - in main menu
                self.game_status_label.setText("🎮 AC: En menu")
                self.game_status_label.setStyleSheet("color: #FF9800;")
            else:
                # Not connected - disconnect to retry next poll
                if self.shared_memory.is_connected:
                    self.shared_memory.disconnect()
                # Show more helpful message
                self.game_status_label.setText("🎮 En attente de session AC...")
                self.game_status_label.setStyleSheet("color: #888;")
                
        except Exception as e:
            # Disconnect on error to retry next poll
            if self.shared_memory.is_connected:
                self.shared_memory.disconnect()
            self.game_status_label.setText(f"🎮 Erreur: {str(e)[:30]}")
            self.game_status_label.setStyleSheet("color: #F44336;")
    
    def _update_game_status(self, live_data) -> None:
        """Update the game status display."""
        print("[DEBUG] _update_game_status called!")
        status_text = "🎮 "
        
        if live_data.is_in_pit or live_data.is_in_pit_lane:
            status_text += "EN PIT - Setup modifiable"
            self.game_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            status_text += f"EN PISTE - {live_data.speed_kmh:.0f} km/h"
            self.game_status_label.setStyleSheet("color: #2196F3;")
        
        print(f"[DEBUG] Setting status text to: {status_text}")
        self.game_status_label.setText(status_text)
    
    def _update_track_map(self, live_data) -> None:
        """Update the track map widget with live data."""
        # Initialize track map if needed
        if not self._track_map_initialized and live_data.track:
            self.track_map_widget.set_track_name(live_data.track, live_data.track_config)
            self._track_map_initialized = True
        
        # Update lap times
        self.track_map_widget.update_current_lap_time(live_data.current_lap_time_ms)
        self.track_map_widget.update_best_lap_time(live_data.best_lap_time_ms)
        
        # Update delta
        if live_data.best_lap_time_ms > 0 and live_data.current_lap_time_ms > 0:
            delta = live_data.current_lap_time_ms - live_data.best_lap_time_ms
            self.track_map_widget.update_delta(delta)
        
        # Check for sector change to record sector time
        if live_data.current_sector_index != self._last_sector_index:
            # When sector changes, lastSectorTime contains the time for the PREVIOUS sector
            if self._last_sector_index >= 0 and live_data.last_sector_time_ms > 0:
                # Record the completed sector time
                print(f"[DEBUG] Sector {self._last_sector_index} completed: {live_data.last_sector_time_ms}ms")
                self.track_map_widget.update_sector_time(
                    self._last_sector_index,
                    live_data.last_sector_time_ms
                )
            self._last_sector_index = live_data.current_sector_index
            print(f"[DEBUG] Now in sector {live_data.current_sector_index}")
        
        # Update delta (current vs best)
        if live_data.best_lap_time_ms > 0 and live_data.current_lap_time_ms > 0:
            # Simple delta calculation based on position
            expected_time = int(live_data.normalized_car_position * live_data.best_lap_time_ms)
            delta = live_data.current_lap_time_ms - expected_time
            self.track_map_widget.update_delta(delta)
    
    def _record_lap_data(self, live_data) -> None:
        """Record lap data for AI learning.
        
        Supports:
        - Circuit tracks: detection via completedLaps increment
        - Point-to-point tracks with timing: detection via lastTime change
        - Freeroam maps: not supported (no timing data available)
        """
        lap_detected = False
        lap_time_ms = 0
        lap_number = 0
        
        # Initialize tracking attributes
        if not hasattr(self, '_last_recorded_lap_time_ms'):
            self._last_recorded_lap_time_ms = 0
            self._point_to_point_run_count = 0
        
        # Method 1: Standard lap detection via completedLaps (for circuits)
        if live_data.completed_laps > self._last_completed_laps:
            lap_detected = True
            lap_time_ms = live_data.last_lap_time_ms
            lap_number = live_data.completed_laps
            self._last_completed_laps = live_data.completed_laps
            self._last_recorded_lap_time_ms = lap_time_ms
            print(f"[LAP] Circuit lap detected: lap={lap_number}, time={lap_time_ms}ms")
        
        # Method 2: Point-to-point detection via last_lap_time_ms change
        # Works for tracks with start/finish timing (not freeroam)
        elif live_data.last_lap_time_ms > 0 and live_data.last_lap_time_ms != self._last_recorded_lap_time_ms:
            self._point_to_point_run_count += 1
            lap_detected = True
            lap_time_ms = live_data.last_lap_time_ms
            lap_number = self._point_to_point_run_count
            self._last_recorded_lap_time_ms = lap_time_ms
            print(f"[LAP] Point-to-point run detected: run={lap_number}, time={lap_time_ms}ms")
        
        # Record the lap if detected
        if lap_detected and lap_time_ms > 0 and live_data.car_model and live_data.track:
            # Record the lap
            self.adaptive_engine.record_lap(
                car_id=live_data.car_model,
                track_id=live_data.track,
                lap_time=lap_time_ms / 1000.0,  # Convert to seconds
                conditions=self.current_conditions
            )
            
            # Update adaptive panel stats
            stats = self.adaptive_engine.get_performance_stats(
                live_data.car_model,
                live_data.track
            )
            self.adaptive_panel.update_stats(stats)
            
            # Show feedback in status bar with AI progress
            lap_time_str = f"{lap_time_ms / 1000.0:.3f}s"
            total_laps = stats.get('total_laps', 1)
            confidence = min(total_laps / 50.0 * 100, 100)
            
            if total_laps < 3:
                ai_status = f"🧠 IA analyse... ({total_laps}/3 tours min)"
            elif total_laps < 10:
                ai_status = f"🔍 IA apprend ({total_laps} tours)"
            elif total_laps < 25:
                ai_status = f"⚡ IA optimise ({confidence:.0f}% confiance)"
            else:
                ai_status = f"✅ IA prête ({confidence:.0f}% confiance)"
            
            self.statusbar.showMessage(
                f"🏁 Tour/Run {lap_number}: {lap_time_str} | {ai_status}"
            )
            
            print(f"[AI LEARNING] Lap/Run {lap_number} recorded: {lap_time_str} | Confidence: {confidence:.0f}%")
    
    def _on_quick_start_generate(self) -> None:
        """Handle quick start generate button."""
        # Use the auto-detected car and track
        car = self.car_track_selector.get_selected_car()
        track = self.car_track_selector.get_selected_track()
        
        if not car or not track:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Aucune détection",
                "Lance Assetto Corsa et sélectionne une voiture et une piste d'abord."
            )
            return
        
        # Update quick start status
        self.quick_start_widget.set_status("generating")
        
        # Auto-detect driving style from recent data
        metrics = self.driving_analyzer.get_metrics()
        if metrics and metrics.confidence > 0.3:
            # Auto-apply the detected style
            style_to_behavior = {
                "SMOOTH": "safe",
                "BALANCED": "balanced",
                "AGGRESSIVE": "attack",
                "DRIFT": "drift"
            }
            behavior = style_to_behavior.get(metrics.style.name, "balanced")
            self.behavior_selector.set_behavior(behavior)
        
        # Get current conditions from AC if available
        try:
            live_data = self.shared_memory.get_live_data()
            if live_data and live_data.is_connected:
                # Update conditions based on live data
                from ai.adaptive_setup_engine import TrackConditions
                self.current_conditions = TrackConditions(
                    temperature=live_data.ambient_temp if hasattr(live_data, 'ambient_temp') else 25.0,
                    track_temp=live_data.road_temp if hasattr(live_data, 'road_temp') else 30.0,
                    weather="dry"  # AC doesn't provide weather in shared memory
                )
        except:
            pass
        
        # ═══════════════════════════════════════════════════════════
        # V2.1 SETUP GENERATION PIPELINE
        # ═══════════════════════════════════════════════════════════
        
        # Step 1: Get thermal data from AC Monitor V2
        thermal_data = self.ac_monitor_v2.get_thermal_data()
        ambient_temp = thermal_data.get("ambient_temp", 25.0)
        road_temp = thermal_data.get("road_temp", 30.0)
        
        print(f"[V2.1] Thermal data: Ambient={ambient_temp:.1f}°C, Road={road_temp:.1f}°C")
        
        # Step 2: Load enriched car data
        from utils.car_data_loader import load_car_data
        car_data = load_car_data(car.car_id)
        
        # Step 3: Generate setup with V2 engine
        behavior_id = self.behavior_selector.get_selected_behavior()
        base_setup = self.setup_engine_v2.generate_setup(
            car=car,
            track=track,
            behavior_id=behavior_id,
            profile=self._current_profile,
            ambient_temp=ambient_temp,
            road_temp=road_temp
        )
        
        # Step 4: Apply physics refinement (V2.1)
        category = self.setup_engine_v2.classify_car(car)
        targets = CATEGORY_TARGETS.get(category)
        rake_angle = targets.rake_angle if targets else 0.0
        
        # Detect track type
        track_type = "circuit"
        track_name_lower = track.name.lower()
        if "touge" in track_name_lower or "akina" in track_name_lower or "usui" in track_name_lower:
            track_type = "touge"
        elif "street" in track_name_lower or "highway" in track_name_lower:
            track_type = "street"
        
        print(f"[V2.1] Refining: category={category}, rake={rake_angle:.1f}°, track_type={track_type}")
        
        refined_setup = self.physics_refiner.refine(
            setup=base_setup,
            category=category,
            rake_angle=rake_angle,
            track_type=track_type,
            car_data=car_data
        )
        
        # Step 5: Apply adaptive adjustments (optional)
        adapted_setup = self.adaptive_engine.adapt_setup_to_conditions(
            refined_setup, self.current_conditions, car, track
        )
        
        # Step 6: Apply learned optimizations
        optimized_setup = self.adaptive_engine.apply_learned_adjustments(adapted_setup)
        
        # Save and apply
        self._current_setup = optimized_setup
        self.repository.save_setup(optimized_setup)
        
        # Write to AC using connector (correct method with all required args)
        success, message, file_path = self.connector.save_setup(
            setup=optimized_setup,
            car_id=car.car_id,
            track_id=track.full_id,
            overwrite=True
        )
        
        if success:
            self.quick_start_widget.set_status("done")
            self.statusbar.showMessage("🎯 Setup généré et appliqué automatiquement!")
            
            # Show brief success notification
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "✅ Setup Prêt!",
                f"Ton setup a été généré et appliqué!\n\n"
                f"🏎️ {car.name}\n"
                f"🏁 {track.name}\n\n"
                f"Tu peux maintenant rouler!"
            )
        else:
            self.quick_start_widget.set_status("ready", car.name, track.name)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "⚠️ Erreur",
                "Impossible d'écrire le setup. Vérifie que AC est bien installé."
            )
    
    def _auto_select_car_track(self, car_model: str, track: str, track_config: str) -> None:
        """Auto-select car and track in the UI based on live detection."""
        print(f"[DEBUG] _auto_select_car_track called: car={car_model}, track={track}, config={track_config}")
        
        cars = self._cars_cache if self._cars_cache else self.connector.get_cars()
        tracks = self._tracks_cache if self._tracks_cache else self.connector.get_tracks()
        
        print(f"[DEBUG] Cars cache: {len(cars) if cars else 0} cars")
        print(f"[DEBUG] Tracks cache: {len(tracks) if tracks else 0} tracks")

        # If scans are empty, inject fallback entries so selection becomes possible
        if not cars:
            cars = [Car(car_id=car_model, name=car_model)]
            self._cars_cache = cars
            self.car_track_selector.set_cars(cars)

        if not tracks:
            tracks = [Track(track_id=track, name=track, config=track_config)]
            self._tracks_cache = tracks
            self.car_track_selector.set_tracks(tracks)

        # Find and select car
        car_found = False
        print(f"[DEBUG] Searching for car: {car_model}")
        for car in cars:
            if car.car_id == car_model or car_model in car.car_id:
                print(f"[DEBUG] Car found! Setting: {car.car_id}")
                self.car_track_selector.set_selected_car(car.car_id)
                car_found = True
                break

        if not car_found:
            # Add fallback car if not found
            print(f"[DEBUG] Car not found in cache, adding fallback: {car_model}")
            fallback_car = Car(car_id=car_model, name=car_model)
            if not self._cars_cache:
                self._cars_cache = []
            self._cars_cache.append(fallback_car)
            self.car_track_selector.set_cars(self._cars_cache)
            self.car_track_selector.set_selected_car(fallback_car.car_id)
            car_found = True
            print(f"[DEBUG] Fallback car added and selected")

        # Find and select track
        track_found = False
        print(f"[DEBUG] Searching for track: {track}")
        for t in tracks:
            if t.track_id == track or track in t.track_id:
                print(f"[DEBUG] Track found! Setting: {t.track_id}")
                self.car_track_selector.set_selected_track(t.track_id, track_config)
                track_found = True
                break

        if not track_found:
            # Add fallback track if not found
            print(f"[DEBUG] Track not found in cache, adding fallback: {track}")
            fallback_track = Track(track_id=track, name=track, config=track_config)
            if not self._tracks_cache:
                self._tracks_cache = []
            self._tracks_cache.append(fallback_track)
            self.car_track_selector.set_tracks(self._tracks_cache)
            self.car_track_selector.set_selected_track(fallback_track.track_id, track_config)
            track_found = True
            print(f"[DEBUG] Fallback track added and selected")
        
        # Notify user and update Quick Start widget
        print(f"[DEBUG] car_found={car_found}, track_found={track_found}")
        if car_found and track_found:
            print(f"[DEBUG] Both found! Updating UI...")
            self.statusbar.showMessage(
                f"🎯 Détection auto: {car_model} sur {track}"
            )
            self._update_preview()
            
            # Update Quick Start widget to ready state
            car_obj = self.car_track_selector.get_selected_car()
            track_obj = self.car_track_selector.get_selected_track()
            print(f"[DEBUG] car_obj={car_obj}, track_obj={track_obj}")
            if car_obj and track_obj:
                print(f"[DEBUG] Updating Quick Start widget: {car_obj.name} @ {track_obj.name}")
                self.quick_start_widget.set_status("ready", car_obj.name, track_obj.name)
            else:
                print(f"[DEBUG] WARNING: car_obj or track_obj is None!")
            
            # Switch to Quick Start tab automatically for easy access
            self.right_tabs.setCurrentIndex(0)
            print(f"[DEBUG] Switched to Quick Start tab")
        elif car_found or track_found:
            print(f"[DEBUG] Partial detection")
            self.statusbar.showMessage(
                f"⚠️ Détection partielle: {car_model} / {track}"
            )
            self.quick_start_widget.set_status("detecting")
        else:
            print(f"[DEBUG] ERROR: Neither car nor track found!")
    
    def closeEvent(self, event) -> None:
        """Handle window close."""
        # Stop polling timer
        if self._ac_polling_timer:
            self._ac_polling_timer.stop()
        
        # Disconnect shared memory
        self.shared_memory.disconnect()
        
        # Save current profile
        if self._current_profile:
            self.repository.save_profile(self._current_profile)
        
        # Close database
        self.repository.close()
        
        event.accept()
