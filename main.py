import sys
import time
import os
import asyncio
import ctypes
import json
import traceback

# PySide6 imports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QPushButton,
    QHBoxLayout, QLabel, QCheckBox, QComboBox, QSystemTrayIcon
)
from PySide6.QtCore import Qt, Signal, QEvent, QTimer
from PySide6.QtGui import QCursor, QIcon, QDoubleValidator, QIntValidator

# Third-party imports
import keyboard
import pyautogui
import pyperclip
import psutil
import qasync

# Windows API imports
from win32con import WM_CHAR, WM_COPY
import win32clipboard
from win32api import PostMessage
from win32gui import GetForegroundWindow, SetForegroundWindow, GetClassName
from win32com import client as win32com_client
import win32con
import win32gui
import win32api
from win32process import GetWindowThreadProcessId, AttachThreadInput
import win32process

# Local imports
from services.ai_client import AIClient
from ui.tray_icon import SystemTrayIcon
from ui.settings_window import SettingsWindow
from ui.prompts_window import PromptsWindow
from ui.selection_search import SelectionSearchDialog
from utils.hotkey_manager import GlobalHotkey
from ui.floating_button import FloatingStopButton
from utils.utils import remove_markdown
from ui.styles import MAIN_STYLE, CHECKBOX_STYLE
from utils.screenshot import ScreenshotOverlay
from services.ai_image_client import AIImageClient
from ui.image_analysis_dialog import ImageAnalysisDialog
from ui.selection_keywords_window import SelectionKeywordsWindow
from ui.command_window import CommandWindow
from ui.prompt_input_window import PromptInputWindow

# 在程序开始时设置 DPI 感知
ctypes.windll.user32.SetProcessDPIAware()

