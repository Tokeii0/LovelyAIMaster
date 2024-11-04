from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextEdit, QPushButton, QSplitter, QWidget, QComboBox, 
                             QCheckBox, QGroupBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage
import os
import json
from styles import MAIN_STYLE, CHECKBOX_STYLE

class ImageAnalysisDialog(QDialog):
    analyze_requested = Signal(str, str)  # 发送(提示词, 图片路径)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.resize(800, 500)
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建顶部布局（只包含关闭按钮）
        top_layout = QHBoxLayout()
        top_layout.setSpacing(0)
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
        
        # 添加复选框布局
        checkbox_layout = QHBoxLayout()
        
        # 添加过滤markdown的复选框
        self.filter_markdown = QCheckBox("过滤Markdown格式")
        checkbox_layout.addWidget(self.filter_markdown)
        
        # 添加流模式的复选框
        self.stream_mode = QCheckBox("启用流模式")
        self.stream_mode.setChecked(True)
        checkbox_layout.addWidget(self.stream_mode)
        
        input_layout.addLayout(checkbox_layout)
        
        # 添加发送按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.analyze_button = QPushButton("发送")
        self.analyze_button.setObjectName("sendButton")
        self.analyze_button.setFixedWidth(60)
        button_layout.addWidget(self.analyze_button)
        input_layout.addLayout(button_layout)
        
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
        
        # 设置整体样式
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            QGroupBox {
                font-family: 'Microsoft YaHei';
                font-size: 13px;
                color: #333;
                border: none;
                margin-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            #previewGroup, #inputGroup, #responseGroup {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 6px;
            }
            QLabel {
                color: #555;
                font-size: 12px;
            }
            QComboBox {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 24px;
                font-size: 12px;
            }
            QComboBox:hover {
                border-color: #4a90e2;
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
            QCheckBox {
                color: #555;
                font-size: 12px;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #e0e0e0;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #4a90e2;
                border-color: #4a90e2;
            }
            QPushButton#closeButton {
                background: transparent;
                border: none;
                color: #999;
                font-size: 18px;
                padding: 5px 10px;
            }
            QPushButton#closeButton:hover {
                background-color: #ff4444;
                color: white;
                border-radius: 4px;
            }
            QPushButton#sendButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 15px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton#sendButton:hover {
                background-color: #357abd;
            }
            QLabel#imageLabel {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QSplitter::handle {
                background-color: #e9ecef;
                width: 1px;
            }
        """)
        
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
            if not os.path.exists('prompts.json'):
                default_prompts = [
                    {
                        "title": "示例提示词",
                        "content": "这是一个示例提示词"
                    }
                ]
                with open('prompts.json', 'w', encoding='utf-8') as f:
                    json.dump(default_prompts, f, ensure_ascii=False, indent=4)
            
            with open('prompts.json', 'r', encoding='utf-8') as f:
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