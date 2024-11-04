MAIN_STYLE = """
QMainWindow {
    background: transparent;
}
QWidget#centralWidget {
    background-color: rgba(245, 245, 245, 90%);
    border: 1px solid rgba(220, 220, 220, 50%);
    border-radius: 10px;
}
QTextEdit {
    background-color: rgba(255, 255, 255, 80%);
    border: 1px solid rgba(220, 220, 220, 50%);
    border-radius: 5px;
    padding: 5px;
    font-size: 14px;
    color: #333;
}
QPushButton {
    background-color: rgba(74, 144, 226, 80%);
    color: white;
    border: none;
    border-radius: 5px;
    padding: 5px 15px;
    font-size: 13px;
    min-height: 25px;
}
QPushButton:hover {
    background-color: rgba(53, 122, 189, 80%);
}
QPushButton#closeButton {
    background-color: transparent;
    color: #666;
    font-size: 14px;
    padding: 2px;
    min-width: 20px;
    min-height: 20px;
    margin: 2px;
}
QPushButton#closeButton:hover {
    background-color: rgba(255, 68, 68, 80%);
    color: white;
}
QPushButton#stopButton {
    background-color: rgba(255, 68, 68, 80%);
    color: white;
    border: none;
    border-radius: 5px;
    padding: 5px 15px;
    font-size: 13px;
    min-height: 25px;
}
QPushButton#stopButton:hover {
    background-color: rgba(255, 38, 38, 80%);
}
"""

CHECKBOX_STYLE = """
QCheckBox {
    color: #666;
    font-size: 12px;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
}
QCheckBox::indicator:unchecked {
    border: 1px solid #999;
    background: rgba(255, 255, 255, 80%);
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    border: 1px solid #4A90E2;
    background: rgba(74, 144, 226, 80%);
    border-radius: 3px;
}
""" 