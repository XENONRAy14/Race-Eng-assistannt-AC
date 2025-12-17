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

from models.driver_profile import DriverProfile
from models.setup import Setup
from models.car import Car
from models.track import Track

from core.setup_engine import SetupEngine
from ai.decision_engine import DecisionEngine
from ai.driving_analyzer import DrivingAnalyzer
from assetto.ac_connector import ACConnector
from assetto.ac_shared_memory import ACSharedMemory, ACStatus
from data.setup_repository import SetupRepository
from config.user_settings import get_user_settings


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
        self.connector = ACConnector()
        self.setup_engine = SetupEngine()
        self.decision_engine = DecisionEngine(self.setup_engine)
        self.shared_memory = ACSharedMemory()
        self.driving_analyzer = DrivingAnalyzer()
        
        # State
        self._current_profile: Optional[DriverProfile] = None
        self._current_setup: Optional[Setup] = None
        self._last_score = None
        self._ac_polling_timer: Optional[QTimer] = None
        self._telemetry_timer: Optional[QTimer] = None
        self._last_detected_car: str = ""
        self._last_detected_track: str = ""
        self._cars_cache: list[Car] = []
        self._tracks_cache: list[Track] = []
        
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
                background-color: #1a1a1a;
                color: #fff;
            }
            QMenuBar::item:selected {
                background-color: #333;
            }
            QMenu {
                background-color: #2a2a2a;
                color: #fff;
                border: 1px solid #444;
            }
            QMenu::item:selected {
                background-color: #2196F3;
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
        folder = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier d'installation Assetto Corsa",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if not folder:
            return
        
        folder_path = Path(folder)
        
        # Validate it's an AC folder
        if not (folder_path / "AssettoCorsa.exe").exists() and not (folder_path / "content").exists():
            QMessageBox.warning(
                self,
                "Dossier invalide",
                "Ce dossier ne semble pas être une installation Assetto Corsa valide.\n\n"
                "Cherchez le dossier contenant 'AssettoCorsa.exe' ou le dossier 'content'."
            )
            return
        
        # Update detector with custom path
        if self.connector.detector._installation is None:
            from assetto.ac_detector import ACInstallation
            # Find documents path
            docs_path = Path.home() / "Documents" / "Assetto Corsa"
            if not docs_path.exists():
                docs_path.mkdir(parents=True, exist_ok=True)
            self.connector.detector._installation = ACInstallation(documents_path=docs_path)
            # Setup writer needs the setups path
            self.connector.writer.set_base_path(docs_path / "setups")
        
        self.connector.detector._installation.game_path = folder_path
        self.connector.detector._installation.cars_path = folder_path / "content" / "cars"
        self.connector.detector._installation.tracks_path = folder_path / "content" / "tracks"
        self.connector.detector._installation.is_valid = True
        self.connector.detector._installation.can_write_setups = True
        
        # Save the path for next launch
        user_settings = get_user_settings()
        user_settings.set_ac_game_path(folder_path)
        
        # Update connection status in UI
        self.connection_label.setText("🟢 Connecté à Assetto Corsa")
        self.connection_label.setStyleSheet("color: #4CAF50;")
        
        # Refresh content
        self._on_refresh_content()
        
        QMessageBox.information(
            self,
            "Dossier AC configuré",
            f"Dossier Assetto Corsa configuré:\n{folder_path}\n\n"
            f"Les voitures et pistes ont été rechargées.\n"
            f"Ce chemin sera mémorisé pour les prochains lancements."
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
        
        # Tab 1: Setup Preview (original)
        setup_tab = self._create_setup_preview_tab()
        self.right_tabs.addTab(setup_tab, "📊 Setup")
        
        # Tab 2: Live Telemetry
        self.telemetry_panel = TelemetryPanel()
        self.right_tabs.addTab(self.telemetry_panel, "📡 Télémétrie")
        
        # Tab 3: Driving Analysis
        self.driving_style_widget = DrivingStyleWidget()
        self.driving_style_widget.apply_recommendation.connect(self._on_apply_style_recommendation)
        self.right_tabs.addTab(self.driving_style_widget, "🧠 Analyse")
        
        # Tab 4: Presets
        self.presets_panel = PresetsPanel()
        self.presets_panel.preset_loaded.connect(self._on_preset_loaded)
        self.right_tabs.addTab(self.presets_panel, "⭐ Presets")
        
        layout.addWidget(self.right_tabs)
        
        return panel
    
    def _create_setup_preview_tab(self) -> QWidget:
        """Create the setup preview tab content."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Score display
        score_group = QGroupBox("Score IA")
        score_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        score_layout = QVBoxLayout(score_group)
        
        self.score_label = QLabel("--/100")
        self.score_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setStyleSheet("color: #2196F3;")
        score_layout.addWidget(self.score_label)
        
        self.confidence_label = QLabel("Confiance: --%")
        self.confidence_label.setAlignment(Qt.AlignCenter)
        self.confidence_label.setStyleSheet("color: #888;")
        score_layout.addWidget(self.confidence_label)
        
        layout.addWidget(score_group)
        
        # Setup preview
        preview_group = QGroupBox("Valeurs clés")
        preview_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                color: #fff;
                border: none;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """)
        self.preview_text.setMaximumHeight(200)
        preview_layout.addWidget(self.preview_text)
        
        layout.addWidget(preview_group)
        
        # AI Notes
        notes_group = QGroupBox("Notes IA")
        notes_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)
        self.notes_text.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                color: #888;
                border: none;
                font-size: 11px;
            }
        """)
        self.notes_text.setMaximumHeight(120)
        notes_layout.addWidget(self.notes_text)
        
        layout.addWidget(notes_group)
        
        layout.addStretch()
        
        return tab
    
    def _on_apply_style_recommendation(self, behavior: str) -> None:
        """Apply the recommended behavior from driving analysis."""
        self.behavior_selector.set_behavior(behavior)
        self._on_behavior_changed(behavior)
        self.statusbar.showMessage(f"✨ Mode '{behavior}' appliqué selon ton style de conduite!")
    
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
        self.statusbar.showMessage(f"⭐ Preset '{preset.name}' chargé!")
    
    def _start_telemetry_polling(self) -> None:
        """Start polling telemetry data from AC."""
        if self._telemetry_timer is None:
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
                    self.driving_style_widget.update_metrics(metrics)
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
            self.presets_panel.set_current_car(car.car_id, car.name)
    
    def _on_behavior_changed(self, behavior_id: str) -> None:
        """Handle behavior selection change."""
        self._update_preview()
    
    def _on_profile_changed(self, profile: DriverProfile) -> None:
        """Handle profile slider changes."""
        self._current_profile = profile
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
        # Validate selection
        if not self.car_track_selector.has_valid_selection():
            QMessageBox.warning(
                self,
                "Sélection incomplète",
                "Veuillez sélectionner une voiture et une piste."
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
            
            if live_data.is_connected and live_data.status in [ACStatus.AC_LIVE, ACStatus.AC_PAUSE, ACStatus.AC_REPLAY]:
                # Game is running (live, paused, or replay)
                self._update_game_status(live_data)
                
                # Check for car/track change
                if live_data.car_model and live_data.track:
                    if (live_data.car_model != self._last_detected_car or 
                        live_data.track != self._last_detected_track):
                        
                        self._last_detected_car = live_data.car_model
                        self._last_detected_track = live_data.track
                        
                        # Auto-select in UI
                        self._auto_select_car_track(
                            live_data.car_model, 
                            live_data.track,
                            live_data.track_config
                        )
            elif live_data.is_connected and live_data.status == ACStatus.AC_OFF:
                # Connected but game in menu/loading
                self.game_status_label.setText("🎮 AC: En menu")
                self.game_status_label.setStyleSheet("color: #FF9800;")
            elif live_data.is_connected:
                # Connected but unknown status - still show as connected
                self.game_status_label.setText("🎮 AC: Connecté")
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
        status_text = "🎮 "
        
        if live_data.is_in_pit or live_data.is_in_pit_lane:
            status_text += "EN PIT - Setup modifiable"
            self.game_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            status_text += f"EN PISTE - {live_data.speed_kmh:.0f} km/h"
            self.game_status_label.setStyleSheet("color: #2196F3;")
        
        self.game_status_label.setText(status_text)
    
    def _auto_select_car_track(self, car_model: str, track: str, track_config: str) -> None:
        """Auto-select car and track in the UI based on live detection."""
        cars = self._cars_cache if self._cars_cache else self.connector.get_cars()
        tracks = self._tracks_cache if self._tracks_cache else self.connector.get_tracks()

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
        for car in cars:
            if car.car_id == car_model or car_model in car.car_id:
                self.car_track_selector.set_selected_car(car.car_id)
                car_found = True
                break

        if not car_found:
            # Add fallback car if not found
            fallback_car = Car(car_id=car_model, name=car_model)
            self._cars_cache.append(fallback_car)
            self.car_track_selector.set_cars(self._cars_cache)
            self.car_track_selector.set_selected_car(fallback_car.car_id)
            car_found = True

        # Find and select track
        track_found = False
        for t in tracks:
            if t.track_id == track or track in t.track_id:
                self.car_track_selector.set_selected_track(t.track_id, track_config)
                track_found = True
                break

        if not track_found:
            # Add fallback track if not found
            fallback_track = Track(track_id=track, name=track, config=track_config)
            self._tracks_cache.append(fallback_track)
            self.car_track_selector.set_tracks(self._tracks_cache)
            self.car_track_selector.set_selected_track(fallback_track.track_id, track_config)
            track_found = True
        
        # Notify user
        if car_found and track_found:
            self.statusbar.showMessage(
                f"🎯 Détection auto: {car_model} sur {track}"
            )
            self._update_preview()
            
            # Show notification
            QMessageBox.information(
                self,
                "Détection automatique",
                f"Voiture et piste détectées automatiquement!\n\n"
                f"Voiture: {car_model}\n"
                f"Piste: {track}\n\n"
                f"Vous pouvez maintenant générer un setup."
            )
        elif car_found or track_found:
            self.statusbar.showMessage(
                f"⚠️ Détection partielle: {car_model} / {track}"
            )
    
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
