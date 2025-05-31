from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLabel,
                             QLineEdit, QPushButton, QHBoxLayout, QApplication, QComboBox,
                             QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
import subprocess
import os
import asyncio
from services.ai_client import AIClient
import json
import qasync
from .base_window import BaseWindow

class ResultWindow(BaseWindow):
    """结果展示窗口"""
    def __init__(self):
        super().__init__()
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 10)
        layout.setSpacing(8)
        
        # 顶部布局（包含关闭按钮）
        top_layout = QHBoxLayout()
        top_layout.setSpacing(0)
        top_layout.addStretch()
        
        # 使用基类的关闭按钮
        self.create_close_button(top_layout)
        layout.addLayout(top_layout)
        
        # 结果列表
        self.result_list = QListWidget()
        self.result_list.itemDoubleClicked.connect(self.execute_result)
        layout.addWidget(self.result_list)
        
        # 设置窗口大小
        self.resize(500, 400)

    def set_results(self, results):
        """设置结果列表"""
        self.result_list.clear()
        for result in results:
            item = QListWidgetItem(result)
            self.result_list.addItem(item)

    def execute_result(self, item):
        """执行双击的结果"""
        try:
            command = item.text()
            if os.path.exists(command):
                subprocess.Popen(f'cmd /c "{command}"')
            else:
                subprocess.Popen(f'cmd /c "{os.path.dirname(command)}"')
            # 执行完命令后隐藏窗口
            self.hide()
        except Exception as e:
            print(f"执行结果失败: {str(e)}")



    def showEvent(self, event):
        # 在显示窗口时居中显示
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        super().showEvent(event)

class CommandWindow(BaseWindow):
    command_executed = Signal()

    def __init__(self):
        super().__init__()
        
        # 初始化 AI 客户端
        self.init_ai_client()
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 10)
        layout.setSpacing(8)
        
        # 顶部布局（包含关闭按钮）
        top_layout = QHBoxLayout()
        top_layout.setSpacing(0)
        top_layout.addStretch()
        
        # 使用基类的关闭按钮
        self.create_close_button(top_layout)
        layout.addLayout(top_layout)
        
        # 提示词下拉框
        self.prompt_combo = QComboBox()
        self.prompt_combo.addItem("选择提示词...")
        self.load_prompts()
        layout.addWidget(self.prompt_combo)
        
        # 命令输入框
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("输入命令...")
        self.command_input.setMinimumHeight(32)
        self.command_input.returnPressed.connect(self.on_execute_command)
        layout.addWidget(self.command_input)
        
        # 提交按钮
        submit_button = QPushButton("执行")
        submit_button.setMinimumHeight(30)
        submit_button.clicked.connect(self.on_execute_command)
        layout.addWidget(submit_button)
        
        # 设置窗口大小
        self.resize(400, 200)
        
        # 创建结果窗口
        self.result_window = ResultWindow()

    def init_ai_client(self):
        """初始化 AI 客户端"""
        try:
            with open('config/config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            self.ai_client = AIClient(
                api_key=config.get('api_key', ''),
                base_url=config.get('base_url', None),
                model=config.get('model', 'gpt-4o'),
                api_type=config.get('api_type', 'OpenAI'),
                proxy=config.get('proxy', '127.0.0.1:1090'),
                proxy_enabled=config.get('proxy_enabled', False)
            )
            
            self.es_path = config.get('es_path', 'C:\\Program Files\\Everything\\es.exe')
        except Exception as e:
            print(f"初始化 AI 客户端失败: {str(e)}")

    def load_prompts(self):
        """加载提示词列表"""
        try:
            if os.path.exists('config/prompts.json'):
                with open('config/prompts.json', 'r', encoding='utf-8') as f:
                    prompts = json.load(f)
                    for prompt in prompts:
                        self.prompt_combo.addItem(prompt['title'], prompt['content'])
        except Exception as e:
            print(f"加载提示词失败: {str(e)}")

    def on_execute_command(self):
        """处理执行命令的点击事件"""
        asyncio.create_task(self.execute_command())

    async def execute_command(self):
        """执行命令"""
        command = self.command_input.text().strip()
        if not command:
            return
            
        try:
            # 获取选中的提示词
            current_index = self.prompt_combo.currentIndex()
            if current_index > 0:  # 0 是 "选择提示词..." 选项
                prompt_content = self.prompt_combo.currentData()
                messages = [
                    {
                        "role": "system",
                        "content": "请直接回答问题，不要使用markdown格式。每个结果占一行。"
                    },
                    {
                        "role": "user",
                        "content": prompt_content
                    },
                    {
                        "role": "user",
                        "content": command
                    }
                ]
            else:
                messages = None
            
            # 获取 AI 响应
            response = await self.ai_client.get_response(command, messages=messages)
            print(f"AI 响应: {response}")
            
            # 使用 ES 搜索并获取结果
            if os.path.exists(self.es_path):
                # 构建 ES 命令，添加 -r 参数以获取原始输出
                es_command = f'"{self.es_path}" "{response}" -r "^(?!.*卸载).*"'
                try:
                    # 执行 ES 命令并获取输出，使用 GBK 编码
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                    
                    process = subprocess.Popen(
                        es_command, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        startupinfo=startupinfo,
                        text=True,
                        encoding='gbk',  # 使用 GBK 编码
                        errors='ignore'   # 忽略无法解码的字符
                    )
                    stdout, stderr = process.communicate()
                    
                    # 处理搜索结果
                    if stdout:
                        # 将结果按行分割并过滤空行
                        results = [line.strip() for line in stdout.split('\n') if line.strip()]
                        
                        # 显示结果窗口
                        self.result_window.set_results(results)
                        self.result_window.show()
                        self.result_window.raise_()
                        self.result_window.activateWindow()
                    else:
                        # 如果没有搜索结果，显示提示信息
                        self.result_window.set_results(["未找到匹配的文件"])
                        self.result_window.show()
                        self.result_window.raise_()
                        self.result_window.activateWindow()
                        
                except Exception as e:
                    print(f"执行 ES 命令失败: {str(e)}")
                    self.command_executed.emit(f"执行 ES 命令失败: {str(e)}")
            else:
                print(f"ES 可执行文件不存在: {self.es_path}")
                self.command_executed.emit(f"ES 可执行文件不存在: {self.es_path}")
                
            # 清空输入框并隐藏命令窗口
            self.command_input.clear()
            self.hide()
            
        except Exception as e:
            print(f"执行命令失败: {str(e)}")
            self.command_executed.emit(f"执行失败: {str(e)}")



    def showEvent(self, event):
        # 在显示窗口时居中显示
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        # 清空输入框并聚焦
        self.command_input.clear()
        self.command_input.setFocus()
        super().showEvent(event)