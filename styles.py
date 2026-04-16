DARK_THEME = """
/* ── Base ── */
QWidget {
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}
QMainWindow, QDialog {
    background-color: #0d1117;
}

/* ── Buttons ── */
QPushButton {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #30363d;
    border-color: #8b949e;
}
QPushButton:pressed {
    background-color: #161b22;
}
QPushButton:disabled {
    color: #484f58;
    border-color: #21262d;
}
QPushButton#primaryBtn {
    background-color: #238636;
    border-color: #2ea043;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#primaryBtn:hover {
    background-color: #2ea043;
    border-color: #3fb950;
}
QPushButton#dangerBtn {
    background-color: #da3633;
    border-color: #f85149;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#dangerBtn:hover {
    background-color: #b91c1c;
}
QPushButton#warnBtn {
    background-color: #9e6a03;
    border-color: #d29922;
    color: #ffffff;
}
QPushButton#warnBtn:hover {
    background-color: #d29922;
}

/* ── Inputs ── */
QLineEdit {
    background-color: #161b22;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #1f6feb;
}
QLineEdit:focus {
    border-color: #1f6feb;
    outline: none;
}
QLineEdit:disabled {
    color: #484f58;
    background-color: #0d1117;
}

/* ── Labels ── */
QLabel {
    color: #c9d1d9;
    background: transparent;
}
QLabel#titleLabel {
    font-size: 22px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.5px;
}
QLabel#subtitleLabel {
    font-size: 13px;
    color: #8b949e;
}
QLabel#sectionLabel {
    font-size: 11px;
    font-weight: 700;
    color: #8b949e;
    letter-spacing: 0.5px;
}
QLabel#badgeGreen {
    color: #3fb950;
    background: transparent;
}
QLabel#badgeRed {
    color: #f85149;
    background: transparent;
}
QLabel#badgeBlue {
    color: #58a6ff;
    background: transparent;
}

/* ── Lists ── */
QListWidget {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #c9d1d9;
    padding: 4px;
    outline: none;
}
QListWidget::item {
    padding: 8px 12px;
    border-radius: 4px;
    margin: 1px 0;
}
QListWidget::item:selected {
    background-color: #1f6feb;
    color: #ffffff;
}
QListWidget::item:hover:!selected {
    background-color: #21262d;
}

/* ── Progress Bar ── */
QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: #21262d;
    height: 8px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background-color: #238636;
    border-radius: 4px;
}

/* ── Frames ── */
QFrame#card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
}
QFrame#header {
    background-color: #161b22;
    border-bottom: 1px solid #30363d;
}
QFrame#statusBar {
    background-color: #161b22;
    border-top: 1px solid #30363d;
}

/* ── Scrollbars ── */
QScrollBar:vertical {
    border: none;
    background: #0d1117;
    width: 8px;
    border-radius: 4px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #8b949e;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

/* ── Message Boxes ── */
QMessageBox {
    background-color: #161b22;
}
QMessageBox QLabel {
    color: #c9d1d9;
}
QMessageBox QPushButton {
    min-width: 80px;
}

/* ── Input Dialog ── */
QInputDialog {
    background-color: #161b22;
}

/* ── Tooltips ── */
QToolTip {
    background-color: #161b22;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
}
"""
