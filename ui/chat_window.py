from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTextEdit, 
                               QPushButton, QHBoxLayout, QCheckBox, QLabel, QListWidget, QListWidgetItem, QSizePolicy, QSizeGrip, QComboBox)
from PySide6.QtCore import Qt, QEvent,QTimer, QSize
from PySide6.QtGui import QTextOption, QIcon, QDoubleValidator, QIntValidator

import asyncio


class MessageItem(QWidget):
    def __init__(self, role: str, content: str):
        super().__init__()
        self.role = role
        self.content = content
        self.label = None
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)

        # 使用 QTextEdit 替代 QLabel
        self.label = QTextEdit()
        self.label.setReadOnly(True)
        self.label.setText(self.content)
        
        # 设置自动换行
        self.label.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        
        # 隐藏滚动条
        self.label.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.label.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 修改宽度计算逻辑，使其基于父窗口宽度
        parent_width = self.parent().width() if self.parent() else 550
        max_width = int(parent_width * 0.85)  # 使用父窗口宽度的85%
        content_length = max(len(line) for line in self.content.split('\n'))
        width = min(max_width, max(200, content_length * 20))  # 增加每个字符的宽度
        self.label.setFixedWidth(width)
        
        # 计算实际需要的高度
        document = self.label.document()
        document.setTextWidth(width - 20)  # 考虑padding
        
        # 使用documentLayout来获取更准确的文本高度
        text_height = document.documentLayout().documentSize().height()
        padding = 20  # 上下各10px的padding
        total_height = int(text_height + padding)
        
        # 设置最小高度
        total_height = max(40, total_height)  # 确保至少40px高
        
        self.label.setFixedHeight(total_height)
        
        if self.role == 'user':
            layout.addStretch()
            layout.addWidget(self.label)
            self.label.setStyleSheet("""
                QTextEdit {
                    background-color: #DCF8C6;
                    padding: 10px;
                    border-radius: 10px;
                    border: none;
                    font-size: 13px;
                    color: #000000;
                    selection-background-color: #B5E2A8;
                    line-height: 1.5;
                }
            """)
        else:
            layout.addWidget(self.label)
            layout.addStretch()
            self.label.setStyleSheet("""
                QTextEdit {
                    background-color: #E3F2FD;
                    padding: 10px;
                    border-radius: 10px;
                    border: none;
                    font-size: 13px;
                    color: #000000;
                    selection-background-color: #BBDEFB;
                    line-height: 1.5;
                }
            """)

        self.setLayout(layout)
        # 为整个widget设置合适的高度，添加额外空间以防止文本被截断
        self.setFixedHeight(total_height + 10)

    def update_content(self, content):
        """更新消息内容"""
        self.content = content
        self.label.setText(content)
        
        width = self.label.width()
        document = self.label.document()
        document.setTextWidth(width - 20)
        
        # 使用documentLayout获取准确的文本高度
        text_height = document.documentLayout().documentSize().height()
        padding = 20
        total_height = int(text_height + padding)
        total_height = max(40, total_height)  # 确保最小高度
        
        self.label.setFixedHeight(total_height)
        self.setFixedHeight(total_height + 10)

    def resizeEvent(self, event):
        """处理大小调整事件"""
        super().resizeEvent(event)
        # 重新计算宽度和高度
        parent_width = self.parent().width() if self.parent() else 550
        max_width = int(parent_width * 0.85)
        content_length = max(len(line) for line in self.content.split('\n'))
        width = min(max_width, max(200, content_length * 20))
        
        self.label.setFixedWidth(width)
        
        # 重新计算高度
        document = self.label.document()
        document.setTextWidth(width - 20)
        text_height = document.documentLayout().documentSize().height()
        padding = 20
        total_height = int(text_height + padding)
        total_height = max(40, total_height)
        
        self.label.setFixedHeight(total_height)
        self.setFixedHeight(total_height + 10)

