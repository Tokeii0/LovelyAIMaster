from PySide6.QtCore import QObject, Signal, Qt
import keyboard
import json
import time
import traceback

class GlobalHotkey(QObject):
    triggered = Signal()
    selection_triggered = Signal()
    screenshot_triggered = Signal()
    chat_triggered = Signal()
    hotkey_failed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 默认快捷键
        self.hotkey1 = 'Alt+Q'
        self.hotkey2 = 'Alt+W'
        self.selection_hotkey = 'Alt+2'
        self.screenshot_hotkey = 'Alt+3'
        self.chat_hotkey = 'Ctrl+4'
        
        self.registered_hotkeys = []  # 存储所有注册的热键
        
        # 加载配置文件中的快捷键设置
        self.load_hotkey_config()
        
        # 注册热键
        self._register_hotkeys()

    def _register_hotkeys(self):
        """注册热键"""
        try:
            # 清理现有热键
            self._unregister_hotkeys()
            
            # 先注册一个空的 alt 处理器，避免 alt 键被系统拦截
            keyboard.on_press_key('alt', lambda _: None, suppress=False)
            time.sleep(0.05)
            
            # 配置热键和对应的信号
            shortcuts_config = [
                (self.hotkey1, self.triggered),
                (self.hotkey2, self.triggered),
                (self.selection_hotkey, self.selection_triggered),
                (self.screenshot_hotkey, self.screenshot_triggered),
                (self.chat_hotkey, self.chat_triggered)
            ]
            
            # 打印调试信息
            print("正在注册的热键:")
            for key, signal in shortcuts_config:
                print(f"热键: {key}, 信号: {signal}")
            
            # 注册新的热键
            for key, signal in shortcuts_config:
                kb_hotkey = key.lower().replace('ctrl', 'control')
                try:
                    keyboard.add_hotkey(
                        kb_hotkey,
                        lambda s=signal: self._trigger_with_check(s),
                        suppress=True,
                        trigger_on_release=False
                    )
                    self.registered_hotkeys.append(kb_hotkey)
                    print(f"成功注册热键: {kb_hotkey}")
                    time.sleep(0.05)
                except Exception as e:
                    print(f"注册热键 {kb_hotkey} 失败: {str(e)}")
                    continue
                
        except Exception as e:
            print(f"注册热键失败: {str(e)}")
            traceback.print_exc()
            self.hotkey_failed.emit(f"注册热键失败: {str(e)}")

    def _trigger_with_check(self, signal):
        """带防重复触发检查的信号触发函数"""
        current_time = time.time()
        if not hasattr(self, '_last_trigger_time'):
            self._last_trigger_time = 0
        
        # 检查是否在短时间内重复触发（300毫秒内）
        if current_time - self._last_trigger_time > 0.3:
            self._last_trigger_time = current_time
            signal.emit()

    def _unregister_hotkeys(self):
        """取消注册的热键"""
        try:
            keyboard.unhook_all()
            self.registered_hotkeys.clear()
            time.sleep(0.1)  # 给系统一些时间来处理
        except Exception as e:
            print(f"取消注册热键失败: {str(e)}")

    def stop(self):
        """停止热键监听"""
        self._unregister_hotkeys()

    def load_hotkey_config(self):
        """从配置文件加载快捷键设置"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.hotkey1 = self._format_shortcut(config.get('hotkey1', 'Alt+Q'))
                self.hotkey2 = self._format_shortcut(config.get('hotkey2', 'Alt+W'))
                self.selection_hotkey = self._format_shortcut(config.get('selection_hotkey', 'Alt+2'))
                self.screenshot_hotkey = self._format_shortcut(config.get('screenshot_hotkey', 'Alt+3'))
                self.chat_hotkey = self._format_shortcut(config.get('chat_hotkey', 'Ctrl+4'))
        except Exception as e:
            print(f"加载配置文件失败，使用默认快捷键。错误信息：{e}")

    def _format_shortcut(self, shortcut):
        """格式化快捷键字符串为标准格式"""
        if not shortcut:
            return ''
        parts = shortcut.split('+')
        return '+'.join(p.capitalize() for p in parts)

    def test_trigger(self, key):
        print(f"快捷键 {key} 被触发")

    def _cleanup_keyboard_state(self):
        """清理键盘状态"""
        try:
            keyboard.unhook_all()
        except Exception as e:
            traceback.print_exc()
