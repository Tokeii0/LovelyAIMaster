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
import win32com.shell.shell as shell   # type: ignore

import win32gui

import win32process
from win32com.shell import shellcon # type: ignore

from selection_search import SelectionSearchDialog

from hotkey_manager import GlobalHotkey
from floating_button import FloatingStopButton
from utils import remove_markdown
from styles import MAIN_STYLE, CHECKBOX_STYLE

from screenshot import ScreenshotOverlay
import mss
import numpy as np
from PIL import Image
import io

from ai_image_client import AIImageClient
from image_analysis_dialog import ImageAnalysisDialog

# 在程序开始时设置 DPI 感知
ctypes.windll.user32.SetProcessDPIAware()

class InputWindow(QMainWindow):
    # 添加一个自定义信号用于触发划词搜索
    selection_triggered = Signal()
    
    def __init__(self):
        super().__init__()
        try:
            self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            
            # 更新样式表
            self.setStyleSheet(MAIN_STYLE)
            # 设置图标
            self.setWindowIcon(QIcon(r"icons\logo.ico"))

            # 创中心部件
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
            
            # 加过滤markdown的复框
            self.filter_markdown = QCheckBox("过滤Markdown格式")
            self.filter_markdown.setStyleSheet(CHECKBOX_STYLE)
            button_layout.addWidget(self.filter_markdown)
            
            # 添加流模式的复选框
            self.stream_mode = QCheckBox("启用流模式")
            self.stream_mode.setStyleSheet(CHECKBOX_STYLE)
            button_layout.addWidget(self.stream_mode)
            
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
                model=self.config.get('model', 'gpt-4o'),
                api_type=self.config.get('api_type', 'OpenAI'),
                proxy=self.config.get('proxy', '127.0.0.1:1090'),
                proxy_enabled=self.config.get('proxy_enabled', False)  # 添加代理配置
            )
            
            # 在这里添加加载提示词的调用
            self.load_prompts()
            
            # 添加鼠标跟踪
            self.setMouseTracking(True)
            
            # 创建置窗口和提词窗口
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
                
            # 创建划词搜索对话框
            self.selection_dialog = SelectionSearchDialog()
            
            # ��加一个定时器划词搜索
            self.selection_timer = QTimer()
            self.selection_timer.setSingleShot(True)
            self.selection_timer.timeout.connect(self._handle_selection_search_in_main_thread)
            
            # 连接自定义信号到处理函数
            self.selection_triggered.connect(self._handle_selection_search_in_main_thread)
            
            # 修改热键连接方式
            try:
                self.hotkey = GlobalHotkey()
                self.hotkey.triggered.connect(self.show_window)
                self.hotkey.selection_triggered.connect(self._handle_selection_search_in_main_thread)
                self.hotkey.screenshot_triggered.connect(self.show_screenshot_overlay)
                # 添加连续对话热键连接
                self.hotkey.chat_triggered.connect(self.show_chat_window)
                self.hotkey.hotkey_failed.connect(self.handle_hotkey_failure)
            except Exception as e:
                traceback.print_exc()
                
            # 添加窗口显示状态标记
            self.is_window_visible = False
            
            # 确保程序退出时清理热键
            app = QApplication.instance()
            app.aboutToQuit.connect(self.cleanup)
            
            # 优化响应性检查定时器
            self.responsiveness_timer = QTimer()
            #self.responsiveness_timer.timeout.connect(self._check_responsiveness)
            self.responsiveness_timer.start(5000)  # 缩短检查间隔到5秒
            
            # 添加事件处理定时器
            self.event_timer = QTimer()
            self.event_timer.timeout.connect(self._process_events)
            self.event_timer.start(1000)  # 每秒处理一次事件
            
            # 创建截图覆盖层
            self.screenshot_overlay = ScreenshotOverlay()
            self.screenshot_overlay.screenshot_taken.connect(self.handle_screenshot)
            
            # 创建图像AI客户端
            self.ai_image_client = AIImageClient(
                api_key=self.config.get('image_api_key', ''),
                base_url=self.config.get('image_base_url', None),
                model=self.config.get('image_model', 'yi-vision'),
                proxy=self.config.get('image_proxy', '127.0.0.1:1090'),
                proxy_enabled=self.config.get('image_proxy_enabled', False)
            )
            
            # 创建图片分析对话框
            self.image_analysis_dialog = ImageAnalysisDialog()
            # 使用lambda来创建异步任务
            self.image_analysis_dialog.analyze_requested.connect(
                lambda prompt, path: asyncio.create_task(self.handle_image_analysis(prompt, path))
            )
            
            # 添加定期清理计时器
            self.cleanup_timer = QTimer()
            self.cleanup_timer.timeout.connect(self._periodic_cleanup)
            self.cleanup_timer.start(300000)  # 每5分钟清理一次
            
        except Exception as e:
            #print(f"InputWindow初始化失败: {str(e)}")
            traceback.print_exc()
    
    def toggle_debug_window(self):
        if self.debug_window.isVisible():
            self.debug_window.hide()
        else:
            self.debug_window.show()
    
    async def get_ai_response(self, prompt: str):
        """处理流式响应"""
        response_text = ""
        self.should_stop = False
        self.floating_stop_button.show_at_cursor()  # 显示悬浮停止按钮
        
        try:
            async for text in self.ai_client.get_response_stream(prompt, stream=True):
                if self.should_stop:
                    break
                # 根据复选框状态决定是否过滤markdown
                if self.filter_markdown.isChecked():
                    text = remove_markdown(text)
                response_text += text
                self.insert_text_to_cursor(text)
                
        except Exception as e:
            error_msg = f"错误: {str(e)}"
            print(error_msg)
        finally:
            self.floating_stop_button.hide()  # 隐藏悬浮停止按钮
            
        return response_text
    
    def insert_text_to_cursor(self, text, stream_mode=True):
        """入文本到光标位置，支持流式和非流式模式"""
        try:
            # 获取当前激活窗口的句柄和进程ID
            hwnd = GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # 获取进程名称
            process_name = psutil.Process(pid).name().lower()
            
            # 如果是Word，使用Word的COM接
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
                    
                    # 保存当前剪贴板内
                    old_clipboard = pyperclip.paste()
                    
                    # 尝试使用剪贴板方式
                    pyperclip.copy(text)
                    keyboard.press_and_release('ctrl+v')
                    time.sleep(0.01)  # 给予一些时间让粘贴完成
                    
                    # 恢复原来的剪贴板容
                    pyperclip.copy(old_clipboard)
                    return
                except:
                    # 如果剪贴板方式失败，使用逐字符输入
                    SetForegroundWindow(hwnd)  # 再确保窗口在前台
                    time.sleep(0.01)
                    if stream_mode:
                        for char in text:
                            keyboard.write(char)
                            time.sleep(0.01)
                    else:
                        pyperclip.copy(text)
                        keyboard.press_and_release('ctrl+v')
                    return
                
            # 如果是CMD或PowerShell，使用pyautogui
            elif process_name in ['cmd.exe', 'powershell.exe', 'windowsterminal.exe']:
                # 保存当前剪贴板内容
                old_clipboard = pyperclip.paste()
                
                try:
                    # 将文本复制到剪贴板
                    pyperclip.copy(text)
                    # 模拟右键点击（在命令行会粘贴）
                    pyautogui.click(button='right')
                    # 恢复原来的剪贴板内容
                    pyperclip.copy(old_clipboard)
                    return
                except Exception as e:
                    # 如果右键粘贴失败，尝试使用快捷键
                    try:
                        pyautogui.hotkey('ctrl', 'v')
                        pyperclip.copy(old_clipboard)
                        return
                    except:
                        pass
            
            # 对其他用使用PostMessage方式
            if stream_mode:
                # 流式模式：逐字符发送
                for char in text:
                    char_code = ord(char)
                    PostMessage(hwnd, WM_CHAR, char_code, 0)
                    time.sleep(0.001)
            else:
                # 非流式模式：使用剪贴板
                old_clipboard = pyperclip.paste()
                pyperclip.copy(text)
                keyboard.press_and_release('ctrl+v')
                time.sleep(0.01)
                pyperclip.copy(old_clipboard)
                
        except Exception as e:
            error_msg = f"输入文本失败: {str(e)}"
            traceback.print_exc()
    
    def is_vb_window(self, hwnd):
        """检查窗口是否是VB程序窗口"""
        try:
            # 获取窗口类名
            class_name = win32gui.GetClassName(hwnd)
            # VB程序通使用 "ThunderRT6FormDC" 或类似的窗口类名
            return class_name.startswith("ThunderRT") or "VB" in class_name
        except:
            return False
    
    async def process_input(self):
        try:
            # 获取用户输入
            user_input = self.input_text.toPlainText()
            if user_input:
                # 获取选中的预设提���词内容
                preset_content = self.prompts_combo.currentData()
                
                # 组合最终的提示词
                final_prompt = user_input
                if preset_content and self.prompts_combo.currentIndex() > 0:  # 如果选择了预设提示词
                    final_prompt = f"{preset_content}\n{user_input}"
                
                self.input_text.clear()
                self.hide()

                # 根据流模式复选框状态决定使用哪种模式
                if self.stream_mode.isChecked():
                    # 流式式：逐字显示
                    await self.get_ai_response(final_prompt)
                else:
                    # 非流式模式：一次性示
                    response = await self.ai_client.get_response(final_prompt)
                    if self.filter_markdown.isChecked():
                        response = remove_markdown(response)
                    # 一次性插入完整响应
                    self.insert_text_to_cursor(response, stream_mode=False)

        except Exception as e:
            print(f"处理输入败: {str(e)}")
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
            # 使用默认置
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
        """显示或隐窗口的方法"""
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
                
                # 确保窗口不会超出幕边界
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
            
            # 重新初始化文本AI客户端
            self.ai_client = AIClient(
                api_key=config.get('api_key', ''),
                base_url=config.get('base_url', None),
                model=config.get('model', 'yi-lightning'),
                api_type=config.get('api_type', 'OpenAI'),
                proxy=config.get('proxy', '127.0.0.1:1090'),
                proxy_enabled=config.get('proxy_enabled', False)
            )
            
            # 重新初始化图像AI客户端
            self.ai_image_client = AIImageClient(
                api_key=config.get('image_api_key', ''),
                base_url=config.get('image_base_url', None),
                model=config.get('image_model', 'yi-vision'),
                proxy=config.get('image_proxy', '127.0.0.1:1090'),
                proxy_enabled=config.get('image_proxy_enabled', False)
            )
            
            # # 如果热键设置发生变化，重启热键监听
            # if hotkeys_changed:
            #     self.hotkey.load_hotkey_config()
            #     self.hotkey.restart()
                
        except Exception as e:
            traceback.print_exc()

    def load_prompts(self):
        """加载设提示词到下拉框"""
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
            
            # 读取示词文件
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
            #print(f"加载提示词失: {str(e)}")
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
        try:
            # 尝试重置键盘状态
            keyboard.unhook_all()
            time.sleep(0.1)
            
            # 重新初始化热键管理器
            if hasattr(self, 'hotkey'):
                self.hotkey._cleanup_keyboard_state()
        except Exception as e:
            traceback.print_exc()

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

    def cleanup(self):
        """程序退出时的清理工作"""
        try:
            # 停止所有定时器
            for timer in [self.responsiveness_timer, self.event_timer]:
                if timer and timer.isActive():
                    timer.stop()
            
            # 清理热键
            if hasattr(self, 'hotkey'):
                self.hotkey.stop()
                delattr(self, 'hotkey')
            
            # 清理划词搜索热键
            try:
                keyboard.unhook_all()
            except:
                pass
            
            # 理其他资源
            if hasattr(self, 'prompts_window'):
                if hasattr(self.prompts_window, 'save_timer') and self.prompts_window.save_timer.isActive():
                    self.prompts_window._delayed_save()
                if hasattr(self.prompts_window, 'save_timer'):
                    self.prompts_window.save_timer.stop()
            
            # 处理剩余事件
            QApplication.processEvents()
            
            # 停止清理计时器
            if hasattr(self, 'cleanup_timer') and self.cleanup_timer.isActive():
                self.cleanup_timer.stop()
                
            # 确保清理键盘状态
            keyboard.unhook_all()
            
        except Exception as e:
            pass

    def _check_responsiveness(self):
        """检查程序响应性"""
        try:
            if hasattr(self, 'hotkey'):
                # 检查热键状态
                if not self.hotkey.monitor_thread.is_alive() or \
                   time.time() - self.hotkey.last_trigger_time > 15:  # 15秒无响应就重启
                    #print("检测到热键可能失效，尝试重启")
                    #self.hotkey.restart()
                    pass
                
            QApplication.processEvents()  # 确保UI响应
        except Exception as e:
            #print(f"响应性检查失败: {str(e)}")
            # 发生异常时尝试重启热键
            # if hasattr(self, 'hotkey'):
            #     self.hotkey.restart()
            pass

    def _process_events(self):
        """定期处理累的事件"""
        try:
            QApplication.processEvents()
        except Exception as e:
            pass

    def _handle_selection_search_wrapper(self):
        """在主线程中处理划词搜索"""
        try:
            # 使用信号触发主线程处理
            self.selection_triggered.emit()
        except Exception as e:
            print(f"处理划词搜索失败: {str(e)}")
            traceback.print_exc()

    def _handle_selection_search_in_main_thread(self):
        """在主线程中创建异步任务"""
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self.handle_selection_search())
        except Exception as e:
            print(f"创建异步任务失败: {str(e)}")
            traceback.print_exc()

    async def handle_selection_search(self):
        """处理划词搜索"""
        try:
            # 获取选中的文本
            selected_text = self.get_selected_text()
            if not selected_text:
                print("未选中文本")
                return
                
            # 显示对话框
            self.selection_dialog.show_at_cursor()
            self.selection_dialog.text_display.clear()  # 清空之前的内容
            
            # 构建提示词
            prompt = f"解释下面这段文本的含义：\n{selected_text}"
            
            try:
                # 获取AI响应（不过滤Markdown格式）
                async for text in self.ai_client.get_response_stream(prompt, stream=True):
                    if self.selection_dialog.isVisible():  # 只有当对话框可见时才更新
                        self.selection_dialog.set_text(text)
                    else:
                        break
            except Exception as e:
                error_msg = f"获取AI响应失败: {str(e)}"
                print(error_msg)
                if self.selection_dialog.isVisible():
                    self.selection_dialog.set_text(f"错误: {error_msg}")
                
        except Exception as e:
            print(f"划词搜索失败: {str(e)}")
            traceback.print_exc()

    def handle_screenshot(self, image_path):
        """处理截图"""
        print(f"截图已保存到: {image_path}")
        try:
            # 显示图片分析对话框
            if not self.image_analysis_dialog.isVisible():
                self.image_analysis_dialog.set_image(image_path)
                self.image_analysis_dialog.clear_response()
                self.image_analysis_dialog.show()
        except Exception as e:
            print(f"显示图片分析对话框失败: {str(e)}")
            traceback.print_exc()

    async def handle_image_analysis(self, prompt: str, image_path: str):
        """处理图片分析请求"""
        try:
            # 如果对话框已经隐藏，则不继续处理
            if not self.image_analysis_dialog.isVisible():
                return
                
            # 读取图片数据
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # 清空之前的响应
            self.image_analysis_dialog.clear_response()
            
            # 根据对话框中的设置决定使用哪种模式
            if self.image_analysis_dialog.stream_mode.isChecked():
                async for text in self.ai_image_client.get_response_stream(prompt, image_data):
                    # 如果对话框已经隐藏，则停止处理
                    if not self.image_analysis_dialog.isVisible():
                        break
                        
                    if self.image_analysis_dialog.filter_markdown.isChecked():
                        text = remove_markdown(text)
                    self.image_analysis_dialog.append_response(text)
            else:
                response = await self.ai_image_client.get_response(prompt, image_data)
                # 如果对话框已经隐藏，则不显示响应
                if not self.image_analysis_dialog.isVisible():
                    return
                    
                if self.image_analysis_dialog.filter_markdown.isChecked():
                    response = remove_markdown(response)
                self.image_analysis_dialog.append_response(response)
                
        except Exception as e:
            if self.image_analysis_dialog.isVisible():
                error_msg = f"分析图片失败: {str(e)}"
                print(error_msg)
                self.image_analysis_dialog.append_response(f"错误: {error_msg}")
                traceback.print_exc()

    def show_screenshot_overlay(self):
        """显示截图覆盖层"""
        # 如果图片分析对话框已经显示，则隐藏它
        if self.image_analysis_dialog.isVisible():
            self.image_analysis_dialog.hide()
            return
        
        # 否则显示截图覆盖层
        self.screenshot_overlay.show()

    def get_selected_text(self):
        """获取选中的文本"""
        try:
            # 保存当前剪贴板内容
            old_clipboard = pyperclip.paste()
            
            # 模拟 Ctrl+C 复制选中文本
            keyboard.press_and_release('ctrl+c')
            time.sleep(0.1)  # 给系统一些时间来处理复制操作
            
            # 获取剪贴板内容（即选中的文本）
            selected_text = pyperclip.paste()
            
            # 恢复原来的剪贴板内容
            pyperclip.copy(old_clipboard)
            
            # 如果选中的文本为空或者与原剪贴板内容相同，说明可能没有选中文本
            if not selected_text or selected_text == old_clipboard:
                return None
                
            return selected_text.strip()
            
        except Exception as e:
            print(f"获取选中文本失败: {str(e)}")
            traceback.print_exc()
            return None

    def _periodic_cleanup(self):
        """定期清理系统资源"""
        try:
            if hasattr(self, 'hotkey'):
                # 移除对不存在方法的调用
                keyboard.unhook_all()  # 直接使用 keyboard 的 unhook_all 方法
        except Exception as e:
            traceback.print_exc()

    def show_chat_window(self):
        """显示连续对话窗口"""
        try:
            from chat_window import ChatWindow
            if not hasattr(self, 'chat_window'):
                self.chat_window = ChatWindow(self.ai_client)
            
            if self.chat_window.isVisible():
                self.chat_window.hide()
            else:
                # 获取当前鼠标位置
                cursor = QCursor.pos()
                # 设置窗口位置在鼠标光标右下方
                window_x = cursor.x() + 10
                window_y = cursor.y() + 10
                
                # 确保窗口不会超出屏幕边界
                screen = QApplication.primaryScreen().geometry()
                if window_x + self.chat_window.width() > screen.width():
                    window_x = screen.width() - self.chat_window.width()
                if window_y + self.chat_window.height() > screen.height():
                    window_y = screen.height() - self.chat_window.height()
                
                self.chat_window.move(window_x, window_y)
                self.chat_window.show()
                self.chat_window.raise_()
                self.chat_window.activateWindow()
                
        except Exception as e:
            print(f"显示连续对话窗口失败: {str(e)}")
            traceback.print_exc()

