from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel, QCheckBox, QComboBox
from PySide6.QtCore import Qt, Signal, QObject, QEvent,QTimer
from PySide6.QtGui import QCursor,QIcon
import keyboard
import pyautogui
import sys
import time
from threading import Thread
import asyncio
import json
from ai_client import AIClient
import qasync
import ctypes
import pyperclip
from win32con import WM_CHAR
from win32api import PostMessage
from win32gui import GetForegroundWindow, SetForegroundWindow
import re
from win32com import client as win32com_client
import win32process
import psutil
from tray_icon import SystemTrayIcon
from settings_window import SettingsWindow
from prompts_window import PromptsWindow
import traceback
import os
import threading
import win32com.shell.shell as shell   # type: ignore
import win32con
import win32event
import win32gui

import win32process
from win32com.shell import shellcon # type: ignore

# 在程序开始时设置 DPI 感知
ctypes.windll.user32.SetProcessDPIAware()

class GlobalHotkey(QObject):
    triggered = Signal()
    hotkey_failed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.hotkey_registered = False
        self.retry_count = 0
        self.max_retries = 3
        self.lock = threading.Lock()
        self._start_monitoring()
    
    def _start_monitoring(self):
        """启动热键监听线程"""
        try:
            self._clean_existing_hotkey()
            self.monitor_thread = Thread(target=self._monitor_hotkey, daemon=True)
            self.monitor_thread.start()
        except Exception as e:
            #print(f"启动热键监听线程失败: {str(e)}")
            self.hotkey_failed.emit(str(e))
    
    def _clean_existing_hotkey(self):
        """清理已存在的热键"""
        try:
            keyboard.unhook_all()
            time.sleep(0.1)
        except Exception as e:
            pass
            #print(f"清理现有热键失败: {str(e)}")
    
    def _monitor_hotkey(self):
        """热键监听主循环"""
        while self.running:
            try:
                with self.lock:
                    if not self.hotkey_registered:
                        # 注册两个热键组合
                        keyboard.add_hotkey('alt+q', self._on_hotkey_triggered, suppress=True)
                        keyboard.add_hotkey('alt+w', self._on_hotkey_triggered, suppress=True)
                        self.hotkey_registered = True
                        self.retry_count = 0
                        #print("热键注册成功: Alt+Q  Alt+W")
                
                # 使用简单的循环保持线程运行
                while self.running and self.hotkey_registered:
                    time.sleep(0.1)
                    
            except Exception as e:
                #print(f"热键监听错误: {str(e)}")
                traceback.print_exc()  # 添加详细的错误跟踪
                self.hotkey_registered = False
                self.retry_count += 1
                
                if self.retry_count <= self.max_retries:
                    #print(f"尝试重新注册热键 (尝试 {self.retry_count}/{self.max_retries})")
                    time.sleep(2)
                else:
                    #print("热键注册失败次数过多，停止重试")
                    self.hotkey_failed.emit(str(e))
                    break
    
    def _on_hotkey_triggered(self):
        """热键触发时的处理函数"""
        try:
            #print("热键被触发")  # 添加调试输出
            # 直接发送信号
            self.triggered.emit()
            #print("信号已发送")  # 添加调试输出
        except Exception as e:
            #print(f"热键触发处理失败: {str(e)}")
            traceback.print_exc()
    
    def restart(self):
        """重新启动热键监听"""
        with self.lock:
            self.stop()
            time.sleep(1)
            self.running = True
            self.hotkey_registered = False
            self.retry_count = 0
            self._clean_existing_hotkey()
            self._start_monitoring()
    
    def stop(self):
        """停止热键监听"""
        with self.lock:
            self.running = False
            self.hotkey_registered = False
            try:
                keyboard.unhook_all()
                time.sleep(0.1)
            except:
                pass

