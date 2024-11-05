from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QSizeGrip, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor, QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QCursor, QIcon
from styles import SELECTION_SEARCH_STYLE, SELECTION_SEARCH_CLOSE_BUTTON_STYLE, SELECTION_SEARCH_TEXT_DISPLAY_STYLE
import re

class MarkdownHighlighter(QSyntaxHighlighter):
    """Markdown语法高亮器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 定义Markdown语法规则和对应的格式
        self.formats = {
            'header': self._format('#2962FF'),  # 标题
            'bold': self._format('#000000', bold=True),  # 粗体
            'italic': self._format('#000000', italic=True),  # 斜体
            'code': self._format('#D81B60', background='#F5F5F5'),  # 代码
            'link': self._format('#1976D2'),  # 链接
            'list': self._format('#4CAF50'),  # 列表
        }
        
        # 编译正则表达式
        self.patterns = {
            'header': re.compile(r'^#{1,6}\s.*$'),
            'bold': re.compile(r'\*\*.*?\*\*'),
            'italic': re.compile(r'\*.*?\*'),
            'code': re.compile(r'`.*?`'),
            'link': re.compile(r'\[.*?\]\(.*?\)'),
            'list': re.compile(r'^\s*[\*\-\+]\s.*$'),
        }
    
    def _format(self, color, background=None, bold=False, italic=False):
        """创建文本格式"""
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if background:
            fmt.setBackground(QColor(background))
        fmt.setFontWeight(700 if bold else 400)
        fmt.setFontItalic(italic)
        return fmt
    
    def highlightBlock(self, text):
        """高亮文本块"""
        for pattern_name, pattern in self.patterns.items():
            format = self.formats[pattern_name]
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), format)

class SelectionSearchDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet(SELECTION_SEARCH_STYLE)
        self.setWindowIcon(QIcon(r"icons\logo.ico"))
        
        # 设置最小尺寸
        self.setMinimumSize(450, 300)
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 10)
        main_layout.setSpacing(5)
        
        # 创建顶部布局（包含关闭按钮）
        top_layout = QHBoxLayout()
        top_layout.setSpacing(0)
        
        # 添加弹性空间
        top_layout.addStretch()
        
        # 创建关闭按钮
        close_button = QPushButton("×")
        close_button.setStyleSheet(SELECTION_SEARCH_CLOSE_BUTTON_STYLE)
        close_button.clicked.connect(self.hide)
        close_button.setCursor(Qt.PointingHandCursor)
        top_layout.addWidget(close_button)
        
        main_layout.addLayout(top_layout)
        
        # 创建文本显示区域
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setStyleSheet(SELECTION_SEARCH_TEXT_DISPLAY_STYLE)
        
        # 添加Markdown高亮
        self.highlighter = MarkdownHighlighter(self.text_display.document())
        
        main_layout.addWidget(self.text_display)
        
        # 添加大小调整手柄
        size_grip = QSizeGrip(self)
        main_layout.addWidget(size_grip, 0, Qt.AlignBottom | Qt.AlignRight)
        
        # 用于拖动窗口的变量
        self.drag_position = None
        
        # 用于存储当前光标位置
        self.current_cursor = None
    
    def set_text(self, text):
        """设置显示文本，避免不必要的换行"""
        if not self.current_cursor:
            # 第一次设置文本，获取文本光标
            self.current_cursor = self.text_display.textCursor()
        
        # 在当前位置插入文本，不添加额外换行
        self.current_cursor.insertText(text)
        
        # 确保显示最新内容
        self.text_display.setTextCursor(self.current_cursor)
        self.text_display.ensureCursorVisible()
    
    def show_at_cursor(self):
        """在鼠标位置显示对话框"""
        cursor = QCursor.pos()
        self.move(cursor.x() + 10, cursor.y() + 10)
        # 重置光标位置
        self.current_cursor = None
        self.show()
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if event.buttons() & Qt.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.drag_position = None
            event.accept()