class InputWindow(QMainWindow):
    selection_triggered = Signal()

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_config()
        self.init_ai_clients()
        self.init_tray_icon()
        self.init_selection_dialog()
        self.init_hotkeys()
        self.init_timers()
        self.init_screenshot_overlay()
        self.init_image_analysis()
        self.init_selection_keywords_window()
        self.init_command_window()
        self.init_prompt_input_window()
        self.is_window_visible = False
        self.drag_position = None
        app = QApplication.instance()
        app.aboutToQuit.connect(self.cleanup)

    def init_ui(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(MAIN_STYLE)
        self.setWindowIcon(QIcon(r"icons\logo.ico"))
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 5, 10, 10)
        main_layout.setSpacing(10)
        # 顶部布局和关闭按钮
        top_layout = QHBoxLayout()
        top_layout.setSpacing(0)
        top_layout.addStretch()
        close_button = QPushButton("×")
        close_button.setObjectName("closeButton")
        close_button.clicked.connect(self.hide)
        top_layout.addWidget(close_button)
        main_layout.addLayout(top_layout)
        # 流模式设置
        stream_layout = QHBoxLayout()
        self.stream_mode = QCheckBox("启用流模式")
        self.stream_mode.setStyleSheet(CHECKBOX_STYLE)
        self.stream_mode.setChecked(True)
        stream_layout.addWidget(self.stream_mode)
        stream_layout.addStretch()
        
        # 打开提示词输入窗口按钮
        self.open_prompt_button = QPushButton("打开提示词输入")
        self.open_prompt_button.clicked.connect(self.show_prompt_input_window)
        stream_layout.addWidget(self.open_prompt_button)
        
        main_layout.addLayout(stream_layout)
        # 悬浮停止按钮
        self.floating_stop_button = FloatingStopButton()
        self.floating_stop_button.stop_button.clicked.connect(self.stop_response)
        # 设置窗口大小
        self.resize(300, 200)
        # 更新样式表
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
        # 添加鼠标跟踪
        self.setMouseTracking(True)
        # 创建设置窗口和提示词窗口
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
        # 提示词功能已移到独立的提示词输入窗口

    def init_ai_clients(self):
        self.ai_client = AIClient(
            api_key=self.config.get('api_key', ''),
            base_url=self.config.get('base_url', None),
            model=self.config.get('model', 'gpt-4o'),
            api_type=self.config.get('api_type', 'OpenAI'),
            proxy=self.config.get('proxy', '127.0.0.1:1090'),
            proxy_enabled=self.config.get('proxy_enabled', False)
        )
        self.ai_image_client = AIImageClient(
            api_key=self.config.get('image_api_key', ''),
            base_url=self.config.get('image_base_url', None),
            model=self.config.get('image_model', 'yi-vision'),
            proxy=self.config.get('image_proxy', '127.0.0.1:1090'),
            proxy_enabled=self.config.get('image_proxy_enabled', False)
        )

    def init_tray_icon(self):
        self.tray_icon = SystemTrayIcon(self)
        self.tray_icon.show_settings_signal.connect(lambda: self.settings_window.show())
        self.tray_icon.show_prompts_signal.connect(lambda: self.prompts_window.show())
        self.tray_icon.quit_signal.connect(lambda: QApplication.instance().quit())
        self.tray_icon.reset_hotkeys_signal.connect(self.reset_hotkeys)
        self.tray_icon.show_selection_keywords_signal.connect(lambda: self.selection_keywords_window.show())

    def init_selection_dialog(self):
        self.selection_dialog = SelectionSearchDialog()
        self.selection_dialog.set_ai_client(self.ai_client)
        self.selection_timer = QTimer()
        self.selection_timer.setSingleShot(True)
        self.selection_timer.timeout.connect(self._handle_selection_search_in_main_thread)
        self.selection_triggered.connect(self._handle_selection_search_in_main_thread)

    def init_hotkeys(self):
        self.hotkey = GlobalHotkey()
        self.hotkey.triggered.connect(self.show_window)
        self.hotkey.selection_triggered.connect(self._handle_selection_search_in_main_thread)
        self.hotkey.screenshot_triggered.connect(self.show_screenshot_overlay)
        self.hotkey.chat_triggered.connect(self.show_chat_window)
        self.hotkey.command_triggered.connect(self.show_command_window)
        self.hotkey.hotkey_failed.connect(self.handle_hotkey_failure)
        self.hotkey.selection_to_input_triggered.connect(self.handle_selection_to_input)

    def init_timers(self):
        self.responsiveness_timer = QTimer()
        self.responsiveness_timer.start(5000)
        self.event_timer = QTimer()
        self.event_timer.timeout.connect(self._process_events)
        self.event_timer.start(1000)
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._periodic_cleanup)
        self.cleanup_timer.start(300000)

    def init_screenshot_overlay(self):
        self.screenshot_overlay = ScreenshotOverlay()
        self.screenshot_overlay.screenshot_taken.connect(self.handle_screenshot)

    def init_image_analysis(self):
        self.image_analysis_dialog = ImageAnalysisDialog()
        self.image_analysis_dialog.analyze_requested.connect(
            lambda prompt, path: asyncio.create_task(self.handle_image_analysis(prompt, path))
        )

    def init_selection_keywords_window(self):
        self.selection_keywords_window = SelectionKeywordsWindow()
        self.selection_keywords_window.keywords_updated.connect(self.refresh_selection_menu)

    def init_command_window(self):
        self.command_window = CommandWindow()
    
    def init_prompt_input_window(self):
        """初始化提示词输入窗口"""
        self.prompt_input_window = PromptInputWindow()
        self.prompt_input_window.prompt_submitted.connect(self.handle_prompt_submission)
        self.prompt_input_window.window_closed.connect(self.on_prompt_window_closed)
    
    def show_prompt_input_window(self):
        """显示提示词输入窗口"""
        self.prompt_input_window.show_at_cursor()
    
    def handle_prompt_submission(self, prompt, temperature, max_tokens, filter_markdown):
        """处理提示词提交"""
        asyncio.create_task(self.process_prompt(prompt, temperature, max_tokens, filter_markdown))
    
    def on_prompt_window_closed(self):
        """提示词窗口关闭时的处理"""
        pass  # 可以在这里添加需要的清理逻辑

    async def process_prompt(self, prompt, temperature, max_tokens, filter_markdown):
        """处理从提示词输入窗口提交的提示词"""
        try:
            if self.stream_mode.isChecked():
                await self.get_ai_response_with_filter(prompt, temperature, max_tokens, filter_markdown)
            else:
                await self._get_non_stream_response_with_filter(prompt, temperature, max_tokens, filter_markdown)
        except Exception as e:
            print(f"处理提示词时发生错误: {e}")
            traceback.print_exc()
    
    async def get_ai_response_with_filter(self, prompt: str, temperature: float = None, max_tokens: int = None, filter_markdown: bool = False):
        """处理流式响应（带过滤选项）"""
        response_text = ""
        self.should_stop = False
        self.floating_stop_button.show_at_cursor()
        
        try:
            async for text in self.ai_client.get_response_stream(
                prompt, 
                stream=True,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                if self.should_stop:
                    print("用户停止了响应")
                    break
                    
                if filter_markdown:
                    text = remove_markdown(text)
                    
                response_text += text
                self.insert_text_to_cursor(text)
                
        except asyncio.CancelledError:
            print("AI响应被取消")
        except ConnectionError as e:
            print(f"网络连接错误: {e}")
            response_text = f"网络连接失败: {str(e)}"
        except Exception as e:
            print(f"获取AI响应时发生错误: {e}")
            traceback.print_exc()
            response_text = f"获取响应失败: {str(e)}"
        finally:
            self.floating_stop_button.hide()
            
        return response_text
    
    async def _get_non_stream_response_with_filter(self, prompt, temperature, max_tokens, filter_markdown):
        """获取非流式响应（带过滤选项）"""
        try:
            response = await self.ai_client.get_response(
                prompt, 
                temperature=temperature, 
                max_tokens=max_tokens
            )
            if filter_markdown:
                response = remove_markdown(response)
            self.insert_text_to_cursor(response, stream_mode=False)
        except Exception as e:
            print(f"获取非流式响应失败: {e}")
            error_msg = f"获取响应失败: {str(e)}"
            self.insert_text_to_cursor(error_msg, stream_mode=False)

    async def get_ai_response(self, prompt: str, temperature: float = None, max_tokens: int = None):
        """处理流式响应"""
        response_text = ""
        self.should_stop = False
        self.floating_stop_button.show_at_cursor()
        
        try:
            async for text in self.ai_client.get_response_stream(
                prompt, 
                stream=True,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                if self.should_stop:
                    print("用户停止了响应")
                    break
                    
                if self.filter_markdown.isChecked():
                    text = remove_markdown(text)
                    
                response_text += text
                self.insert_text_to_cursor(text)
                
        except asyncio.CancelledError:
            print("AI响应被取消")
        except ConnectionError as e:
            print(f"网络连接错误: {e}")
            response_text = f"网络连接失败: {str(e)}"
        except Exception as e:
            print(f"获取AI响应时发生错误: {e}")
            traceback.print_exc()
            response_text = f"获取响应失败: {str(e)}"
        finally:
            self.floating_stop_button.hide()
            
        return response_text

    def insert_text_to_cursor(self, text, stream_mode=True):
        """插入文本到光标位置，支持流式和非流式模式，结合多种方法"""
        try:
            hwnd = GetForegroundWindow()
            _, pid = GetWindowThreadProcessId(hwnd)
            process_name = psutil.Process(pid).name().lower()
            
            # 获取当前线程ID和目标窗口线程ID
            current_thread = win32api.GetCurrentThreadId()
            target_thread = GetWindowThreadProcessId(hwnd)[0]
            
            # 附加输入线程，这样可以保持输入焦点
            AttachThreadInput(current_thread, target_thread, True)
            try:
                SetForegroundWindow(hwnd)
            finally:
                AttachThreadInput(current_thread, target_thread, False)
            
            success = False

            # 特殊处理 Microsoft Word
            if 'winword' in process_name:
                try:
                    word = win32com_client.Dispatch("Word.Application")
                    if word.Documents.Count > 0:
                        word.Selection.TypeText(text)
                        success = True
                except Exception as e:
                    print(f"使用 Word 自动化接口失败: {e}")

            # 使用 PostMessage 发送 WM_CHAR
            if not success:
                try:
                    if not stream_mode:
                        # 非流式模式使用剪贴板
                        old_clipboard = pyperclip.paste()
                        pyperclip.copy(text)
                        keyboard.press_and_release('ctrl+v')
                        time.sleep(0.01)
                        pyperclip.copy(old_clipboard)
                    else:
                        # 流式模式使用PostMessage
                        for char in text:
                            PostMessage(hwnd, WM_CHAR, ord(char), 0)
                    success = True
                except Exception as e:
                    print(f"PostMessage 方法失败: {e}")

            # 使用 keyboard 模块作为备选方案
            if not success:
                try:
                    if stream_mode:
                        keyboard.write(text, delay=0.001)
                    else:
                        keyboard.write(text)
                    success = True
                except Exception as e:
                    print(f"keyboard 模块输入失败: {e}")

            if not success:
                print("所有插入方法均失败")
                
        except Exception as e:
            print(f"插入文本到光标失败: {e}")
            traceback.print_exc()



    def load_config(self):
        """加载配置文件，如果不存在则创建默认配置"""
        default_config = {
            'api_key': '',
            'base_url': 'https://api.openai.com/v1',
            'model': 'gpt-4o-mini',
            'api_type': 'OpenAI',
            'proxy_enabled': False,
            'proxy': '127.0.0.1:1090'
        }
        
        try:
            with open('config/config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                if 'proxy_enabled' in self.config:
                    self.config['proxy_enabled'] = bool(self.config['proxy_enabled'])
        except FileNotFoundError:
            print("配置文件不存在，创建默认配置")
            self.config = default_config
            self._save_config()
        except json.JSONDecodeError as e:
            print(f"配置文件格式错误: {e}，使用默认配置")
            self.config = default_config
            self._save_config()
        except (OSError, IOError) as e:
            print(f"读取配置文件失败: {e}，使用默认配置")
            self.config = default_config
    
    def _save_config(self):
        """保存配置文件"""
        try:
            with open('config/config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except (OSError, IOError) as e:
            print(f"保存配置文件失败: {e}")

    def show_window(self):
        """显示或隐藏窗口的方法"""
        try:
            if self.isVisible():
                self.hide()
            else:
                cursor = QCursor.pos()
                window_x = cursor.x() + 10
                window_y = cursor.y() + 10
                screen = QApplication.primaryScreen().geometry()
                if window_x + self.width() > screen.width():
                    window_x = screen.width() - self.width()
                if window_y + self.height() > screen.height():
                    window_y = screen.height() - self.height()
                self.move(window_x, window_y)
                super().show()
                self.raise_()
                self.activateWindow()
                # 输入框已移到独立的提示词输入窗口
        except KeyboardInterrupt:
            print("收到键盘中断信号")
        except Exception as e:
            print(f"事件循环发生错误: {e}")
            traceback.print_exc()

    def hide(self):
        """重写hide方法以更新状态"""
        super().hide()
        self.is_window_visible = False

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

    def eventFilter(self, obj, event):
        try:
            if obj is self.input_text and event.type() == QEvent.Type.KeyPress:
                if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.NoModifier:
                    asyncio.get_event_loop().create_task(self.process_input())
                    return True
                elif event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                    cursor = self.input_text.textCursor()
                    cursor.insertText('\n')
                    return True
            return super().eventFilter(obj, event)
        except KeyboardInterrupt:
            print("收到键盘中断信号")
        except Exception as e:
            print(f"事件循环发生错误: {e}")
            traceback.print_exc()
            return False

    def stop_response(self):
        self.should_stop = True
        self.floating_stop_button.hide()

    def on_settings_saved(self, settings_data):
        """当设置被保存时更新配置和AI客户端"""
        try:
            config = settings_data["config"]
            self.config = config
            self.init_ai_clients()
            self.reset_hotkeys()
        except KeyboardInterrupt:
            print("收到键盘中断信号")
        except Exception as e:
            print(f"事件循环发生错误: {e}")
            traceback.print_exc()



    def handle_hotkey_failure(self, error_msg):
        """处理热键失败的情况"""
        try:
            keyboard.unhook_all()
            time.sleep(0.1)
            if hasattr(self, 'hotkey'):
                self.hotkey._cleanup_keyboard_state()
        except KeyboardInterrupt:
            print("收到键盘中断信号")
        except Exception as e:
            print(f"事件循环发生错误: {e}")
            traceback.print_exc()

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
            for timer in [self.responsiveness_timer, self.event_timer]:
                if timer and timer.isActive():
                    timer.stop()
            if hasattr(self, 'hotkey'):
                self.hotkey.stop()
                delattr(self, 'hotkey')
            QApplication.processEvents()
            if hasattr(self, 'cleanup_timer') and self.cleanup_timer.isActive():
                self.cleanup_timer.stop()
        except KeyboardInterrupt:
            print("收到键盘中断信号")
        except Exception as e:
            print(f"事件循环发生错误: {e}")
            traceback.print_exc()

    def _process_events(self):
        """定期处理累积的事件"""
        try:
            QApplication.processEvents()
        except KeyboardInterrupt:
            print("收到键盘中断信号")
        except Exception as e:
            print(f"事件循环发生错误: {e}")
            traceback.print_exc()

    def _handle_selection_search_in_main_thread(self):
        """在主线程中创建异步任务"""
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self.handle_selection_search())
        except KeyboardInterrupt:
            print("收到键盘中断信号")
        except Exception as e:
            print(f"事件循环发生错误: {e}")
            traceback.print_exc()

    async def handle_selection_search(self):
        """理划词搜索"""
        try:
            # 先等待一下让热键释放
            await asyncio.sleep(0.1)
            
            selected_text = self.get_selected_text()
            if not selected_text:
                print("未获取到选中文本，重试一次")
                # 如果第一次获取失败，稍等后重试一次
                await asyncio.sleep(0.2)
                selected_text = self.get_selected_text()
                if not selected_text:
                    return
                
            old_clipboard = pyperclip.paste()
            pyperclip.copy(selected_text)
            try:
                self.selection_dialog.show_menu(selected_text)
            finally:
                pyperclip.copy(old_clipboard)
        except KeyboardInterrupt:
            print("收到键盘中断信号")
        except Exception as e:
            print(f"事件循环发生错误: {e}")
            traceback.print_exc()

    def handle_screenshot(self, image_path):
        """处理截图"""
        try:
            if not self.image_analysis_dialog.isVisible():
                self.image_analysis_dialog.set_image(image_path)
                self.image_analysis_dialog.clear_response()
                self.image_analysis_dialog.show()
        except KeyboardInterrupt:
            print("收到键盘中断信号")
        except Exception as e:
            print(f"事件循环发生错误: {e}")
            traceback.print_exc()

    async def handle_image_analysis(self, prompt: str, image_path: str):
        """处理图片分析请求"""
        try:
            if not self.image_analysis_dialog.isVisible():
                return
            with open(image_path, 'rb') as f:
                image_data = f.read()
            self.image_analysis_dialog.clear_response()
            if self.image_analysis_dialog.stream_mode.isChecked():
                async for text in self.ai_image_client.get_response_stream(prompt, image_data):
                    if not self.image_analysis_dialog.isVisible():
                        break
                    if self.image_analysis_dialog.filter_markdown.isChecked():
                        text = remove_markdown(text)
                    self.image_analysis_dialog.append_response(text)
            else:
                response = await self.ai_image_client.get_response(prompt, image_data)
                if not self.image_analysis_dialog.isVisible():
                    return
                if self.image_analysis_dialog.filter_markdown.isChecked():
                    response = remove_markdown(response)
                self.image_analysis_dialog.append_response(response)
        except Exception as e:
            if self.image_analysis_dialog.isVisible():
                error_msg = f"分析图片失败: {str(e)}"
                self.image_analysis_dialog.append_response(f"错误: {error_msg}")
                traceback.print_exc()

    def show_screenshot_overlay(self):
        """显示截图覆盖层"""
        if self.image_analysis_dialog.isVisible():
            self.image_analysis_dialog.hide()
            return
        self.screenshot_overlay.show()

    def handle_selection_to_input(self):
        """处理将选中文本添加到输入框的功能"""
        try:
            # 移除延迟，改为更短的延迟
            time.sleep(0.05)
            
            # 保存当前焦点窗口
            current_hwnd = GetForegroundWindow()
            
            # 获取选中文本
            selected_text = self.get_selected_text()
            
            # 显示提示词输入窗口并传入选中的文本
            if selected_text and selected_text.strip():
                self.prompt_input_window.set_input_text(selected_text)
            
            # 显示提示词输入窗口
            self.prompt_input_window.show()
            self.prompt_input_window.raise_()
            self.prompt_input_window.activateWindow()
            
            # 如果之前的窗口还存在，尝试恢复其焦点状态
            if current_hwnd and win32gui.IsWindow(current_hwnd):
                try:
                    SetForegroundWindow(current_hwnd)
                    time.sleep(0.05)
                    self.prompt_input_window.raise_()
                    self.prompt_input_window.activateWindow()
                except:
                    pass
                    
        except KeyboardInterrupt:
            print("收到键盘中断信号")
        except Exception as e:
            print(f"事件循环发生错误: {e}")
            traceback.print_exc()

    def get_selected_text(self):
        """获取选中��文本"""
        try:
            hwnd = GetForegroundWindow()
            if not hwnd:
                print("无法获取活动窗口")
                return None

            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process_name = psutil.Process(pid).name().lower()
            print(f"当前活动窗口进程：{process_name}")

            # 保存原始剪贴板内容
            old_clipboard = pyperclip.paste()
            
            # 清空剪贴板
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.CloseClipboard()

            # 针对Chrome等浏览器的特殊处理
            chromium_browsers = [
                'chrome.exe', 'msedge.exe', 'firefox.exe', 'opera.exe', 
                'brave.exe', 'vivaldi.exe', 'edge.exe'
            ]
            
            if process_name in chromium_browsers:
                # 确保窗口处于前台
                SetForegroundWindow(hwnd)
                time.sleep(0.01)  # 给窗口切换更多时间
                
                # 尝试使用不同的复制方法
                try:
                    # 方法1：使用ctrl+c
                    keyboard.press_and_release('ctrl+c')
                    time.sleep(0.3)  # 给复制操作更多时间
                    
                    selected_text = pyperclip.paste()
                    if not selected_text:
                        # 方法2：使用ctrl+insert
                        keyboard.press_and_release('ctrl+insert')
                        time.sleep(0.3)
                        selected_text = pyperclip.paste()
                        
                    if not selected_text:
                        # 方法3：发送复制消息
                        PostMessage(hwnd, WM_COPY, 0, 0)
                        time.sleep(0.3)
                        selected_text = pyperclip.paste()
                except Exception as e:
                    print(f"复制操作失败: {str(e)}")
                    selected_text = None
            else:
                # 其他程序的常规处理
                SetForegroundWindow(hwnd)
                time.sleep(0.1)
                keyboard.press_and_release('ctrl+c')
                time.sleep(0.2)
                selected_text = pyperclip.paste()

            # 恢复原始剪贴板内容
            try:
                if old_clipboard:
                    pyperclip.copy(old_clipboard)
            except:
                pass

            if selected_text:
                selected_text = selected_text.strip()
                if selected_text:
                    print(f"成功获取选中文本: {selected_text[:50]}...")
                    return selected_text

            print("未能获取选中文本")
            return None
        
        except Exception as e:
            print(f"获取选中文本失败: {str(e)}")
            traceback.print_exc()
            return None


    def _periodic_cleanup(self):
        """定期清理系统资源"""
        pass

    def show_chat_window(self):
        """显示连续对话窗口"""
        try:
            from chat_window import ChatWindow
            if not hasattr(self, 'chat_window'):
                self.chat_window = ChatWindow(self.ai_client)
            if self.chat_window.isVisible():
                self.chat_window.hide()
            else:
                cursor = QCursor.pos()
                window_x = cursor.x() + 10
                window_y = cursor.y() + 10
                screen = QApplication.primaryScreen().geometry()
                if window_x + self.chat_window.width() > screen.width():
                    window_x = screen.width() - self.chat_window.width()
                if window_y + self.chat_window.height() > screen.height():
                    window_y = screen.height() - self.chat_window.height()
                self.chat_window.move(window_x, window_y)
                self.chat_window.show()
                self.chat_window.raise_()
                self.chat_window.activateWindow()
        except KeyboardInterrupt:
            print("收到键盘中断信号")
        except Exception as e:
            print(f"事件循环发生错误: {e}")
            traceback.print_exc()

    def refresh_selection_menu(self):
        """刷新划词菜单"""
        try:
            if hasattr(self, 'selection_dialog'):
                if not hasattr(self.selection_dialog, 'selection_menu'):
                    self.selection_dialog.show_menu("")
                self.selection_dialog.selection_menu.refresh_menu()
        except KeyboardInterrupt:
            print("收到键盘中断信号")
        except Exception as e:
            print(f"事件循环发生错误: {e}")
            traceback.print_exc()

    def reset_hotkeys(self):
        """重置热键的方法"""
        try:
            if hasattr(self, 'hotkey'):
                self.hotkey.stop()
                keyboard.unhook_all()
                time.sleep(0.1)
                delattr(self, 'hotkey')
                time.sleep(0.1)
                self.init_hotkeys()
                self.tray_icon.showMessage(
                    "热键重置",
                    "热键已成功重置",
                    QSystemTrayIcon.Information,
                    2000
                )
                QApplication.processEvents()
            else:
                self.init_hotkeys()
                self.tray_icon.showMessage(
                    "热键初始化",
                    "热键已初始化",
                    QSystemTrayIcon.Information,
                    2000
                )
        except Exception as e:
            error_msg = f"重置热键失败: {str(e)}"
            self.tray_icon.showMessage(
                "热键重置失败",
                error_msg,
                QSystemTrayIcon.Warning,
                2000
            )
            try:
                keyboard.unhook_all()
                time.sleep(0.2)
                self.init_hotkeys()
            except Exception:
                traceback.print_exc()

    def show_command_window(self):
        """显示命令窗口"""
        try:
            if not hasattr(self, 'command_window'):
                self.command_window = CommandWindow()
            if not self.command_window.isVisible():
                screen = QApplication.primaryScreen().geometry()
                window_x = (screen.width() - self.command_window.width()) // 2
                window_y = (screen.height() - self.command_window.height()) // 2
                self.command_window.move(window_x, window_y)
                self.command_window.show()
                self.command_window.raise_()
                self.command_window.activateWindow()
            else:
                self.command_window.hide()
        except KeyboardInterrupt:
            print("收到键盘中断信号")
        except Exception as e:
            print(f"事件循环发生错误: {e}")
            traceback.print_exc()

def check_single_instance():
    """检查否已有实例在运行"""
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

async def main():
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        window = InputWindow()
        
        # 创建事件循环
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        # 创建清理任务
        cleanup_task = None
        
        async def cleanup_routine():
            while True:
                try:
                    await asyncio.sleep(60)
                    QApplication.processEvents()
                except asyncio.CancelledError:
                    break
                except Exception:
                    traceback.print_exc()
        
        try:
            # 启动清理任务
            cleanup_task = loop.create_task(cleanup_routine())
            
            # 注册程序退出时的清理函���
            def cleanup():
                if cleanup_task and not cleanup_task.done():
                    cleanup_task.cancel()
                if loop.is_running():
                    loop.stop()
            
            app.aboutToQuit.connect(cleanup)
            
            # 运行事件循环
            with loop:
                return loop.run_forever()
                
        except KeyboardInterrupt:
            print("收到键盘中断信号")
        except Exception as e:
            print(f"事件循环发生错误: {e}")
            traceback.print_exc()
        finally:
            # 清理资源
            print("开始清理程序资源...")
            
            # 取消清理任务
            if cleanup_task and not cleanup_task.done():
                cleanup_task.cancel()
                print("清理任务已取消")
            
            # 停止并关闭事件循环
            try:
                if loop.is_running():
                    loop.stop()
                    print("事件循环已停止")
                loop.close()
                print("事件循环已关闭")
            except Exception as e:
                print(f"关闭事件循环时发生错误: {e}")
            
            print("程序资源清理完成")
            
    except Exception as e:
        print(f"主函数发生严重错误: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"
    try:
        if not check_single_instance():
            print("程序已在运行！")
            sys.exit(0)
            
        # 使用 asyncio.run 替代直接调用
        sys.exit(asyncio.run(main()))
        
    except Exception as e:
        print(f"程序启动失败: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