class FloatingStopButton(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stop_button = QPushButton("停止")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setStyleSheet("""
            QPushButton#stopButton {
                background-color: rgba(255, 68, 68, 80%);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
                font-size: 13px;
                min-height: 25px;
                min-width: 60px;
            }
            QPushButton#stopButton:hover {
                background-color: rgba(255, 38, 38, 80%);
            }
        """)
        
        layout.addWidget(self.stop_button)
        self.resize(70, 35)

    def show_at_cursor(self):
        cursor_pos = QCursor.pos()
        self.move(cursor_pos.x() + 20, cursor_pos.y() + 20)
        self.show()

def remove_markdown(text: str) -> str:
    """移除markdown格式"""
    # 移除代码块
    text = re.sub(r'```[\s\S]*?```', '', text)
    # 移除行内代码
    text = re.sub(r'`[^`]*`', '', text)
    # 移除标题
    text = re.sub(r'#{1,6}\s.*\n', '', text)
    # 移除粗体和斜体
    text = re.sub(r'\*\*.*?\*\*', '', text)
    text = re.sub(r'\*.*?\*', '', text)
    text = re.sub(r'__.*?__', '', text)
    text = re.sub(r'_.*?_', '', text)
    # 移除列表标记
    text = re.sub(r'^\s*[-*+]\s', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s', '', text, flags=re.MULTILINE)
    # 移除链接
    text = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', text)
    # 移除图片
    text = re.sub(r'!\[([^\]]*)\]\([^\)]*\)', '', text)
    # 移除引用
    text = re.sub(r'^\s*>\s', '', text, flags=re.MULTILINE)
    # 移除水平线
    text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)
    # 移除表格
    text = re.sub(r'\|.*\|', '', text)
    text = re.sub(r'^\s*[-:|\s]+$', '', text, flags=re.MULTILINE)
    # 清理多余的空行
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

class InputWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            
            # 更新样式表
            self.setStyleSheet("""
                QMainWindow {
                    background: transparent;
                }
                QWidget#centralWidget {
                    background-color: rgba(245, 245, 245, 90%);
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
                    margin: 2px;
                }
                QPushButton#closeButton:hover {
                    background-color: rgba(255, 68, 68, 80%);
                    color: white;
                }
            """)
            
            # 创建中心部件
            central_widget = QWidget()
            central_widget.setObjectName("centralWidget")
            self.setCentralWidget(central_widget)
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(10, 5, 10, 10)
            main_layout.setSpacing(10)
            
            # 创建顶部布局（只包含关闭按钮）
            top_layout = QHBoxLayout()
            top_layout.setSpacing(0)
            
            # 添加弹性空间
            top_layout.addStretch()
            
            # 添加关闭按钮
            close_button = QPushButton("×")
            close_button.setObjectName("closeButton")
            close_button.clicked.connect(self.hide)
            top_layout.addWidget(close_button)
            
            main_layout.addLayout(top_layout)
            
            # 创建提示词下拉框
            prompts_layout = QHBoxLayout()
            prompts_label = QLabel("预设提示词:")
            self.prompts_combo = QComboBox()
            self.prompts_combo.currentIndexChanged.connect(self.on_prompt_selected)
            prompts_layout.addWidget(prompts_label)
            prompts_layout.addWidget(self.prompts_combo)
            main_layout.addLayout(prompts_layout)
            
            # 创建输入框
            self.input_text = QTextEdit()
            self.input_text.setPlaceholderText("请输入提示词...")
            self.input_text.setMinimumHeight(100)
            self.input_text.setMaximumHeight(150)
            # 加回车键处理
            self.input_text.installEventFilter(self)
            main_layout.addWidget(self.input_text)
            
            # 创建复选框和发送按钮的水平布局
            button_layout = QHBoxLayout()
            
            # 添加过滤markdown的复选框
            self.filter_markdown = QCheckBox("过滤Markdown格式")
            self.filter_markdown.setStyleSheet("""
                QCheckBox {
                    color: #666;
                    font-size: 12px;
                }
                QCheckBox::indicator {
                    width: 15px;
                    height: 15px;
                }
                QCheckBox::indicator:unchecked {
                    border: 1px solid #999;
                    background: rgba(255, 255, 255, 80%);
                    border-radius: 3px;
                }
                QCheckBox::indicator:checked {
                    border: 1px solid #4A90E2;
                    background: rgba(74, 144, 226, 80%);
                    border-radius: 3px;
                }
            """)
            button_layout.addWidget(self.filter_markdown)
            
            # 添加弹性空间
            button_layout.addStretch()
            
            # 创建发送按钮
            self.send_button = QPushButton("发送")
            # 使用 lambda 来创建异步任务
            self.send_button.clicked.connect(
                lambda: asyncio.get_event_loop().create_task(self.process_input())
            )
            button_layout.addWidget(self.send_button)
            
            main_layout.addLayout(button_layout)
            
            # 创建悬浮停止按钮
            self.floating_stop_button = FloatingStopButton()
            self.floating_stop_button.stop_button.clicked.connect(self.stop_response)
            
            # 添加停止标志
            self.should_stop = False
            
            # 更新样式表，加停止按钮样式
            self.setStyleSheet(self.styleSheet() + """
                QPushButton#stopButton {
                    background-color: rgba(255, 68, 68, 80%);
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 5px 15px;
                    font-size: 13px;
                    min-height: 25px;
                }
                QPushButton#stopButton:hover {
                    background-color: rgba(255, 38, 38, 80%);
                }
            """)
            
            # 设置窗口大小
            self.resize(300, 200)
            
            # 加载配置和化AI客户端
            self.load_config()
            self.ai_client = AIClient(
                api_key=self.config.get('api_key', ''),
                base_url=self.config.get('base_url', None),
                model=self.config.get('model', 'yi-lightning'),
                api_type=self.config.get('api_type', 'OpenAI'),
                proxy=self.config.get('proxy', '127.0.0.1:1090'),
                proxy_enabled=self.config.get('proxy_enabled', False)  # 添加代理配置
            )
            
            # 在这里添加加载提示词的调用
            self.load_prompts()
            
            # 添加鼠标跟踪
            self.setMouseTracking(True)
            
            # 创建置窗口和提示词窗口
            self.settings_window = SettingsWindow()
            self.settings_window.setWindowFlags(
                self.settings_window.windowFlags() | 
                Qt.WindowStaysOnTopHint | 
                Qt.WindowSystemMenuHint | 
                Qt.WindowCloseButtonHint
            )
            self.prompts_window = PromptsWindow()
            
            # 连接设置窗口的信号
            self.settings_window.settings_saved.connect(self.on_settings_saved)
            self.prompts_window.prompts_updated.connect(self.load_prompts)
            
            # 创建系统托盘图标
            try:
                self.tray_icon = SystemTrayIcon(self)
                self.tray_icon.show_settings_signal.connect(lambda: self.settings_window.show())
                self.tray_icon.show_prompts_signal.connect(lambda: self.prompts_window.show())
                self.tray_icon.quit_signal.connect(lambda: QApplication.instance().quit())
                #print("盘图标创建成功")
            except Exception as e:
                #print(f"托盘图标创建失败: {str(e)}")
                traceback.print_exc()
                
            # 修改热键连接方式
            try:
                self.hotkey = GlobalHotkey()
                # 直接连接到 show_window 方法，不使用 QTimer
                self.hotkey.triggered.connect(self.show_window)
                self.hotkey.hotkey_failed.connect(self.handle_hotkey_failure)
                #print("全局热键监听器创建成功 - Alt+Q/Alt+W")
            except Exception as e:
                #print(f"全局热键监听器创建失败: {str(e)}")
                traceback.print_exc()
                
            # 添加窗口显示状态标记
            self.is_window_visible = False
            
        except Exception as e:
            #print(f"InputWindow初始化失败: {str(e)}")
            traceback.print_exc()
    
    def toggle_debug_window(self):
        if self.debug_window.isVisible():
            self.debug_window.hide()
        else:
            self.debug_window.show()
    
    async def get_ai_response(self, prompt):
        response_text = ""
        #print(f"用户输入: {prompt}")
        self.should_stop = False
        self.floating_stop_button.show_at_cursor()  # 显示悬浮停止按钮
        
        try:
            async for text in self.ai_client.get_response_stream(prompt):
                if self.should_stop:
                    break
                # 根据复选框状态决定是否过滤markdown
                if self.filter_markdown.isChecked():
                    text = remove_markdown(text)
                response_text += text
                self.insert_text_to_cursor(text)
                #print(text, end='', flush=True)
                
        except Exception as e:
            error_msg = f"错误: {str(e)}"
            #print(error_msg)
        finally:
            self.floating_stop_button.hide()  # 隐藏悬浮停止按钮
            
        #print("\n响应完成")
        return response_text
    
    def insert_text_to_cursor(self, text):
        try:
            # 获取当前激活窗口的句柄和进程ID
            hwnd = GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # 获取进程名称
            process_name = psutil.Process(pid).name().lower()
            
            # 如果是Word，使用Word的COM接口
            if 'winword' in process_name:
                try:
                    word = win32com_client.Dispatch("Word.Application")
                    if word.Documents.Count > 0:
                        word.Selection.TypeText(text)
                    return
                except Exception as e:
                    pass
            
            # 如果是VB程序，使用SendInput模拟键盘输入
            elif process_name.endswith('.exe') and self.is_vb_window(hwnd):
                try:
                    # 确保VB窗口在前台
                    SetForegroundWindow(hwnd)
                    time.sleep(0.1)  # 给窗口一些时间来获取焦点
                    
                    # 保存当前剪贴板内容
                    old_clipboard = pyperclip.paste()
                    
                    # 尝试使用剪贴板方式
                    pyperclip.copy(text)
                    keyboard.press_and_release('ctrl+v')
                    time.sleep(0.01)  # 给予一些时间让粘贴完成
                    
                    # 恢复原来的剪贴板内容
                    pyperclip.copy(old_clipboard)
                    return
                except:
                    # 如果剪贴板方式失败，使用逐字符输入
                    SetForegroundWindow(hwnd)  # 再次确保窗口在前台
                    time.sleep(0.01)
                    for char in text:
                        keyboard.write(char)
                        time.sleep(0.01)  # 添加少量延迟以确保输入稳定
                    return
                
            # 如果是CMD或PowerShell，使用pyautogui
            elif process_name in ['cmd.exe', 'powershell.exe', 'windowsterminal.exe']:
                # 保存当前剪贴板内容
                old_clipboard = pyperclip.paste()
                
                try:
                    # 将文本复制到剪贴板
                    pyperclip.copy(text)
                    # 模拟右键点击（在命令行中会粘贴）
                    pyautogui.click(button='right')
                    # 恢复原来的剪贴板内容
                    pyperclip.copy(old_clipboard)
                    return
                except Exception as e:
                    #print(f"CMD输入失败: {str(e)}")
                    # 如果右键粘贴失败，尝试使用快捷键
                    try:
                        pyautogui.hotkey('ctrl', 'v')
                        pyperclip.copy(old_clipboard)
                        return
                    except:
                        pass
            
            # 对其他应用使用PostMessage方式
            for char in text:
                char_code = ord(char)
                PostMessage(hwnd, WM_CHAR, char_code, 0)
                time.sleep(0.001)
                
        except Exception as e:
            error_msg = f"输入文本失败: {str(e)}"
            traceback.print_exc()
    
    def is_vb_window(self, hwnd):
        """检查窗口是否是VB程序窗口"""
        try:
            # 获取窗口类名
            class_name = win32gui.GetClassName(hwnd)
            # VB程序通常使用 "ThunderRT6FormDC" 或类似的窗口类名
            return class_name.startswith("ThunderRT") or "VB" in class_name
        except:
            return False
    
    async def process_input(self):
        try:
            # 获取用户输入
            user_input = self.input_text.toPlainText()
            if user_input:
                # 获取前选中的预设提示词内容
                preset_content = self.prompts_combo.currentData()
                
                # 组合最终的提示词
                final_prompt = user_input
                if preset_content and self.prompts_combo.currentIndex() > 0:  # 如果选择了预设提示词
                    final_prompt = f"{preset_content}\n{user_input}"
                
                self.input_text.clear()
                self.hide()
                await self.get_ai_response(final_prompt)
        except Exception as e:
            #print(f"处理输入失败: {str(e)}")
            traceback.print_exc()
    
    def load_config(self):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                # 确保布尔值正确
                if 'proxy_enabled' in self.config:
                    self.config['proxy_enabled'] = bool(self.config['proxy_enabled'])
        except Exception as e:
            error_msg = f"加载配置文件失败: {str(e)}"
            #print(error_msg)
            # 使用默认配置
            self.config = {
                'api_key': '',
                'base_url': 'https://api.openai.com/v1',
                'model': 'gpt-4o-mini',
                'api_type': 'OpenAI',
                'proxy_enabled': False,
                'proxy': '127.0.0.1:1090'
            }
            # 创建默认配置文件
            try:
                with open('config.json', 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
            except Exception as write_error:
                #print(f"创建默认配置文件失败: {str(write_error)}")
                pass
    
    def show_window(self):
        """显示或隐藏窗口的方法"""
        #print("触发显示/隐藏窗口")
        try:
            if self.isVisible():
                #print("窗口当前可见，准备隐藏")
                self.hide()
            else:
                #print("窗口当前隐藏，准备显示")
                # 获取当前鼠标位置
                cursor = QCursor.pos()
                # 设置窗口位置在鼠标光标右下方
                window_x = cursor.x() + 10
                window_y = cursor.y() + 10
                
                # 确保窗口不会超出屏幕边界
                screen = QApplication.primaryScreen().geometry()
                if window_x + self.width() > screen.width():
                    window_x = screen.width() - self.width()
                if window_y + self.height() > screen.height():
                    window_y = screen.height() - self.height()
                
                self.move(window_x, window_y)
                super().show()
                self.raise_()
                self.activateWindow()
                self.input_text.setFocus()
                #print(f"窗口已显示在位置: ({window_x}, {window_y})")
        except Exception as e:
            #print(f"显示/隐藏窗口失败: {str(e)}")
            traceback.print_exc()

    def hide(self):
        """重写hide方法以更新状态"""
        super().hide()
        self.is_window_visible = False
        #print("窗口已隐藏")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def eventFilter(self, obj, event):
        try:
            if obj is self.input_text and event.type() == QEvent.Type.KeyPress:
                if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.NoModifier:
                    # 普通回车键处理发送
                    try:
                        # 使用 asyncio.create_task 来处理异步函数
                        loop = asyncio.get_event_loop()
                        loop.create_task(self.process_input())
                    except Exception as e:
                        traceback.print_exc()
                    return True
                elif event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                    # Shift+回车插入换行
                    cursor = self.input_text.textCursor()
                    cursor.insertText('\n')
                    return True
            return super().eventFilter(obj, event)
        except Exception as e:
            traceback.print_exc()
            return False

    def stop_response(self):
        self.should_stop = True
        self.floating_stop_button.hide()
        #print("\n已停止输出")

    def on_settings_saved(self, settings_data):
        """当设置被保存时更新配置和AI客户端"""
        try:
            config = settings_data["config"]
            hotkeys_changed = settings_data["hotkeys_changed"]
            
            # 更新配置
            self.config = config
            
            # 重新初始化AI客户端
            self.ai_client = AIClient(
                api_key=config.get('api_key', ''),
                base_url=config.get('base_url', None),
                model=config.get('model', 'yi-lightning'),
                api_type=config.get('api_type', 'OpenAI'),
                proxy=config.get('proxy', '127.0.0.1:1090'),
                proxy_enabled=config.get('proxy_enabled', False)
            )
            
            # 如果热键设置发生变化，重启热键监听
            if hotkeys_changed:
                self.hotkey.restart()
                
        except Exception as e:
            traceback.print_exc()

    def load_prompts(self):
        """加载预设提示词到下拉框"""
        try:
            # 检查文件是存在
            if not os.path.exists('prompts.json'):
                #print("提示词文件不存在，创建默认文件")
                default_prompts = [
                    {
                        "title": "例提示词",
                        "content": "这是一个示例提示词"
                    }
                ]
                with open('prompts.json', 'w', encoding='utf-8') as f:
                    json.dump(default_prompts, f, ensure_ascii=False, indent=4)
            
            # 读取提示词文件
            with open('prompts.json', 'r', encoding='utf-8') as f:
                prompts = json.load(f)
                self.prompts_combo.clear()
                self.prompts_combo.addItem("选择提示词...")  # 添加默认选项
                for prompt in prompts:
                    self.prompts_combo.addItem(prompt['title'], prompt['content'])
                #print(f"成功加载 {len(prompts)} 个提示词")
        except json.JSONDecodeError as e:
            print(f"提示词文件格式错误: {str(e)}")
        except Exception as e:
            #print(f"加载提示词失败: {str(e)}")
            traceback.print_exc()
    
    def on_prompt_selected(self, index):
        """当选择提示词时触发"""
        if index > 0:  # 跳过默认选项
            # 不再设置输入框的内容
            self.input_text.setFocus()  # 将焦点设置到输入框

    def show_settings(self):
        """显示设置窗口"""
        try:
            print("正在尝试显示设置窗口...")
            print(f"设置窗口当前状态: visible={self.settings_window.isVisible()}")
            
            if not self.settings_window.isVisible():
                self.settings_window.show()
                print("设置窗口.show()已调用")
                self.settings_window.raise_()
                print("设置窗口.raise()已调用")
                self.settings_window.activateWindow()
                print("设置窗口.activateWindow()已调用")
                
            print("设置窗口显示流程完成")
        except Exception as e:
            print(f"显示设置窗口时出错: {str(e)}")
            traceback.print_exc()
    
    def show_prompts(self):
        """显示提示词管理窗口"""
        self.prompts_window.show()

    def handle_hotkey_failure(self, error_msg):
        """处理热键失败的情况"""
        #print(f"热键失败: {error_msg}")
        # 使用 QTimer 延迟重启
        QTimer.singleShot(2000, self._delayed_restart_hotkey)
    
    def _delayed_restart_hotkey(self):
        try:
            self.hotkey.restart()
            #print("已重新启动热键监听")
        except Exception as e:
            print(f"重启热键监听失败: {str(e)}")
    
    def closeEvent(self, event):
        """窗口关闭时清理热键"""
        try:
            self.hotkey.stop()
        except:
            pass
        super().closeEvent(event)

# 修改 main() 函数
async def main():
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        window = InputWindow()
        
        # 使用 qasync 创建事件循环
        try:
            loop = qasync.QEventLoop(app)
            asyncio.set_event_loop(loop)
            #print("事件循环创建成功")
            
            # 运行事件循环
            with loop:
                loop.run_forever()  # 使用 loop.run_forever()
        except Exception as e:
            #print(f"事件循环错误: {str(e)}")
            traceback.print_exc()
            
    except Exception as e:
        #print(f"main函数错误: {str(e)}")
        traceback.print_exc()

# 修改程序入口点
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"程序启动失败: {str(e)}")
        traceback.print_exc()