class ChatWindow(QMainWindow):
    def __init__(self, ai_client):
        super().__init__()
        self.ai_client = ai_client
        self.messages = []  # 存储对话历史
        self.should_stop = False

        # 设置窗口属性 - 移除标题栏并保持置顶
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.WindowMaximizeButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 创建中心部件并设置对象名称
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        self.setWindowIcon(QIcon(r"icons\logo.ico"))
        
        # 从 styles.py 导入样式
        from .styles import CHAT_WINDOW_STYLE
        self.setStyleSheet(CHAT_WINDOW_STYLE)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)  # 减小边距
        layout.setSpacing(5)  # 减小间距

        # 创建顶部布局（包含关闭按钮）
        top_layout = QHBoxLayout()
        top_layout.setSpacing(0)

        # 添加标题
        title_label = QLabel("连续对话")
        top_layout.addWidget(title_label)

        # 添加弹性空间
        top_layout.addStretch()

        # 添加关闭按钮
        close_button = QLabel("×")
        close_button.setObjectName("closeButton")
        close_button.setFixedSize(30, 30)
        close_button.setAlignment(Qt.AlignCenter)
        close_button.mousePressEvent = lambda event: self.hide()
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

        layout.addLayout(top_layout)

        # 创建聊天历史显示区域（使用 QListWidget）
        self.chat_history = QListWidget()
        self.chat_history.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QListWidget::item {
                padding: 0px;
                margin: 2px 0px;
            }
        """)
        self.chat_history.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_history.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.chat_history.setSpacing(2)  # 减小项目间距
        layout.addWidget(self.chat_history)

        # 创建输入框
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("在此输入消息...")
        self.input_text.setMaximumHeight(100)
        self.input_text.installEventFilter(self)
        layout.addWidget(self.input_text)

        # 创建底部控制栏
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(10, 5, 10, 5)
        bottom_layout.setSpacing(10)
        
        # 添加温度设置
        temp_layout = QHBoxLayout()
        temp_label = QLabel("温度:")
        self.temperature_combo = QComboBox()
        self.temperature_combo.setEditable(True)
        self.temperature_combo.addItems(['0.0', '0.3', '0.5', '0.7', '0.9', '1.0'])
        self.temperature_combo.setCurrentText('0.7')
        self.temperature_combo.setValidator(QDoubleValidator(0.0, 2.0, 2))
        self.temperature_combo.setMinimumWidth(60)
        self.temperature_combo.setFixedWidth(60)
        temp_layout.addWidget(temp_label)
        temp_layout.addWidget(self.temperature_combo)
        bottom_layout.addLayout(temp_layout)
        
        # 添加最大令牌数设置
        tokens_layout = QHBoxLayout()
        tokens_label = QLabel("最大令牌:")
        self.max_tokens_combo = QComboBox()
        self.max_tokens_combo.setEditable(True)
        self.max_tokens_combo.addItems(['1000', '2000', '4000', '8000', '16000'])
        self.max_tokens_combo.setCurrentText('2000')
        self.max_tokens_combo.setValidator(QIntValidator(1, 32000))
        self.max_tokens_combo.setMinimumWidth(70)
        self.max_tokens_combo.setFixedWidth(70)
        tokens_layout.addWidget(tokens_label)
        tokens_layout.addWidget(self.max_tokens_combo)
        bottom_layout.addLayout(tokens_layout)
        
        # 添加现有的复选框和按钮
        self.filter_markdown = QCheckBox("过滤 Markdown")
        bottom_layout.addWidget(self.filter_markdown)
        
        self.stream_mode = QCheckBox("流模式")
        self.stream_mode.setChecked(True)
        bottom_layout.addWidget(self.stream_mode)
        
        # 添加清空按钮
        clear_button = QPushButton("清空")
        clear_button.setFixedHeight(25)
        clear_button.clicked.connect(self.clear_chat)
        bottom_layout.addWidget(clear_button)

        # 添加发送按钮
        self.send_button = QPushButton("发送")
        self.send_button.setFixedHeight(25)
        self.send_button.clicked.connect(
            lambda: asyncio.get_event_loop().create_task(self.send_message())
        )
        bottom_layout.addWidget(self.send_button)

        # 设置底部布局的固定高度
        bottom_widget = QWidget()
        bottom_widget.setLayout(bottom_layout)
        bottom_widget.setFixedHeight(35)
        
        layout.addWidget(bottom_widget)

        # 创建一个大小调整手柄
        self.size_grip = QSizeGrip(self)
        self.size_grip.setFixedSize(20, 20)
        
        # 设置初始位置
        self.updateSizeGripPos()
        
        # 设置窗口大小
        self.resize(600, 550)

        # 允许窗口调整大小
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.WindowMaximizeButtonHint)
        
        # 设置最小窗口大小
        self.setMinimumSize(400, 300)

    def updateSizeGripPos(self):
        """更新大小调整手柄的位置"""
        self.size_grip.move(
            self.width() - self.size_grip.width(),
            self.height() - self.size_grip.height()
        )

    def resizeEvent(self, event):
        """处理窗口大小调整事件"""
        super().resizeEvent(event)
        # 更新大小调整手柄位置
        self.updateSizeGripPos()
        # 遍历所有消息项并更新它们的大小
        for i in range(self.chat_history.count()):
            item = self.chat_history.item(i)
            widget = self.chat_history.itemWidget(item)
            if widget:
                widget.resizeEvent(event)
                item.setSizeHint(widget.sizeHint())

    def append_message(self, role: str, content: str):
        """添加消息到聊天历史，使用自定义的 MessageItem"""
        self.messages.append({"role": role, "content": content})

        message_item = MessageItem(role, content)
        list_item = QListWidgetItem()
        
        # 获取消息项的实际���小
        size = message_item.sizeHint()
        # 确保高度足够
        size.setHeight(message_item.height()+15)  # 添加一点间距
        list_item.setSizeHint(size)
        
        self.chat_history.addItem(list_item)
        self.chat_history.setItemWidget(list_item, message_item)

        # 滚动到底部
        self.chat_history.scrollToBottom()
        # 延迟再次滚动，确保完全显示
        QTimer.singleShot(100, self.chat_history.scrollToBottom)

    def mousePressEvent(self, event):
        # 添加右下角调整大小的功能
        if event.position().x() > self.width() - 20 and event.position().y() > self.height() - 20:
            self.resizing = True
            self.resize_start_pos = event.position().toPoint()
            self.resize_start_size = self.size()
        else:
            self.resizing = False
            if event.button() == Qt.LeftButton:
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        event.accept()

    def mouseMoveEvent(self, event):
        if self.resizing:
            # 处理窗口大小调整
            delta = event.position().toPoint() - self.resize_start_pos
            new_size = self.resize_start_size + QSize(delta.x(), delta.y())
            self.resize(new_size)
        elif event.buttons() == Qt.LeftButton:
            # 处理窗口拖动
            self.move(event.globalPosition().toPoint() - self.drag_position)
        event.accept()

    def mouseReleaseEvent(self, event):
        self.resizing = False
        event.accept()

    def eventFilter(self, obj, event):
        if obj is self.input_text and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.NoModifier:
                asyncio.get_event_loop().create_task(self.send_message())
                return True
            elif event.key() == Qt.Key_Return and event.modifiers() == Qt.ShiftModifier:
                cursor = self.input_text.textCursor()
                cursor.insertText('\n')
                return True
        return super().eventFilter(obj, event)

    async def send_message(self):
        """发送消息并获取回复"""
        user_input = self.input_text.toPlainText().strip()
        if not user_input:
            return

        # 保存完整的用户输入
        full_input = user_input
        
        # 清空输入框
        self.input_text.clear()

        # 添加用户消息
        self.append_message("user", full_input)

        try:
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
            
            messages = [{"role": "system", "content": "请直接回答问题，不要使用 markdown 格式。"}]
            messages.extend(self.messages)

            if self.stream_mode.isChecked():
                response_text = ""
                message_widget = None
                first_chunk = True
                
                async for text in self.ai_client.get_response_stream(
                    full_input, 
                    stream=True, 
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                ):
                    if self.should_stop:
                        break

                    if self.filter_markdown.isChecked():
                        from utils.utils import remove_markdown
                        text = remove_markdown(text)

                    response_text += text

                    if first_chunk:
                        self.append_message("assistant", response_text)
                        last_item = self.chat_history.item(self.chat_history.count() - 1)
                        message_widget = self.chat_history.itemWidget(last_item)
                        first_chunk = False
                    else:
                        message_widget.update_content(response_text)
                    
                    self.chat_history.scrollToBottom()
                    await asyncio.sleep(0.01)

                # 流式输出结束后，重新计算并更新消息高度
                if message_widget:
                    # 重新计算高度
                    width = message_widget.label.width()
                    document = message_widget.label.document()
                    document.setTextWidth(width - 20)
                    
                    # 获取最终的文本高度
                    layout = document.documentLayout()
                    size = layout.documentSize()
                    # 正确触发 documentSizeChanged 信号
                    layout.documentSizeChanged.emit(size)
                    
                    # 获取最终的文本高度
                    text_height = size.height()
                    padding = 20
                    total_height = int(text_height + padding)
                    total_height = max(40, total_height)
                    
                    # 更新高度
                    message_widget.label.setFixedHeight(total_height)
                    message_widget.setFixedHeight(total_height + 10)
                    
                    # 更新 QListWidgetItem 的大小
                    last_item.setSizeHint(message_widget.sizeHint())
                    
                    # 确保滚动到底部
                    self.chat_history.scrollToBottom()

                # 更新消息历史
                if len(self.messages) > 0 and self.messages[-1]['role'] == 'assistant':
                    self.messages[-1]['content'] = response_text
                else:
                    self.messages.append({"role": "assistant", "content": response_text})

            else:
                response = await self.ai_client.get_response(
                    full_input, 
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                if self.filter_markdown.isChecked():
                    from utils.utils import remove_markdown
                    response = remove_markdown(response)
                self.append_message("assistant", response)
                self.messages.append({"role": "assistant", "content": response})

        except Exception as e:
            error_msg = f"错误: {str(e)}"
            self.append_message("assistant", error_msg)

    def clear_chat(self):
        """清空聊天历史"""
        self.messages.clear()
        self.chat_history.clear()

    def closeEvent(self, event):
        """重写关闭事件，使窗口关闭时只隐藏而不退出程序"""
        event.ignore()  # 忽略原始的关闭事件
        self.hide()     # 只隐藏窗口
