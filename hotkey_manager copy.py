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
        
        # 添加定时清理计时器
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._cleanup_keyboard_state)
        self.cleanup_timer.start(30000)  # 每30秒清理一次

    def _register_hotkeys(self):
        """注册热键"""
        try:
            # 确保清理现有热键
            try:
                keyboard.unhook_all()
                time.sleep(0.1)
            except Exception:
                pass
            
            # 先注册一个空的 alt 处理器，避免 alt 键被完全屏蔽
            try:
                keyboard.on_press_key('alt', lambda _: None, suppress=False)
                time.sleep(0.05)
            except Exception:
                pass
            
            # 修改注册方式，使用更可靠的方式
            for hotkey in [self.hotkey1, self.hotkey2, self.selection_hotkey, 
                          self.screenshot_hotkey, self.chat_hotkey]:
                try:
                    # 对于包含 alt 的热键使用特殊处理
                    if 'alt' in hotkey.lower():
                        keyboard.add_hotkey(hotkey, 
                                            self._get_trigger_function(hotkey),
                                            suppress=False,  # 改为 False
                                            trigger_on_release=True,
                                            timeout=0.2)  # 增加超时时间
                    else:
                        keyboard.add_hotkey(hotkey,
                                            self._get_trigger_function(hotkey),
                                            suppress=False,  # 改为 False
                                            trigger_on_release=True)
                    time.sleep(0.1)  # 增加等待时间
                except Exception as e:
                    print(f"注册热键 {hotkey} 失败: {str(e)}")
                    continue
                
        except Exception as e:
            traceback.print_exc()
            self.hotkey_failed.emit(f"注册热键失败: {str(e)}")

    def _get_trigger_function(self, hotkey):
        """根据热键返回对应的触发函数"""
        if hotkey in [self.hotkey1, self.hotkey2]:
            return self._on_hotkey_triggered
        elif hotkey == self.selection_hotkey:
            return self._on_selection_triggered
        elif hotkey == self.screenshot_hotkey:
            return self._on_screenshot_triggered
        elif hotkey == self.chat_hotkey:
            return self._emit_chat_signal
        return lambda: None

    def _unregister_hotkeys(self):
        """取消注册的热键"""
        try:
            # 先尝试完全清理所有热键
            keyboard.unhook_all()
            time.sleep(0.1)
        except Exception as e:
            print(f"清理所有热键失败: {str(e)}")
            traceback.print_exc()
        
        # 再逐个尝试清理特定热键
        for hotkey in [self.hotkey1, self.hotkey2, self.selection_hotkey, 
                      self.screenshot_hotkey, self.chat_hotkey]:
            try:
                keyboard.remove_hotkey(hotkey)
            except (KeyError, ValueError, Exception) as e:
                # 忽略特定热键清理失败的错误
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

    # 添加定期清理机制
    def _cleanup_keyboard_state(self):
        """定期清理键盘状态"""
        try:
            # 先解除所有热键
            keyboard.unhook_all()
            time.sleep(0.2)  # 增加等待时间
            
            # 重置键盘状态
            for key in ['alt', 'ctrl', 'shift']:
                try:
                    keyboard.release(key)
                except:
                    pass
                time.sleep(0.05)
            
            # 重新注册热键
            self._register_hotkeys()
        except Exception as e:
            traceback.print_exc()