def check_single_instance():
    """检查是否已有实例在运行"""
    try:
        from win32event import CreateMutex
        from win32api import CloseHandle, GetLastError
        from winerror import ERROR_ALREADY_EXISTS
        
        mutex = CreateMutex(None, False, "YourAppMutexName")
        if GetLastError() == ERROR_ALREADY_EXISTS:
            CloseHandle(mutex)
            return False
        return True
    except:
        return True

# 修改 main() 函数
async def main():
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        window = InputWindow()
        
        # 使用 qasync 创建事件循环
        try:
            loop = qasync.QEventLoop(app)
            asyncio.set_event_loop(loop)
            
            # 添加定期清理任务
            async def cleanup_routine():
                while True:
                    await asyncio.sleep(60)  # 每60秒执行一次
                    QApplication.processEvents()  # 处理积累的事件
                    
            # 启动清理任务
            loop.create_task(cleanup_routine())
            
            # 运行事件循环
            with loop:
                loop.run_forever()
                
        except Exception as e:
            traceback.print_exc()
            
    except Exception as e:
        traceback.print_exc()

# 修改程序入口点
if __name__ == "__main__":
    import os
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"
    try:
        if not check_single_instance():
            print("程序已在运行！")
            sys.exit(0)
        
        asyncio.run(main())
    except Exception as e:
        print(f"程序启动失败: {str(e)}")
        traceback.print_exc()