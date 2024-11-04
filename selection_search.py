from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel, QWidget, QApplication
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QScreen, QCursor

import win32clipboard
import win32con
import keyboard
import pyperclip
import time
import traceback

class SelectionSearchDialog(QDialog):
    search_completed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 添加一个变量用于累积文本
        self.current_text = ""
        self.setup_ui()
        
    def setup_ui(self):
        # 设置主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建一个widget作为背景
        self.setStyleSheet("""
            QDialog {
                background: transparent;
            }
            QWidget#contentWidget {
                background-color: rgba(245, 245, 245, 95%);
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
            }
            QPushButton#closeButton:hover {
                background-color: rgba(255, 68, 68, 80%);
                color: white;
            }
        """)
        
        # 创建内容widget
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_layout = QVBoxLayout(content_widget)
        
        # 顶部布局（标题关闭按钮）
        top_layout = QHBoxLayout()
        title_label = QLabel("划词解释")
        title_label.setStyleSheet("color: #333; font-size: 14px;")
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        
        close_button = QPushButton("×")
        close_button.setObjectName("closeButton")
        close_button.clicked.connect(self.hide)
        top_layout.addWidget(close_button)
        content_layout.addLayout(top_layout)
        
        # 文本显示区域
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setMinimumSize(400, 200)
        content_layout.addWidget(self.text_display)
        
        main_layout.addWidget(content_widget)
        
        # 设置窗口大小
        self.resize(450, 300)
        
    def show_at_cursor(self):
        """在鼠标位置显示窗口"""
        # 重置累积的文本
        self.current_text = ""
        cursor = QCursor.pos()
        screen = QApplication.primaryScreen().geometry()
        
        # 计算窗口位置，确保不会超出屏幕
        x = min(cursor.x(), screen.width() - self.width())
        y = min(cursor.y(), screen.height() - self.height())
        
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
        
    def get_selected_text(self):
        """获取选中的文本"""
        # 保存当前剪贴板内容
        old_clipboard = pyperclip.paste()
        
        try:
            # 模拟Ctrl+C复制选中内容
            keyboard.send('ctrl+c')
            time.sleep(0.1)  # 等待复制完成
            
            # 获取剪贴板内容
            selected_text = pyperclip.paste()
            
            # 恢复原来的剪贴板内容
            pyperclip.copy(old_clipboard)
            
            return selected_text.strip()
        except Exception as e:
            print(f"获取选中文本失败: {str(e)}")
            return ""
            
    def set_text(self, text):
        """设置显示文本"""
        try:
            # 累积文本
            self.current_text += text
            # 设置累积的文本到显示框
            self.text_display.setText(self.current_text)
            
            # 滚动到底部
            self.text_display.verticalScrollBar().setValue(
                self.text_display.verticalScrollBar().maximum()
            )
        except Exception as e:
            print(f"设置文本失败: {str(e)}")
            traceback.print_exc()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept() 