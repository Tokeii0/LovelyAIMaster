from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor

class BaseWindow(QWidget):
    """基础窗口类，提供通用的窗口功能"""
    
    window_closed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drag_position = None
        self.setup_base_window()
    
    def setup_base_window(self):
        """设置基础窗口属性"""
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setMouseTracking(True)
        self.setStyleSheet(self.get_base_style())
    
    def get_base_style(self):
        """获取基础樱花粉配色样式"""
        return """
        QWidget {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 240, 245, 250),
                stop:1 rgba(255, 228, 225, 240));
            border: 2px solid rgba(255, 182, 193, 180);
            border-radius: 20px;
        }
        QTextEdit {
            background-color: rgba(255, 250, 250, 250);
            border: 2px solid rgba(255, 192, 203, 150);
            border-radius: 12px;
            padding: 10px;
            font-size: 14px;
            color: rgba(139, 69, 19, 200);
            selection-background-color: rgba(255, 105, 180, 150);
            selection-color: white;
        }
        QTextEdit:focus {
            border: 2px solid rgba(255, 105, 180, 200);
        }
        QComboBox {
            background-color: rgba(255, 250, 250, 250);
            border: 2px solid rgba(255, 192, 203, 150);
            border-radius: 10px;
            padding: 4px 6px;
            font-size: 12px;
            min-height: 25px;
            min-width: 70px;
            color: rgba(139, 69, 19, 200);
        }
        QComboBox[editable="true"] {
            padding: 1px 6px;
        }
        QComboBox QLineEdit {
            border: none;
            padding: 1px 2px;
            min-width: 60px;
            color: rgba(139, 69, 19, 200);
        }
        QComboBox:hover {
            border: 2px solid rgba(255, 105, 180, 200);
        }
        QComboBox:focus {
            border: 2px solid rgba(255, 105, 180, 220);
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
            background-color: rgba(255, 250, 250, 250);
            border: 1px solid rgba(255, 192, 203, 180);
            selection-background-color: rgba(255, 105, 180, 150);
            selection-color: white;
            border-radius: 8px;
        }
        QLabel {
            font-size: 12px;
            color: rgba(139, 69, 19, 200);
            font-weight: 500;
            padding-right: 4px;
            min-width: 40px;
        }
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 182, 193, 220),
                stop:1 rgba(255, 160, 180, 220));
            color: white;
            border: 2px solid rgba(255, 192, 203, 150);
            border-radius: 12px;
            padding: 10px 18px;
            font-size: 12px;
            font-weight: 500;
            min-width: 60px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 160, 180, 240),
                stop:1 rgba(255, 140, 160, 240));
            border: 2px solid rgba(255, 105, 180, 180);
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 140, 160, 240),
                stop:1 rgba(255, 120, 140, 240));
            border: 2px solid rgba(255, 105, 180, 200);
        }
        QCheckBox {
            color: rgba(139, 69, 19, 180);
            font-size: 12px;
            spacing: 5px;
        }
        QCheckBox::indicator {
            width: 15px;
            height: 15px;
            border: 1px solid rgba(255, 192, 203, 180);
            background: rgba(255, 250, 250, 200);
            border-radius: 6px;
        }
        QCheckBox::indicator:checked {
            border: 1px solid rgba(255, 105, 180, 200);
            background: rgba(255, 182, 193, 200);
        }
        """
    
    def create_close_button(self, layout):
        """创建标准的圆形关闭按钮"""
        close_button = QLabel("×")
        close_button.setObjectName("closeButton")
        close_button.setFixedSize(24, 24)
        close_button.setAlignment(Qt.AlignCenter)
        close_button.mousePressEvent = lambda event: self.close_window()
        close_button.setStyleSheet("""
            QLabel#closeButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ff7675, 
                    stop:1 #e84393);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 600;
                min-width: 24px;
                min-height: 24px;
            }
            QLabel#closeButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #fd79a8, 
                    stop:1 #ff7675);
            }
            QLabel#closeButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #e84393, 
                    stop:1 #d63031);
            }
        """)
        layout.addWidget(close_button)
        return close_button
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 用于拖拽窗口"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖拽窗口"""
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.drag_position = None
            event.accept()
    
    def show_at_cursor(self):
        """在光标位置显示窗口"""
        from PySide6.QtWidgets import QApplication
        
        cursor = QCursor.pos()
        window_x = cursor.x() + 10
        window_y = cursor.y() + 10
        screen = QApplication.primaryScreen().geometry()
        
        # 确保窗口不会超出屏幕边界
        if window_x + self.width() > screen.width():
            window_x = screen.width() - self.width()
        if window_y + self.height() > screen.height():
            window_y = screen.height() - self.height()
            
        self.move(window_x, window_y)
        self.show()
        self.raise_()
        self.activateWindow()
    
    def close_window(self):
        """关闭窗口"""
        self.hide()
        self.window_closed.emit()
    
    def keyPressEvent(self, event):
        """键盘事件处理"""
        if event.key() == Qt.Key_Escape:
            self.close_window()
        else:
            super().keyPressEvent(event)