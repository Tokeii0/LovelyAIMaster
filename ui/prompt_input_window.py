import json
import os
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QComboBox, QCheckBox, QLineEdit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator, QIntValidator, QKeyEvent
from .styles import CHECKBOX_STYLE
from .base_window import BaseWindow

class PromptInputWindow(BaseWindow):
    """独立的提示词输入窗口组件"""
    
    # 信号定义
    prompt_submitted = Signal(str, float, int, bool)  # 提示词, 温度, 最大token, 过滤markdown
    window_closed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setFixedSize(400, 120)
        
        # 设置窗口半透明效果
        self.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 200);
                border-radius: 20px;
                border: 2px solid rgba(0, 184, 148, 150);
            }
        """)
        
        # 设置窗口透明度
        self.setWindowOpacity(0.92)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # 启用Windows模糊效果（简化版本）
        try:
            import platform
            if platform.system() == "Windows":
                # 使用Qt的图形效果来模拟模糊
                from PySide6.QtWidgets import QGraphicsBlurEffect
                
                # 为窗口添加模糊效果
                blur_effect = QGraphicsBlurEffect()
                blur_effect.setBlurRadius(15)
                # self.setGraphicsEffect(blur_effect)  # 暂时注释，可能影响性能
                
                print("已启用半透明效果")
        except Exception as e:
            print(f"模糊效果设置失败: {e}")
        
        # 输入历史记录
        self.input_history = []
        self.history_index = -1
        
        self.init_ui()
        self.load_prompts()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("提示词输入")
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 5, 8, 8)
        main_layout.setSpacing(8)
        
        # 顶部拖动区域和关闭按钮
        top_layout = QHBoxLayout()
        top_layout.setSpacing(0)
        
        # 添加拖动区域标题
        drag_label = QLabel("AI助手")
        drag_label.setStyleSheet("""
            QLabel {
                background: rgba(0, 184, 148, 100);
                color: rgba(255, 255, 255, 220);
                font-family: "Microsoft YaHei";
                font-size: 11px;
                font-weight: bold;
                padding: 4px 12px;
                border-radius: 8px;
                margin-right: 8px;
            }
        """)
        top_layout.addWidget(drag_label)
        top_layout.addStretch()
        
        # 使用基类的关闭按钮
        self.create_close_button(top_layout)
        main_layout.addLayout(top_layout)
        
        # 提示词下拉框（移除标签）
        prompts_layout = QHBoxLayout()
        prompts_layout.setSpacing(8)
        self.prompts_combo = QComboBox()
        self.prompts_combo.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 150);
                border: 1px solid rgba(0, 184, 148, 100);
                border-radius: 10px;
                padding: 6px 12px;
                font-family: "Microsoft YaHei", Arial;
                font-size: 11px;
                font-weight: 400;
                color: #2d3436;
                min-width: 180px;
            }
            QComboBox:hover {
                border: 1px solid rgba(0, 184, 148, 150);
                background: rgba(255, 255, 255, 180);
            }
            QComboBox:focus {
                border: 2px solid rgba(0, 184, 148, 200);
                background: rgba(255, 255, 255, 200);
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
                border-radius: 6px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid rgba(0, 184, 148, 180);
                margin-right: 6px;
            }
        """)
        self.prompts_combo.currentIndexChanged.connect(self.on_prompt_selected)
        prompts_layout.addWidget(self.prompts_combo)
        prompts_layout.addStretch()
        main_layout.addLayout(prompts_layout)
        
        # 输入区域布局
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        # 输入框
        from PySide6.QtWidgets import QLineEdit
        self.input_text = QLineEdit()
        self.input_text.setPlaceholderText("按'↑'查看历史输入，按'ESC'关闭")
        self.input_text.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 150);
                border: 1px solid rgba(0, 184, 148, 100);
                border-radius: 12px;
                padding: 8px 14px;
                font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
                font-size: 12px;
                font-weight: 400;
                color: #2d3436;
                line-height: 1.3;
                selection-background-color: rgba(0, 184, 148, 80);
            }
            QLineEdit:hover {
                border: 1px solid rgba(0, 184, 148, 150);
                background: rgba(255, 255, 255, 180);
            }
            QLineEdit:focus {
                border: 2px solid rgba(0, 184, 148, 200);
                background: rgba(255, 255, 255, 200);
                outline: none;
            }
        """)
        
        # 发送按钮
        self.send_button = QPushButton("✈️")
        self.send_button.setFixedSize(32, 32)
        self.send_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #00b894, 
                    stop:1 #00a085);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
                padding: 4px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #00d2a4, 
                    stop:1 #00b894);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #009975, 
                    stop:1 #008866);
            }
        """)
        self.send_button.clicked.connect(self.submit_prompt)
        
        # 添加到输入布局
        input_layout.addWidget(self.input_text)
        input_layout.addWidget(self.send_button)
        
        main_layout.addLayout(input_layout)
        
        # 隐藏的参数设置（保持功能但不显示）
        self.temperature_combo = QComboBox()
        self.temperature_combo.addItems(['0.0', '0.3', '0.5', '0.7', '0.9', '1.0'])
        self.temperature_combo.setCurrentText('0.7')
        self.temperature_combo.hide()
        
        self.max_tokens_combo = QComboBox()
        self.max_tokens_combo.addItems(['1000', '2000', '4000', '8000', '16000'])
        self.max_tokens_combo.setCurrentText('2000')
        self.max_tokens_combo.hide()
        
        self.filter_markdown = QCheckBox()
        self.filter_markdown.hide()
        
        # 设置窗口大小
        self.resize(400, 120)
        
        # 历史记录
        self.input_history = []
        self.history_index = -1
        
        # 连接输入框事件
        self.input_text.returnPressed.connect(self.submit_prompt)
    

        
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
        user_input = self.input_text.text().strip()
        if not user_input:
            print("输入为空，跳过处理")
            return
        
        # 添加到历史记录
        if user_input not in self.input_history:
            self.input_history.append(user_input)
        self.history_index = -1
            
        # 获取预设提示词内容（虽然现在隐藏了，但保持兼容性）
        preset_content = self.prompts_combo.currentData() if hasattr(self.prompts_combo, 'currentData') else None
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
    
    def keyPressEvent(self, event: QKeyEvent):
        """处理键盘事件"""
        if event.key() == Qt.Key_Escape:
            self.hide()
        elif event.key() == Qt.Key_Up:
            # 上箭头：查看历史记录
            if self.input_history:
                if self.history_index == -1:
                    self.history_index = len(self.input_history) - 1
                elif self.history_index > 0:
                    self.history_index -= 1
                self.input_text.setText(self.input_history[self.history_index])
        elif event.key() == Qt.Key_Down:
            # 下箭头：查看历史记录
            if self.input_history and self.history_index != -1:
                if self.history_index < len(self.input_history) - 1:
                    self.history_index += 1
                    self.input_text.setText(self.input_history[self.history_index])
                else:
                    self.history_index = -1
                    self.input_text.clear()
        elif event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            self.submit_prompt()
        else:
            super().keyPressEvent(event)
    
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
    
    def show_at_cursor(self):
        """在光标位置显示窗口"""
        super().show_at_cursor()
        self.input_text.setFocus()
    
    def refresh_prompts(self):
        """刷新提示词列表"""
        self.load_prompts()
    

    
    def show_window(self):
        """显示窗口"""
        self.show()
        self.raise_()
        self.activateWindow()
        self.input_text.setFocus()
    
    def set_input_text(self, text):
        """设置输入文本"""
        self.input_text.setText(text)