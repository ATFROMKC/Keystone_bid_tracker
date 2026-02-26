"""
Keystone Bid Tracker - Dark Theme
Complete QSS stylesheet and color constants for a polished, professional UI.
"""

COLORS = {
    "background":       "#1a1a1a",
    "surface":          "#2a2a2a",
    "border":           "#3a3a3a",
    "text_primary":     "#f0f0f0",
    "text_secondary":   "#999999",
    "accent":           "#4a9eff",
    "accent_hover":     "#3a8eef",
    "accent_pressed":   "#2a7edf",
    "success":          "#4caf50",
    "error":            "#f44336",
    "warning":          "#ff9800",
    "muted":            "#666666",
    "input_bg":         "#333333",
    "row_alt":          "#242424",
    "hover_row":        "#2e3a4a",
    "selected_row":     "#1e3a5a",
}

STATUS_COLORS = {
    "PENDING": {"bg": "#1a3a5c", "fg": "#4a9eff"},
    "BIDDING": {"bg": "#3a2a00", "fg": "#ff9800"},
    "WON":     {"bg": "#1a3a1a", "fg": "#4caf50"},
}


def get_status_style(status: str) -> str:
    """Return inline QSS for a status pill QLabel."""
    colors = STATUS_COLORS.get(status, STATUS_COLORS["PENDING"])
    return (
        f"background-color: {colors['bg']};"
        f"color: {colors['fg']};"
        "border-radius: 8px;"
        "padding: 3px 12px;"
        "font-size: 11px;"
        "font-weight: 600;"
    )


def get_status_badge_html(status: str) -> str:
    """Return an HTML snippet for rendering a status badge inside a QLabel with rich text."""
    colors = STATUS_COLORS.get(status, STATUS_COLORS["PENDING"])
    return (
        f'<span style="background-color:{colors["bg"]}; color:{colors["fg"]}; '
        f'border-radius:8px; padding:2px 10px; font-size:11px; font-weight:600;">'
        f'{status}</span>'
    )


