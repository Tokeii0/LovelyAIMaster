import time
import threading
import traceback
from PySide6.QtCore import QObject, QTimer, Signal
import keyboard
import json

class GlobalHotkey(QObject):
    triggered = Signal()
    selection_triggered = Signal()
    screenshot_triggered = Signal()
    chat_triggered = Signal()
    hotkey_failed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()
        self.last_trigger_time = time.time()
        
        # 默认快捷键
        self.hotkey1 = 'alt+q'
        self.hotkey2 = 'alt+w'
        self.selection_hotkey = 'alt+2'
        self.screenshot_hotkey = 'alt+3'
        self.chat_hotkey = 'ctrl+4'
        
        # 加载配置文件中的快捷键设置
        self.load_hotkey_config()
        
        # 注册热键
        self._register_hotkeys()
        
        # # 定时检查热键状态
        # self.check_timer = QTimer()
        # self.check_timer.timeout.connect(self._check_hotkey_status)
        # self.check_timer.start(60000)  # 每60秒检查一次

    def _register_hotkeys(self):
        """注册热键"""
        try:
            # 取消之前注册的热键（如果有）
            self._unregister_hotkeys()
            
            # 注册新的热键
            keyboard.add_hotkey(self.hotkey1, self._on_hotkey_triggered, suppress=True, trigger_on_release=True)
            keyboard.add_hotkey(self.hotkey2, self._on_hotkey_triggered, suppress=True, trigger_on_release=True)
            keyboard.add_hotkey(self.selection_hotkey, self._on_selection_triggered, suppress=True, trigger_on_release=True)
            keyboard.add_hotkey(self.screenshot_hotkey, self._on_screenshot_triggered, suppress=True, trigger_on_release=True)
            keyboard.add_hotkey(self.chat_hotkey, self._emit_chat_signal, suppress=True, trigger_on_release=True)
        except Exception as e:
            traceback.print_exc()
            self.hotkey_failed.emit(f"注册热键失败: {str(e)}")

    def _unregister_hotkeys(self):
        """取消注册的热键"""
        for hotkey in [self.hotkey1, self.hotkey2, self.selection_hotkey, 
                      self.screenshot_hotkey, self.chat_hotkey]:
            try:
                keyboard.remove_hotkey(hotkey)
            except KeyError:
                pass

    def _on_hotkey_triggered(self):
        """处理热键触发事件"""
        self.last_trigger_time = time.time()
        self.triggered.emit()

    def _on_selection_triggered(self):
        """处理划词搜索热键触发事件"""
        self.last_trigger_time = time.time()
        self.selection_triggered.emit()

    def _on_screenshot_triggered(self):
        """处理截图热键触发事件"""
        self.last_trigger_time = time.time()
        self.screenshot_triggered.emit()

    def _check_hotkey_status(self):
        """定期检查热键是否仍然有效"""
        # 如果超过5分钟未触发热键，尝试重新注册
        if time.time() - self.last_trigger_time > 300:
            self._register_hotkeys()

    def stop(self):
        """停止热键监听"""
        self._unregister_hotkeys()
        self.check_timer.stop()

    def load_hotkey_config(self):
        """从配置文件加载快捷键设置"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.hotkey1 = config.get('hotkey1', 'alt+q').lower()
                self.hotkey2 = config.get('hotkey2', 'alt+w').lower()
                self.selection_hotkey = config.get('selection_hotkey', 'alt+2').lower()
                self.screenshot_hotkey = config.get('screenshot_hotkey', 'alt+3').lower()
                self.chat_hotkey = config.get('chat_hotkey', 'ctrl+4').lower()
        except Exception as e:
            print(f"加载配置文件失败，使用默认快捷键。错误信息：{e}")

    def _emit_chat_signal(self):
        """发出连续对话信号"""
        self.chat_triggered.emit()
