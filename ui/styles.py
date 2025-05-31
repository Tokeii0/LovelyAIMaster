MAIN_STYLE = """
QMainWindow {
    background: transparent;
}
QWidget#centralWidget {
    background-color: rgba(255, 255, 255, 95%);
    border: 1px solid rgba(200, 200, 200, 50%);
    border-radius: 15px;
}
QTextEdit {
    background-color: rgba(250, 250, 250, 90%);
    border: 2px solid rgba(230, 230, 230, 70%);
    border-radius: 8px;
    padding: 8px;
    font-size: 14px;
    color: #2c3e50;
    selection-background-color: #3498db;
    selection-color: white;
}
QTextEdit:focus {
    border: 2px solid rgba(52, 152, 219, 70%);
}
QComboBox {
    background-color: rgba(255, 255, 255, 95%);
    border: 2px solid rgba(230, 230, 230, 70%);
    border-radius: 6px;
    padding: 4px 6px;
    font-size: 12px;
    min-height: 25px;
    min-width: 70px;
    color: #2c3e50;
}
QComboBox[editable="true"] {
    padding: 1px 6px;
}
QComboBox QLineEdit {
    border: none;
    padding: 1px 2px;
    min-width: 60px;
}
QComboBox:hover {
    border: 2px solid rgba(52, 152, 219, 70%);
}
QComboBox:focus {
    border: 2px solid #3498db;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border: none;
}
QComboBox QAbstractItemView {
    background-color: white;
    border: 1px solid #ddd;
    selection-background-color: #3498db;
    selection-color: white;
    border-radius: 4px;
}
QLabel {
    font-size: 12px;
    color: #2c3e50;
    font-weight: 500;
    padding-right: 4px;
    min-width: 40px;
}
"""

# 复选框样式
CHECKBOX_STYLE = """
QCheckBox {
    color: #666;
    font-size: 12px;
    spacing: 5px;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border: 1px solid #999;
    background: rgba(255, 255, 255, 80%);
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    border: 1px solid #4A90E2;
    background: rgba(74, 144, 226, 80%);
}
"""

# 图片分析窗口样式
IMAGE_ANALYSIS_STYLE = """
QDialog {
    background-color: rgba(245, 245, 245, 90%);
    border: 1px solid rgba(220, 220, 220, 50%);
    border-radius: 10px;
}
QGroupBox {
    font-family: 'Microsoft YaHei';
    font-size: 13px;
    color: #333;
    border: 1px solid #e9ecef;
    border-radius: 6px;
    margin-top: 12px;
    background-color: rgba(248, 249, 250, 90%);
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QTextEdit {
    background-color: white;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 8px;
    font-size: 12px;
    line-height: 1.5;
}
QTextEdit:focus {
    border-color: #4a90e2;
}
QComboBox {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 3px;
    padding: 1px 3px;
    font-size: 12px;
    min-height: 20px;
}
QComboBox:focus {
    border-color: #4a90e2;
}
QComboBox QAbstractItemView {
    selection-background-color: #4a90e2;
    selection-color: white;
}
QLabel {
    font-size: 12px;
    color: #333;
}
QCheckBox {
    color: #666;
    font-size: 12px;
    spacing: 5px;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border: 1px solid #999;
    background: white;
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    border: 1px solid #4A90E2;
    background: #4A90E2;
}
QPushButton#sendButton {
    background-color: #4a90e2;
    color: white;
    border: none;
    border-radius: 3px;
    padding: 3px 10px;
    font-size: 12px;
}
QPushButton#sendButton:hover {
    background-color: #357abd;
}
QPushButton#closeButton {
    background-color: transparent;
    color: #666;
    font-size: 16px;
    padding: 0px;
    min-width: 20px;
    max-width: 20px;
    min-height: 20px;
    max-height: 20px;
    margin: 2px;
    border-radius: 10px;
}
QPushButton#closeButton:hover {
    background-color: rgba(255, 68, 68, 80%);
    color: white;
}
"""

# 划词搜索窗口样式
SELECTION_SEARCH_STYLE = """
QDialog {
    background-color: rgba(245, 245, 245, 90%);
    border: 1px solid rgba(220, 220, 220, 50%);
    border-radius: 10px;
}
QTextEdit {
    background-color: white;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 8px;
    font-family: "Microsoft YaHei", Arial;
    font-size: 14px;
    line-height: 1.5;
}
QComboBox {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 3px;
    padding: 1px 3px;
    font-size: 12px;
    min-height: 20px;
}
QComboBox:focus {
    border-color: #4a90e2;
}
QComboBox QAbstractItemView {
    selection-background-color: #4a90e2;
    selection-color: white;
}
QLabel {
    font-size: 12px;
    color: #333;
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
    font-size: 16px;
    padding: 0px;
    min-width: 20px;
    max-width: 20px;
    min-height: 20px;
    max-height: 20px;
    margin: 2px;
    border-radius: 10px;
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