DARK_THEME = """
/* ============================================================
   GLOBAL
   ============================================================ */
* {
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 13px;
    color: #f0f0f0;
}

QMainWindow, QDialog {
    background-color: #1a1a1a;
}

QWidget {
    background-color: transparent;
}

/* ============================================================
   TAB WIDGET
   ============================================================ */
QTabWidget::pane {
    border: 1px solid #3a3a3a;
    background-color: #1a1a1a;
    border-radius: 0px;
    top: -1px;
}

QTabBar {
    background-color: #1a1a1a;
}

QTabBar::tab {
    background-color: #1a1a1a;
    color: #999999;
    padding: 10px 28px;
    margin-right: 0px;
    border: none;
    border-right: 1px solid #3a3a3a;
    border-bottom: 2px solid transparent;
    font-weight: 500;
    font-size: 13px;
    min-width: 70px;
}

QTabBar::tab:selected {
    color: #4a9eff;
    border-bottom: 2px solid #4a9eff;
}

QTabBar::tab:hover:!selected {
    color: #f0f0f0;
    border-bottom: 2px solid #3a3a3a;
}

/* ============================================================
   TABLE WIDGET
   ============================================================ */
QTableWidget, QTableView {
    background-color: #1a1a1a;
    alternate-background-color: #242424;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    gridline-color: #2a2a2a;
    selection-background-color: #1e3a5a;
    selection-color: #f0f0f0;
    outline: none;
}

QTableWidget::item, QTableView::item {
    padding: 6px 10px;
    border: none;
}

QTableWidget::item:hover, QTableView::item:hover {
    background-color: #2e3a4a;
}

QTableWidget::item:selected, QTableView::item:selected {
    background-color: #1e3a5a;
    color: #f0f0f0;
}

QHeaderView {
    background-color: #1a1a1a;
    border: none;
}

QHeaderView::section {
    background-color: #222222;
    color: #999999;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #3a3a3a;
    border-right: 1px solid #2a2a2a;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
}

QHeaderView::section:hover {
    background-color: #2a2a2a;
    color: #f0f0f0;
}

/* ============================================================
   BUTTONS
   ============================================================ */
QPushButton {
    background-color: #333333;
    color: #f0f0f0;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: 500;
    font-size: 13px;
    min-height: 16px;
}

QPushButton:hover {
    background-color: #3a3a3a;
    border: 1px solid #4a4a4a;
}

QPushButton:pressed {
    background-color: #2a2a2a;
}

QPushButton:disabled {
    background-color: #2a2a2a;
    color: #555555;
    border: 1px solid #333333;
}

/* Primary / accent button (use object name "primaryButton") */
QPushButton#primaryButton, QPushButton#addBidButton {
    background-color: #4a9eff;
    color: #ffffff;
    border: none;
    font-weight: 600;
}

QPushButton#primaryButton:hover, QPushButton#addBidButton:hover {
    background-color: #3a8eef;
}

QPushButton#primaryButton:pressed, QPushButton#addBidButton:pressed {
    background-color: #2a7edf;
}

/* Danger button (use object name "dangerButton") */
QPushButton#dangerButton {
    background-color: #3a1a1a;
    color: #f44336;
    border: 1px solid #5a2a2a;
}

QPushButton#dangerButton:hover {
    background-color: #4a2020;
    border: 1px solid #f44336;
}

/* Success button */
QPushButton#successButton {
    background-color: #1a3a1a;
    color: #4caf50;
    border: 1px solid #2a5a2a;
}

QPushButton#successButton:hover {
    background-color: #204a20;
    border: 1px solid #4caf50;
}

/* ============================================================
   TEXT INPUTS
   ============================================================ */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #333333;
    color: #f0f0f0;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: #4a9eff;
    selection-color: #ffffff;
    font-size: 13px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #4a9eff;
}

QLineEdit:disabled, QTextEdit:disabled {
    background-color: #2a2a2a;
    color: #555555;
}

QLineEdit[readOnly="true"] {
    background-color: #2a2a2a;
    color: #999999;
}

/* ============================================================
   COMBO BOX
   ============================================================ */
QComboBox {
    background-color: #333333;
    color: #f0f0f0;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 16px;
    font-size: 13px;
}

QComboBox:hover {
    border: 1px solid #4a4a4a;
}

QComboBox:focus {
    border: 1px solid #4a9eff;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #999999;
    margin-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #2a2a2a;
    color: #f0f0f0;
    border: 1px solid #3a3a3a;
    selection-background-color: #1e3a5a;
    selection-color: #f0f0f0;
    outline: none;
    padding: 4px;
}

QComboBox QAbstractItemView::item {
    padding: 6px 12px;
    min-height: 24px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #2e3a4a;
}

/* ============================================================
   DATE EDIT / SPIN BOX
   ============================================================ */
QDateEdit, QSpinBox, QDoubleSpinBox {
    background-color: #333333;
    color: #f0f0f0;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}

QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #4a9eff;
}

QDateEdit::drop-down, QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    border: none;
    width: 24px;
}

QCalendarWidget {
    background-color: #2a2a2a;
    color: #f0f0f0;
}

QCalendarWidget QToolButton {
    background-color: #333333;
    color: #f0f0f0;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: 600;
}

QCalendarWidget QToolButton:hover {
    background-color: #4a9eff;
}

QCalendarWidget QAbstractItemView {
    background-color: #2a2a2a;
    color: #f0f0f0;
    selection-background-color: #4a9eff;
    selection-color: #ffffff;
}

/* ============================================================
   SCROLL BARS
   ============================================================ */
QScrollBar:vertical {
    background: #1a1a1a;
    width: 10px;
    border: none;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: #3a3a3a;
    min-height: 30px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #4a4a4a;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background: #1a1a1a;
    height: 10px;
    border: none;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background: #3a3a3a;
    min-width: 30px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal:hover {
    background: #4a4a4a;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}

/* ============================================================
   LABELS
   ============================================================ */
QLabel {
    color: #f0f0f0;
    background-color: transparent;
}

QLabel#secondaryLabel {
    color: #999999;
    font-size: 12px;
}

QLabel#headingLabel {
    font-size: 18px;
    font-weight: 700;
    color: #f0f0f0;
}

QLabel#subheadingLabel {
    font-size: 14px;
    font-weight: 600;
    color: #f0f0f0;
}

/* Stat cards */
QLabel#statValue {
    font-size: 28px;
    font-weight: 700;
    color: #f0f0f0;
}

QLabel#statLabel {
    font-size: 11px;
    font-weight: 600;
    color: #999999;
    text-transform: uppercase;
}

/* ============================================================
   GROUP BOX
   ============================================================ */
QGroupBox {
    background-color: #2a2a2a;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    margin-top: 14px;
    padding: 16px;
    padding-top: 24px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    color: #999999;
    font-size: 11px;
    text-transform: uppercase;
}

/* ============================================================
   CHECK BOX
   ============================================================ */
QCheckBox {
    spacing: 8px;
    color: #f0f0f0;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #3a3a3a;
    background-color: #333333;
}

QCheckBox::indicator:checked {
    background-color: #4a9eff;
    border: 1px solid #4a9eff;
}

QCheckBox::indicator:hover {
    border: 1px solid #4a9eff;
}

/* ============================================================
   PROGRESS BAR
   ============================================================ */
QProgressBar {
    background-color: #333333;
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
    font-size: 11px;
    color: #999999;
}

QProgressBar::chunk {
    background-color: #4a9eff;
    border-radius: 6px;
}

/* ============================================================
   TOOL TIP
   ============================================================ */
QToolTip {
    background-color: #2a2a2a;
    color: #f0f0f0;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ============================================================
   CONTEXT MENU
   ============================================================ */
QMenu {
    background-color: #2a2a2a;
    color: #f0f0f0;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 8px 24px 8px 16px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #1e3a5a;
    color: #f0f0f0;
}

QMenu::separator {
    height: 1px;
    background: #3a3a3a;
    margin: 4px 8px;
}

/* ============================================================
   SPLITTER
   ============================================================ */
QSplitter::handle {
    background-color: #3a3a3a;
}

QSplitter::handle:horizontal {
    width: 1px;
}

QSplitter::handle:vertical {
    height: 1px;
}

/* ============================================================
   SCROLL AREA
   ============================================================ */
QScrollArea {
    border: none;
    background-color: transparent;
}

/* ============================================================
   FRAME (cards / panels)
   ============================================================ */
QFrame#card {
    background-color: #2a2a2a;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
}

QFrame#detailPanel {
    background-color: #222222;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
}

/* ============================================================
   LIST WIDGET (used for customer multi-select)
   ============================================================ */
QListWidget {
    background-color: #333333;
    color: #f0f0f0;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    outline: none;
    padding: 4px;
}

QListWidget::item {
    padding: 6px 10px;
    border-radius: 4px;
}

QListWidget::item:hover {
    background-color: #2e3a4a;
}

QListWidget::item:selected {
    background-color: #1e3a5a;
    color: #f0f0f0;
}

/* ============================================================
   MESSAGE BOX
   ============================================================ */
QMessageBox {
    background-color: #1a1a1a;
}

QMessageBox QLabel {
    color: #f0f0f0;
}

/* ============================================================
   STATUS BAR
   ============================================================ */
QStatusBar {
    background-color: #1a1a1a;
    color: #999999;
    border-top: 1px solid #3a3a3a;
    font-size: 12px;
}
"""


def apply_theme(app):
    """Apply the dark theme stylesheet to the entire QApplication."""
    app.setStyleSheet(DARK_THEME)
