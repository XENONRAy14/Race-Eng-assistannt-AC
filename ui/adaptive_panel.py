"""
Adaptive Setup Panel - Pro Racing Style
Professional UX design with clear hierarchy and structure.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QSlider, QComboBox, QProgressBar, QScrollArea
)
from PySide6.QtCore import Qt, Signal


class AdaptivePanel(QWidget):
    """Main adaptive setup panel - Professional racing style."""
    
    apply_optimization = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI with professional design."""
        self.setStyleSheet("background: #0d0d0d;")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #1a1a1a;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #ff0000;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)
        
        # Content widget
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 20)
        content_layout.setSpacing(24)
        
        # ═══════════════════════════════════════════════════════════
        # SECTION 1: CONDITIONS
        # ═══════════════════════════════════════════════════════════
        conditions_card = self._create_card("TRACK CONDITIONS")
        conditions_layout = QVBoxLayout()
        conditions_layout.setSpacing(20)
        
        # Air Temperature
        air_container = QVBoxLayout()
        air_container.setSpacing(8)
        
        air_header = QHBoxLayout()
        air_label = QLabel("Air Temperature")
        air_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        air_header.addWidget(air_label)
        air_header.addStretch()
        self.temp_value = QLabel("25°C")
        self.temp_value.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold;")
        air_header.addWidget(self.temp_value)
        air_container.addLayout(air_header)
        
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(0, 50)
        self.temp_slider.setValue(25)
        self.temp_slider.setFixedHeight(24)
        self.temp_slider.setStyleSheet(self._get_slider_style())
        self.temp_slider.valueChanged.connect(lambda v: self.temp_value.setText(f"{v}°C"))
        air_container.addWidget(self.temp_slider)
        
        conditions_layout.addLayout(air_container)
        
        # Track Temperature
        track_container = QVBoxLayout()
        track_container.setSpacing(8)
        
        track_header = QHBoxLayout()
        track_label = QLabel("Track Temperature")
        track_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        track_header.addWidget(track_label)
        track_header.addStretch()
        self.track_temp_value = QLabel("30°C")
        self.track_temp_value.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold;")
        track_header.addWidget(self.track_temp_value)
        track_container.addLayout(track_header)
        
        self.track_temp_slider = QSlider(Qt.Horizontal)
        self.track_temp_slider.setRange(10, 60)
        self.track_temp_slider.setValue(30)
        self.track_temp_slider.setFixedHeight(24)
        self.track_temp_slider.setStyleSheet(self._get_slider_style())
        self.track_temp_slider.valueChanged.connect(lambda v: self.track_temp_value.setText(f"{v}°C"))
        track_container.addWidget(self.track_temp_slider)
        
        conditions_layout.addLayout(track_container)
        
        # Weather
        weather_container = QHBoxLayout()
        weather_container.setSpacing(16)
        
        weather_label = QLabel("Weather")
        weather_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        weather_container.addWidget(weather_label)
        weather_container.addStretch()
        
        self.weather_combo = QComboBox()
        self.weather_combo.addItems(["☀️ Dry", "🌥️ Damp", "🌧️ Wet", "⛈️ Rain"])
        self.weather_combo.setFixedWidth(120)
        self.weather_combo.setStyleSheet("""
            QComboBox {
                background: #1a1a1a;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: bold;
            }
            QComboBox:hover {
                border-color: #ff0000;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #ff0000;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background: #1a1a1a;
                color: #ffffff;
                selection-background-color: #ff0000;
                border: 1px solid #333333;
                outline: none;
            }
        """)
        weather_container.addWidget(self.weather_combo)
        
        conditions_layout.addLayout(weather_container)
        
        conditions_card.layout().addLayout(conditions_layout)
        content_layout.addWidget(conditions_card)
        
        # ═══════════════════════════════════════════════════════════
        # SECTION 2: AI LEARNING
        # ═══════════════════════════════════════════════════════════
        learning_card = self._create_card("AI LEARNING")
        learning_layout = QVBoxLayout()
        learning_layout.setSpacing(16)
        
        # Stats grid - 2 columns
        stats_row1 = QHBoxLayout()
        stats_row1.setSpacing(20)
        
        # Laps recorded
        laps_box = self._create_stat_box("LAPS RECORDED", "0", "#ffffff")
        self.laps_value = laps_box["value_label"]
        stats_row1.addWidget(laps_box["widget"])
        
        # Best time
        best_box = self._create_stat_box("BEST TIME", "--", "#00ff00")
        self.best_time_value = best_box["value_label"]
        stats_row1.addWidget(best_box["widget"])
        
        learning_layout.addLayout(stats_row1)
        
        stats_row2 = QHBoxLayout()
        stats_row2.setSpacing(20)
        
        # Consistency
        cons_box = self._create_stat_box("CONSISTENCY", "--", "#ffffff")
        self.consistency_value = cons_box["value_label"]
        stats_row2.addWidget(cons_box["widget"])
        
        # Confidence
        conf_box = self._create_stat_box("CONFIDENCE", "0%", "#ff0000")
        self.confidence_value = conf_box["value_label"]
        stats_row2.addWidget(conf_box["widget"])
        
        learning_layout.addLayout(stats_row2)
        
        # Confidence progress bar
        conf_bar_container = QVBoxLayout()
        conf_bar_container.setSpacing(6)
        
        conf_bar_label = QLabel("AI Learning Progress")
        conf_bar_label.setStyleSheet("color: #666666; font-size: 11px;")
        conf_bar_container.addWidget(conf_bar_label)
        
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setRange(0, 100)
        self.confidence_bar.setValue(0)
        self.confidence_bar.setTextVisible(False)
        self.confidence_bar.setFixedHeight(8)
        self.confidence_bar.setStyleSheet("""
            QProgressBar {
                background: #1a1a1a;
                border: none;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #cc0000, stop:1 #ff0000);
                border-radius: 4px;
            }
        """)
        conf_bar_container.addWidget(self.confidence_bar)
        
        learning_layout.addLayout(conf_bar_container)
        
        # Status message
        self.status_label = QLabel("⏳ Waiting for lap data...")
        self.status_label.setStyleSheet("""
            color: #888888;
            font-size: 12px;
            padding: 10px 12px;
            background: #141414;
            border-radius: 6px;
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        learning_layout.addWidget(self.status_label)
        
        learning_card.layout().addLayout(learning_layout)
        content_layout.addWidget(learning_card)
        
        # ═══════════════════════════════════════════════════════════
        # SECTION 3: PERFORMANCE
        # ═══════════════════════════════════════════════════════════
        perf_card = self._create_card("PERFORMANCE")
        perf_layout = QVBoxLayout()
        perf_layout.setSpacing(8)
        
        self.rank_label = QLabel("--")
        self.rank_label.setStyleSheet("""
            color: #ffffff;
            font-size: 32px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        self.rank_label.setAlignment(Qt.AlignCenter)
        perf_layout.addWidget(self.rank_label)
        
        self.comparison_label = QLabel("Complete laps to see your ranking")
        self.comparison_label.setStyleSheet("color: #666666; font-size: 12px;")
        self.comparison_label.setAlignment(Qt.AlignCenter)
        self.comparison_label.setWordWrap(True)
        perf_layout.addWidget(self.comparison_label)
        
        perf_card.layout().addLayout(perf_layout)
        content_layout.addWidget(perf_card)
        
        # Spacer
        content_layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # ═══════════════════════════════════════════════════════════
        # APPLY BUTTON (Fixed at bottom)
        # ═══════════════════════════════════════════════════════════
        button_container = QFrame()
        button_container.setStyleSheet("""
            QFrame {
                background: #0d0d0d;
                border-top: 1px solid #1a1a1a;
            }
        """)
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(24, 16, 24, 16)
        
        self.apply_button = QPushButton("⚡ APPLY AI OPTIMIZATION")
        self.apply_button.clicked.connect(self.apply_optimization.emit)
        self.apply_button.setFixedHeight(48)
        self.apply_button.setCursor(Qt.PointingHandCursor)
        self.apply_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff0000, stop:1 #cc0000);
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff3333, stop:1 #ff0000);
            }
            QPushButton:pressed {
                background: #990000;
            }
        """)
        button_layout.addWidget(self.apply_button)
        
        main_layout.addWidget(button_container)
    
    def _create_card(self, title: str) -> QFrame:
        """Create a card container with title."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #111111;
                border: 1px solid #1a1a1a;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(16)
        
        # Title with red accent
        title_container = QHBoxLayout()
        title_container.setSpacing(10)
        
        accent = QFrame()
        accent.setFixedSize(3, 16)
        accent.setStyleSheet("background: #ff0000; border-radius: 1px;")
        title_container.addWidget(accent)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        title_container.addWidget(title_label)
        title_container.addStretch()
        
        layout.addLayout(title_container)
        
        return card
    
    def _create_stat_box(self, label: str, value: str, color: str) -> dict:
        """Create a stat display box."""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background: #0d0d0d;
                border: 1px solid #1a1a1a;
                border-radius: 6px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: #666666; font-size: 10px; letter-spacing: 1px;")
        layout.addWidget(label_widget)
        
        value_widget = QLabel(value)
        value_widget.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")
        layout.addWidget(value_widget)
        
        return {"widget": widget, "value_label": value_widget}
    
    def _get_slider_style(self) -> str:
        """Get consistent slider style."""
        return """
            QSlider::groove:horizontal {
                background: #1a1a1a;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ff0000;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #ff3333;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #cc0000, stop:1 #ff0000);
                border-radius: 3px;
            }
        """
    
    def get_conditions(self) -> dict:
        """Get current track conditions."""
        weather_map = {0: "dry", 1: "light_rain", 2: "wet", 3: "heavy_rain"}
        return {
            "temperature": self.temp_slider.value(),
            "track_temp": self.track_temp_slider.value(),
            "weather": weather_map.get(self.weather_combo.currentIndex(), "dry")
        }
    
    def update_stats(self, stats: dict):
        """Update learning statistics display."""
        if not stats.get("has_data", False):
            self.laps_value.setText("0")
            self.best_time_value.setText("--")
            self.consistency_value.setText("--")
            self.confidence_bar.setValue(0)
            self.confidence_value.setText("0%")
            self.status_label.setText("⏳ Waiting for lap data...")
            self.status_label.setStyleSheet("""
                color: #888888;
                font-size: 12px;
                padding: 10px 12px;
                background: #141414;
                border-radius: 6px;
            """)
            self.rank_label.setText("--")
            self.comparison_label.setText("Complete laps to see your ranking")
            return
        
        total_laps = stats['total_laps']
        confidence = min(total_laps / 50.0 * 100, 100)
        
        self.laps_value.setText(str(total_laps))
        self.best_time_value.setText(f"{stats['your_best']:.3f}s")
        self.consistency_value.setText(f"±{stats['consistency']:.2f}s")
        self.confidence_bar.setValue(int(confidence))
        self.confidence_value.setText(f"{int(confidence)}%")
        
        # Status message with colors
        if total_laps < 3:
            self.status_label.setText(f"🔍 Analyzing... ({total_laps}/3 laps minimum)")
            self.status_label.setStyleSheet("""
                color: #ffaa00;
                font-size: 12px;
                padding: 10px 12px;
                background: rgba(255, 170, 0, 0.1);
                border-radius: 6px;
            """)
        elif total_laps < 10:
            self.status_label.setText(f"🧠 Learning your driving style...")
            self.status_label.setStyleSheet("""
                color: #00aaff;
                font-size: 12px;
                padding: 10px 12px;
                background: rgba(0, 170, 255, 0.1);
                border-radius: 6px;
            """)
        elif total_laps < 25:
            self.status_label.setText(f"⚡ Optimizing setup... ({int(confidence)}% confidence)")
            self.status_label.setStyleSheet("""
                color: #00ff88;
                font-size: 12px;
                padding: 10px 12px;
                background: rgba(0, 255, 136, 0.1);
                border-radius: 6px;
            """)
        else:
            self.status_label.setText(f"✅ AI Ready - {total_laps} laps analyzed")
            self.status_label.setStyleSheet("""
                color: #00ff00;
                font-size: 12px;
                font-weight: bold;
                padding: 10px 12px;
                background: rgba(0, 255, 0, 0.1);
                border-radius: 6px;
            """)
        
        # Performance ranking
        rank = stats.get("rank_estimate", "--")
        percentile = stats.get("percentile", 0)
        self.rank_label.setText(f"🏆 {rank}")
        if percentile > 0:
            self.comparison_label.setText(f"You're faster than {percentile:.0f}% of drivers")
