from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QSizeGrip, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor, QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QCursor, QIcon
from styles import SELECTION_SEARCH_STYLE, SELECTION_SEARCH_CLOSE_BUTTON_STYLE, SELECTION_SEARCH_TEXT_DISPLAY_STYLE
import re
import asyncio
import traceback

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
        
        # 添加AI客户端
        self.ai_client = None
    
    def set_ai_client(self, ai_client):
        """设置AI客户端"""
        self.ai_client = ai_client
    
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
    
    def show_menu(self, text):
        """显示插件选择菜单"""
        if not hasattr(self, 'selection_menu'):
            from selection_menu import SelectionMenu
            self.selection_menu = SelectionMenu()
        
        # 存储当前选中的文本
        self.current_selected_text = text
        
        # 检查信号是否已连接，如果已连接则断开
        if hasattr(self, '_connected_signals') and self._connected_signals:
            try:
                if self.selection_menu.ai_query_triggered.receivers(self.selection_menu.ai_query_triggered) > 0:
                    self.selection_menu.ai_query_triggered.disconnect()
                if self.selection_menu.plugin_triggered.receivers(self.selection_menu.plugin_triggered) > 0:
                    self.selection_menu.plugin_triggered.disconnect()
                if self.selection_menu.keyword_query_triggered.receivers(self.selection_menu.keyword_query_triggered) > 0:
                    self.selection_menu.keyword_query_triggered.disconnect()
            except:
                pass
        
        # 连接新的信号处理函数
        self.selection_menu.ai_query_triggered.connect(self._handle_ai_query)
        self.selection_menu.plugin_triggered.connect(self._handle_plugin)
        self.selection_menu.keyword_query_triggered.connect(self._handle_keyword_query)
        
        # 标记信号已连接
        self._connected_signals = True
        
        # 在鼠标位置显示菜单
        self.selection_menu.show_menu(QCursor.pos(), text)
    
    def _handle_ai_query(self):
        """内部方法：处理AI查询"""
        self.handle_ai_query(self.current_selected_text)
    
    def _handle_plugin(self, plugin):
        """内部方法：处理插件请求"""
        self.handle_plugin(self.current_selected_text, plugin)
    
    def _handle_keyword_query(self, prompt):
        """内部方法：处理关键词查询"""
        self.handle_keyword_query(self.current_selected_text, prompt)
    
    async def _process_ai_query(self, text, custom_prompt=None):
        """异步处理AI查询"""
        try:
            # 构建提示词
            if custom_prompt:
                # 如果是自定义提示词，将文本添加到提示词后面
                prompt = f"{custom_prompt}\n{text}"
            else:
                # 默认的询问AI模式
                prompt = f"解释下面这段文本的含义：\n{text}"
            
            # 获取AI响应
            async for response_chunk in self.ai_client.get_response_stream(prompt, stream=True):
                if self.isVisible():  # 只有当对话框可见时才更新
                    self.set_text(response_chunk)
                else:
                    break
                    
        except Exception as e:
            error_msg = f"获取AI响应失败: {str(e)}"
            print(error_msg)
            if self.isVisible():
                self.text_display.setPlainText(f"错误: {error_msg}")
    
    def handle_plugin(self, text, plugin):
        """处理插件处理请求"""
        try:
            result = plugin.process(text)
            self.show()  # 显示对话框
            self.text_display.clear()
            self.text_display.setPlainText(result)
        except Exception as e:
            self.show()
            self.text_display.setPlainText(f"插件处理失败: {str(e)}")
    
    def handle_keyword_query(self, text, prompt):
        """处理关键词查询"""
        try:
            if not self.ai_client:
                self.text_display.setPlainText("错误: AI客户端未初始化")
                return
                
            self.show()  # 显示对话框
            self.text_display.clear()
            self.current_cursor = None
            
            # 创建异步任务处理AI请求，直接使用提供的提示词
            loop = asyncio.get_event_loop()
            loop.create_task(self._process_ai_query(text, prompt))
            
        except Exception as e:
            self.text_display.setPlainText(f"处理查询失败: {str(e)}")
            traceback.print_exc()
    
    def handle_ai_query(self, text):
        """处理AI查询请求"""
        try:
            if not self.ai_client:
                self.text_display.setPlainText("错误: AI客户端未初始化")
                return
                
            self.show()  # 显示对话框
            self.text_display.clear()
            self.current_cursor = None
            
            # 创建异步任务处理AI请求，使用传入的text而不是重新获取
            loop = asyncio.get_event_loop()
            loop.create_task(self._process_ai_query(text))
            
        except Exception as e:
            self.text_display.setPlainText(f"处理查询失败: {str(e)}")
            traceback.print_exc()