"""
Initial D Style - Black and Red gradient theme for entire application.
"""

INITIAL_D_STYLESHEET = """
/* Global Application Style - Initial D Black/Red */

QMainWindow, QWidget {
    background-color: #0a0a0a;
    color: #ffffff;
    font-family: 'Arial', sans-serif;
}

/* Tabs */
QTabWidget::pane {
    border: 2px solid #ff0000;
    border-radius: 8px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a0000, stop:1 #000000);
}

QTabBar::tab {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a0000, stop:1 #000000);
    border: 2px solid #ff0000;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 20px;
    margin-right: 2px;
    color: #888888;
    font-weight: bold;
    font-size: 13px;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ff0000, stop:1 #8a0000);
    color: #ffffff;
    border-bottom: 2px solid #ff0000;
}

QTabBar::tab:hover:!selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #330000, stop:1 #000000);
    color: #ff0000;
}

/* Buttons */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ff0000, stop:1 #8a0000);
    border: 2px solid #ff0000;
    border-radius: 8px;
    color: #ffffff;
    font-weight: bold;
    font-size: 13px;
    padding: 10px 20px;
    min-height: 30px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ff3333, stop:1 #aa0000);
    border: 2px solid #ff3333;
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #cc0000, stop:1 #660000);
}

QPushButton:disabled {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #333333, stop:1 #1a1a1a);
    border: 2px solid #444444;
    color: #666666;
}

/* Input fields */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #1a1a1a;
    border: 2px solid #ff0000;
    border-radius: 6px;
    color: #ffffff;
    padding: 8px;
    font-size: 13px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #ff3333;
    background-color: #2a0000;
}

QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: #0a0a0a;
    border: 2px solid #444444;
    color: #666666;
}

/* ComboBox dropdown */
QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 8px solid #ff0000;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #1a1a1a;
    border: 2px solid #ff0000;
    selection-background-color: #ff0000;
    selection-color: #ffffff;
    color: #ffffff;
}

/* Sliders */
QSlider::groove:horizontal {
    border: 1px solid #ff0000;
    height: 8px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a0000, stop:1 #000000);
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ff0000, stop:1 #8a0000);
    border: 2px solid #ff0000;
    width: 18px;
    margin: -5px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ff3333, stop:1 #aa0000);
}

/* Group boxes */
QGroupBox {
    border: 2px solid #ff0000;
    border-radius: 8px;
    margin-top: 15px;
    padding-top: 20px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a0000, stop:1 #000000);
    font-weight: bold;
    font-size: 14px;
    color: #ff0000;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 8px;
    background-color: #000000;
}

/* Labels */
QLabel {
    color: #ffffff;
    background: transparent;
}

/* Scroll bars */
QScrollBar:vertical {
    border: 1px solid #ff0000;
    background: #1a1a1a;
    width: 15px;
    border-radius: 7px;
}

QScrollBar::handle:vertical {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ff0000, stop:1 #8a0000);
    min-height: 20px;
    border-radius: 7px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: 1px solid #ff0000;
    background: #1a1a1a;
    height: 15px;
    border-radius: 7px;
}

QScrollBar::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ff0000, stop:1 #8a0000);
    min-width: 20px;
    border-radius: 7px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Frames */
QFrame {
    border-radius: 8px;
}

/* Menu bar */
QMenuBar {
    background-color: #0a0a0a;
    border-bottom: 2px solid #ff0000;
    color: #ffffff;
}

QMenuBar::item {
    background: transparent;
    padding: 8px 15px;
}

QMenuBar::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ff0000, stop:1 #8a0000);
}

QMenu {
    background-color: #1a1a1a;
    border: 2px solid #ff0000;
    color: #ffffff;
}

QMenu::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ff0000, stop:1 #8a0000);
}

/* Status bar */
QStatusBar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a0000, stop:1 #000000);
    border-top: 2px solid #ff0000;
    color: #ffffff;
}

/* Progress bar */
QProgressBar {
    border: 2px solid #ff0000;
    border-radius: 8px;
    text-align: center;
    background-color: #1a1a1a;
    color: #ffffff;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ff0000, stop:1 #8a0000);
    border-radius: 6px;
}

/* Tooltips */
QToolTip {
    background-color: #1a1a1a;
    border: 2px solid #ff0000;
    color: #ffffff;
    padding: 5px;
    border-radius: 4px;
}

/* Check boxes and radio buttons */
QCheckBox, QRadioButton {
    color: #ffffff;
    spacing: 8px;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #ff0000;
    border-radius: 4px;
    background-color: #1a1a1a;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #ff0000, stop:1 #8a0000);
}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border: 2px solid #ff3333;
}

/* Text edit */
QTextEdit, QPlainTextEdit {
    background-color: #1a1a1a;
    border: 2px solid #ff0000;
    border-radius: 6px;
    color: #ffffff;
    padding: 8px;
}

/* Scroll area */
QScrollArea {
    border: none;
    background: transparent;
}

/* List widget */
QListWidget {
    background-color: #1a1a1a;
    border: 2px solid #ff0000;
    border-radius: 6px;
    color: #ffffff;
}

QListWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ff0000, stop:1 #8a0000);
}

QListWidget::item:hover {
    background: #2a0000;
}

/* Table widget */
QTableWidget {
    background-color: #1a1a1a;
    border: 2px solid #ff0000;
    border-radius: 6px;
    color: #ffffff;
    gridline-color: #ff0000;
}

QTableWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ff0000, stop:1 #8a0000);
}

QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a0000, stop:1 #000000);
    border: 1px solid #ff0000;
    color: #ff0000;
    padding: 5px;
    font-weight: bold;
}
"""

def apply_initial_d_style(app):
    """Apply Initial D black/red gradient style to the entire application."""
    app.setStyleSheet(INITIAL_D_STYLESHEET)
