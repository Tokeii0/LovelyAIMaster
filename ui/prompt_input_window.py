import json
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator, QIntValidator
from .styles import MAIN_STYLE, CHECKBOX_STYLE

class PromptInputWindow(QWidget):
    """独立的提示词输入窗口组件"""
    
    # 信号定义
    prompt_submitted = Signal(str, float, int, bool)  # 提示词, 温度, 最大token, 过滤markdown
    window_closed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_prompts()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet(self.get_window_style())
        self.setWindowTitle("提示词输入")
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 10)
        main_layout.setSpacing(10)
        
        # 顶部布局和关闭按钮
        top_layout = QHBoxLayout()
        top_layout.setSpacing(0)
        top_layout.addStretch()
        
        # 圆形关闭标签
        close_button = QLabel("×")
        close_button.setObjectName("closeButton")
        close_button.setFixedSize(30, 30)
        close_button.setAlignment(Qt.AlignCenter)
        close_button.mousePressEvent = lambda event: self.close_window()
        close_button.setStyleSheet("""
            QLabel#closeButton {
                background-color: rgba(255, 182, 193, 200);
                color: rgba(139, 69, 19, 200);
                border-radius: 15px;
                font-size: 18px;
                font-weight: bold;
                border: 2px solid rgba(255, 192, 203, 150);
            }
            QLabel#closeButton:hover {
                background-color: rgba(255, 160, 180, 230);
                border: 2px solid rgba(255, 105, 180, 180);
            }
        """)
        top_layout.addWidget(close_button)
        main_layout.addLayout(top_layout)
        
        # 提示词下拉框
        prompts_layout = QHBoxLayout()
        prompts_label = QLabel("预设提示词:")
        self.prompts_combo = QComboBox()
        self.prompts_combo.currentIndexChanged.connect(self.on_prompt_selected)
        prompts_layout.addWidget(prompts_label)
        prompts_layout.addWidget(self.prompts_combo)
        main_layout.addLayout(prompts_layout)
        
        # 输入框
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("请输入提示词...")
        self.input_text.setMinimumHeight(100)
        self.input_text.setMaximumHeight(150)
        main_layout.addWidget(self.input_text)
        
        # 参数设置和按钮布局
        button_layout = QHBoxLayout()
        
        # 温度设置
        temp_layout = QHBoxLayout()
        temp_label = QLabel("个性度:")
        self.temperature_combo = QComboBox()
        self.temperature_combo.setEditable(True)
        self.temperature_combo.addItems(['0.0', '0.3', '0.5', '0.7', '0.9', '1.0'])
        self.temperature_combo.setCurrentText('0.7')
        self.temperature_combo.setValidator(QDoubleValidator(0.0, 2.0, 2))
        self.temperature_combo.setMinimumWidth(60)
        self.temperature_combo.setFixedWidth(60)
        temp_layout.addWidget(temp_label)
        temp_layout.addWidget(self.temperature_combo)
        button_layout.addLayout(temp_layout)
        
        # 最大令牌数设置
        tokens_layout = QHBoxLayout()
        tokens_label = QLabel("词元:")
        self.max_tokens_combo = QComboBox()
        self.max_tokens_combo.setEditable(True)
        self.max_tokens_combo.addItems(['1000', '2000', '4000', '8000', '16000'])
        self.max_tokens_combo.setCurrentText('2000')
        self.max_tokens_combo.setValidator(QIntValidator(1, 32000))
        self.max_tokens_combo.setMinimumWidth(70)
        self.max_tokens_combo.setFixedWidth(70)
        tokens_layout.addWidget(tokens_label)
        tokens_layout.addWidget(self.max_tokens_combo)
        button_layout.addLayout(tokens_layout)
        
        # 间距
        button_layout.addSpacing(5)
        
        # 过滤Markdown复选框
        self.filter_markdown = QCheckBox("过滤Markdown格式")
        self.filter_markdown.setStyleSheet(CHECKBOX_STYLE)
        button_layout.addWidget(self.filter_markdown)
        
        button_layout.addStretch()
        
        # 发送按钮
        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.submit_prompt)
        button_layout.addWidget(self.send_button)
        
        main_layout.addLayout(button_layout)
        
        # 设置窗口大小
        self.resize(350, 250)
        
        # 设置鼠标跟踪
        self.setMouseTracking(True)
        self.drag_position = None
    
    def get_window_style(self):
        """获取窗口样式 - 樱花粉配色"""
        return """
        QWidget {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 240, 245, 250),
                stop:1 rgba(255, 228, 225, 240));
            border: 2px solid rgba(255, 182, 193, 180);
            border-radius: 15px;
        }
        QTextEdit {
            background-color: rgba(255, 250, 250, 250);
            border: 2px solid rgba(255, 192, 203, 150);
            border-radius: 8px;
            padding: 8px;
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
            border-radius: 6px;
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
            border-radius: 4px;
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
            border-radius: 8px;
            padding: 8px 16px;
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
            border-radius: 3px;
        }
        QCheckBox::indicator:checked {
            border: 1px solid rgba(255, 105, 180, 200);
            background: rgba(255, 182, 193, 200);
        }
        """
        
    def load_prompts(self):
        """加载预设提示词到下拉框"""
        default_prompts = [
            {
                "title": "示例提示词",
                "content": "这是一个示例提示词"
            }
        ]
        
        try:
            if not os.path.exists('config/prompts.json'):
                self._create_default_prompts(default_prompts)
            
            with open('config/prompts.json', 'r', encoding='utf-8') as f:
                prompts = json.load(f)
                self._populate_prompts_combo(prompts)
                
        except json.JSONDecodeError as e:
            print(f"提示词文件格式错误: {e}，使用默认提示词")
            self._create_default_prompts(default_prompts)
            self._populate_prompts_combo(default_prompts)
        except (OSError, IOError) as e:
            print(f"读取提示词文件失败: {e}，使用默认提示词")
            self._populate_prompts_combo(default_prompts)
        except Exception as e:
            print(f"加载提示词时发生未知错误: {e}")
            self._populate_prompts_combo(default_prompts)
    
    def _create_default_prompts(self, prompts):
        """创建默认提示词文件"""
        try:
            with open('config/prompts.json', 'w', encoding='utf-8') as f:
                json.dump(prompts, f, ensure_ascii=False, indent=4)
        except (OSError, IOError) as e:
            print(f"创建默认提示词文件失败: {e}")
    
    def _populate_prompts_combo(self, prompts):
        """填充提示词下拉框"""
        self.prompts_combo.clear()
        self.prompts_combo.addItem("选择提示词...")
        for prompt in prompts:
            if isinstance(prompt, dict) and 'title' in prompt and 'content' in prompt:
                self.prompts_combo.addItem(prompt['title'], prompt['content'])
            else:
                print(f"无效的提示词格式: {prompt}")
    
    def on_prompt_selected(self, index):
        """当选择提示词时触发"""
        if index > 0:
            self.input_text.setFocus()
    
    def submit_prompt(self):
        """提交提示词"""
        user_input = self.input_text.toPlainText().strip()
        if not user_input:
            print("输入为空，跳过处理")
            return
            
        # 获取预设提示词内容
        preset_content = self.prompts_combo.currentData()
        final_prompt = user_input
        if preset_content:
            final_prompt = preset_content.replace("{input}", user_input)
        
        # 获取参数
        temperature = self._get_temperature_value()
        max_tokens = self._get_max_tokens_value()
        filter_markdown = self.filter_markdown.isChecked()
        
        # 清空输入框并隐藏窗口
        self.input_text.clear()
        self.hide()
        
        # 发送信号
        self.prompt_submitted.emit(final_prompt, temperature, max_tokens, filter_markdown)
    
    def _get_temperature_value(self):
        """获取温度值"""
        try:
            temperature_text = self.temperature_combo.currentText().strip()
            if temperature_text:
                temperature = float(temperature_text)
                # 确保温度值在合理范围内
                return max(0.0, min(2.0, temperature))
        except (ValueError, AttributeError) as e:
            print(f"温度值解析失败: {e}，使用默认值")
        return 0.7  # 默认值
    
    def _get_max_tokens_value(self):
        """获取最大token值"""
        try:
            tokens_text = self.max_tokens_combo.currentText().strip()
            if tokens_text:
                max_tokens = int(tokens_text)
                # 确保token值在合理范围内
                return max(1, min(32000, max_tokens))
        except (ValueError, AttributeError) as e:
            print(f"token值解析失败: {e}，使用默认值")
        return 2000  # 默认值
    
    def close_window(self):
        """关闭窗口"""
        self.hide()
        self.window_closed.emit()
    
    def show_at_cursor(self):
        """在光标位置显示窗口"""
        from PySide6.QtGui import QCursor
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
        self.input_text.setFocus()
    
    def refresh_prompts(self):
        """刷新提示词列表"""
        self.load_prompts()
    
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
    
    def keyPressEvent(self, event):
        """键盘事件处理"""
        if event.key() == Qt.Key_Escape:
            self.close_window()
        elif event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            self.submit_prompt()
        else:
            super().keyPressEvent(event)
    
    def show_window(self):
        """显示窗口"""
        self.show()
        self.raise_()
        self.activateWindow()
        self.input_text.setFocus()
    
    def set_input_text(self, text):
        """设置输入文本"""
        self.input_text.setText(text)