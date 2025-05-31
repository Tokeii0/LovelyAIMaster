from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextEdit, QPushButton, QSplitter, QWidget, QComboBox, 
                             QCheckBox, QGroupBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage, QDoubleValidator, QIntValidator
import os
import json
from .styles import IMAGE_ANALYSIS_STYLE

class ImageAnalysisDialog(QDialog):
    analyze_requested = Signal(str, str)  # 发送(提示词, 图片路径)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet(IMAGE_ANALYSIS_STYLE)  # 应用新的样式
        self.resize(800, 500)
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 2, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建顶部布局（只包含关闭按钮）
        top_layout = QHBoxLayout()
        top_layout.setSpacing(0)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addStretch()
        
        
        # 添加关闭按钮
        close_button = QPushButton("×")
        close_button.setObjectName("closeButton")
        close_button.clicked.connect(self.hide)
        top_layout.addWidget(close_button)
        
        main_layout.addLayout(top_layout)
        
        # 创建内容布局
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)
        
        # 创建左侧面板
        left_widget = QWidget()
        left_widget.setFixedWidth(300)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # 创建图片预览组
        preview_group = QGroupBox("图片预览")
        preview_group.setObjectName("previewGroup")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(10, 15, 10, 10)
        
        # 图片显示区域
        self.image_label = QLabel()
        self.image_label.setObjectName("imageLabel")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(260, 180)
        preview_layout.addWidget(self.image_label)
        
        # 创建输入组
        input_group = QGroupBox("提示词输入")
        input_group.setObjectName("inputGroup")
        input_layout = QVBoxLayout(input_group)
        input_layout.setContentsMargins(10, 15, 10, 10)
        input_layout.setSpacing(8)  # 调整间距
        
        # 添加提示词下拉框
        prompts_layout = QHBoxLayout()
        prompts_label = QLabel("预设提示词:")
        self.prompts_combo = QComboBox()
        self.prompts_combo.currentIndexChanged.connect(self.on_prompt_selected)
        prompts_layout.addWidget(prompts_label)
        prompts_layout.addWidget(self.prompts_combo)
        input_layout.addLayout(prompts_layout)
        
        # 提示词输入区域
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("请输入提示词...")
        self.prompt_input.setFixedHeight(80)
        input_layout.addWidget(self.prompt_input)
        
        # 创建参数和控制布局
        params_layout = QHBoxLayout()
        params_layout.setSpacing(15)  # 增加组件之间的间距
        
        # 创建左侧参数布局（垂直布局）
        left_params = QVBoxLayout()  # 改为垂直布局
        left_params.setSpacing(5)  # 设置垂直间距
        
        # 温度设置
        temp_layout = QHBoxLayout()
        temp_label = QLabel("温度:")
        temp_label.setFixedWidth(50)  # 调整标签宽度
        self.temperature_combo = QComboBox()
        self.temperature_combo.setEditable(True)
        self.temperature_combo.addItems(['0.0', '0.3', '0.5', '0.7', '0.9', '1.0'])
        self.temperature_combo.setCurrentText('0.7')
        self.temperature_combo.setValidator(QDoubleValidator(0.0, 2.0, 2))
        self.temperature_combo.setFixedWidth(65)  # 减小下拉框宽度
        temp_layout.addWidget(temp_label)
        temp_layout.addWidget(self.temperature_combo)
        temp_layout.addStretch()  # 添加弹性空间
        left_params.addLayout(temp_layout)
        
        # 最大令牌数设置
        tokens_layout = QHBoxLayout()
        tokens_label = QLabel("最大令牌:")
        tokens_label.setFixedWidth(50)  # 调整标签宽度
        self.max_tokens_combo = QComboBox()
        self.max_tokens_combo.setEditable(True)
        self.max_tokens_combo.addItems(['1000', '2000', '4000', '8000', '16000'])
        self.max_tokens_combo.setCurrentText('2000')
        self.max_tokens_combo.setValidator(QIntValidator(1, 32000))
        self.max_tokens_combo.setFixedWidth(65)  # 减小下拉框宽度
        tokens_layout.addWidget(tokens_label)
        tokens_layout.addWidget(self.max_tokens_combo)
        tokens_layout.addStretch()  # 添加弹性空间
        left_params.addLayout(tokens_layout)
        
        params_layout.addLayout(left_params)
        
        # 右侧复选框布局（改为垂直布局）
        right_params = QVBoxLayout()  # 改为垂直布局
        right_params.setSpacing(5)  # 设置垂直间距
        
        # 添加复选框
        self.filter_markdown = QCheckBox("过滤Markdown")
        self.filter_markdown.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
                font-size: 12px;
            }
        """)
        right_params.addWidget(self.filter_markdown)
        
        self.stream_mode = QCheckBox("流模式")
        self.stream_mode.setChecked(True)
        self.stream_mode.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
                font-size: 12px;
            }
        """)
        right_params.addWidget(self.stream_mode)
        
        # 创建一个水平布局来放置发送按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # 添加弹性空间，使按钮靠右
        
        # 添加发送按钮
        self.analyze_button = QPushButton("发送")
        self.analyze_button.setObjectName("sendButton")
        self.analyze_button.setFixedWidth(60)
        self.analyze_button.setFixedHeight(24)
        button_layout.addWidget(self.analyze_button)
        
        # 将按钮布局添加到右侧布局
        right_params.addLayout(button_layout)
        
        params_layout.addLayout(right_params)
        params_layout.addStretch()  # 添加弹性空间
        
        # 将参数布局添加到输入布局
        input_layout.addLayout(params_layout)
        
        # 将两个组添加到左侧布局
        left_layout.addWidget(preview_group)
        left_layout.addWidget(input_group)
        
        # 创建右侧响应组
        response_group = QGroupBox("AI响应")
        response_group.setObjectName("responseGroup")
        response_layout = QVBoxLayout(response_group)
        response_layout.setContentsMargins(10, 15, 10, 10)
        
        # 创建右侧响应显示区域
        self.response_display = QTextEdit()
        self.response_display.setReadOnly(True)
        self.response_display.setPlaceholderText("AI响应将显示在这里...")
        response_layout.addWidget(self.response_display)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(response_group)
        
        content_layout.addWidget(splitter)
        main_layout.addLayout(content_layout)
        
        self.current_image_path = None
        self.load_prompts()
        
        # 连接信号
        self.analyze_button.clicked.connect(self.request_analysis)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def closeEvent(self, event):
        """重写关闭事件，使窗口关闭时只隐藏而不退出"""
        event.ignore()
        self.hide()
    
    def set_image(self, image_path):
        """设置要显示的图片"""
        if not os.path.exists(image_path):
            return
            
        self.current_image_path = image_path
        pixmap = QPixmap(image_path)
        
        # 调整图片大小以适应显示区域，保持比例
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)
    
    def request_analysis(self):
        """请求分析图片"""
        if self.current_image_path and self.prompt_input.toPlainText():
            # 获取选中的预设提示词内容
            preset_content = self.prompts_combo.currentData()
            
            # 组合最终的提示词
            final_prompt = self.prompt_input.toPlainText()
            if preset_content and self.prompts_combo.currentIndex() > 0:
                final_prompt = f"{preset_content}\n{final_prompt}"
            
            # 获取并验证温度值
            try:
                temperature = float(self.temperature_combo.currentText())
                temperature = max(0.0, min(2.0, temperature))
            except ValueError:
                temperature = 0.7
            
            # 获取并验证最大令牌数
            try:
                max_tokens = int(self.max_tokens_combo.currentText())
                max_tokens = max(1, min(32000, max_tokens))
            except ValueError:
                max_tokens = 2000
            
            # 发送分析请求，包含温度和最大令牌数参数
            self.analyze_requested.emit(final_prompt, self.current_image_path)
    
    def append_response(self, text):
        """添加AI响应文本"""
        current_text = self.response_display.toPlainText()
        self.response_display.setText(current_text + text)
    
    def clear_response(self):
        """清空响应区域"""
        self.response_display.clear()
    
    def load_prompts(self):
        """加载提示词到下拉框"""
        try:
            if not os.path.exists('config/prompts.json'):
                default_prompts = [
                    {
                        "title": "示例提示词",
                        "content": "这是一个示例提示词"
                    }
                ]
                with open('config/prompts.json', 'w', encoding='utf-8') as f:
                    json.dump(default_prompts, f, ensure_ascii=False, indent=4)
            
            with open('config/prompts.json', 'r', encoding='utf-8') as f:
                prompts = json.load(f)
                self.prompts_combo.clear()
                self.prompts_combo.addItem("选择提示词...")
                for prompt in prompts:
                    self.prompts_combo.addItem(prompt['title'], prompt['content'])
        except Exception as e:
            print(f"加载提示词失败: {str(e)}")
    
    def on_prompt_selected(self, index):
        """当选择提示词时触发"""
        if index > 0:  # 跳过默认选项
            self.prompt_input.setFocus()