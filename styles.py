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

SELECTION_SEARCH_STYLE = """
QDialog {
    background-color: rgba(245, 245, 245, 90%);
    border: 1px solid #ccc;
    border-radius: 5px;
}
"""

SELECTION_SEARCH_CLOSE_BUTTON_STYLE = """
QPushButton {
    background-color: transparent;
    color: #666666;
    border: none;
    font-size: 16px;
    padding: 5px 8px;
}
QPushButton:hover {
    background-color: #f44336;
    color: white;
    border-radius: 3px;
}
"""

SELECTION_SEARCH_TEXT_DISPLAY_STYLE = """
QTextEdit {
    background-color: white;
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 5px;
    font-family: "Microsoft YaHei", Arial;
    font-size: 14px;
    line-height: 1.5;
}
"""

# 聊天窗口样式
CHAT_WINDOW_STYLE = """
QMainWindow {
    background: transparent;
}
QWidget#centralWidget {
    background-color: rgba(255, 255, 255, 90%);
    border: 1px solid rgba(224, 224, 224, 90%);
    border-radius: 10px;
}
QTextEdit#inputText {
    background-color: rgba(255, 255, 255, 95%);
    border: 1px solid rgba(200, 200, 200, 95%);
    border-radius: 5px;
    padding: 8px;
    font-size: 13px;
    margin: 0px 10px;
}
QPushButton {
    background-color: rgba(74, 144, 226, 90%);
    color: white;
    border: none;
    border-radius: 5px;
    padding: 5px 10px;
    font-size: 12px;
    min-width: 50px;
}
QPushButton:hover {
    background-color: rgba(53, 122, 189, 90%);
}
QPushButton#closeButton {
    background-color: transparent;
    color: #666;
    font-size: 13px;
    padding: 2px;
    min-width: 20px;
    min-height: 20px;
    margin: 2px;
}
QPushButton#closeButton:hover {
    background-color: rgba(255, 68, 68, 90%);
    color: white;
}
QCheckBox {
    color: rgba(102, 102, 102, 90%);
    font-size: 12px;
    margin: 0px 5px;
    padding: 2px 5px;
}
QLabel {
    color: rgba(102, 102, 102, 90%);
    font-size: 13px;
    padding: 5px;
}
QListWidget {
    background-color: transparent;
    border: none;
}
"""

# 聊天气泡样式
USER_BUBBLE_STYLE = '''
<div style="
    background-color: #DCF8C6;
    padding: 10px;
    border-radius: 10px;
    margin: 5px;
    max-width: 70%;
    text-align: left;
    float: right;
    clear: both;
">
    {content}
</div>
'''

AI_BUBBLE_STYLE = '''
<div style="
    background-color: #FFFFFF;
    padding: 10px;
    border-radius: 10px;
    margin: 5px;
    max-width: 70%;
    text-align: left;
    float: left;
    clear: both;
">
    {content}
</div>
'''