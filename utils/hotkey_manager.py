from PySide6.QtCore import QObject, Signal, Qt
import win32con
import win32gui
import json
import time
import traceback
import sys
import ctypes
from win32gui import PumpMessages, PostQuitMessage
import win32gui_struct
try:
    import win32api
except ImportError:
    import win32api.win32api as win32api

# 定义热键ID
HOTKEY_SHOW = 1
HOTKEY_SHOW2 = 2
HOTKEY_SELECTION = 3
HOTKEY_SCREENSHOT = 4
HOTKEY_CHAT = 5
HOTKEY_COMMAND = 6

class GlobalHotkey(QObject):
    triggered = Signal()
    selection_triggered = Signal()
    screenshot_triggered = Signal()
    chat_triggered = Signal()
    command_triggered = Signal()
    hotkey_failed = Signal(str)
    selection_to_input_triggered = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 默认快捷键
        self.hotkey1 = ('Alt', '1')  # 改为元组格式
        self.hotkey2 = ('Alt', '2')
        self.selection_hotkey = ('Alt', '3')
        self.screenshot_hotkey = ('Alt', '4')
        self.chat_hotkey = ('Control', '4')
        self.command_hotkey = ('Alt', '5')
        
        self.registered_hotkeys = {}  # 存储已注册的热键ID
        
        # 加载配置
        self.load_hotkey_config()
        
        # 创建隐藏窗口接收热键消息
        self._create_hotkey_window()
        
        # 注册热键
        self._register_hotkeys()

    def _create_hotkey_window(self):
        """创建隐藏窗口用于接收热键消息"""
        try:
            # 初始化hwnd属性为None，确保即使创建失败也有这个属性
            self.hwnd = None
            
            # 设置窗口类
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self._window_proc
            wc.lpszClassName = "GlobalHotkeyWindow"
            
            # 尝试注册窗口类，如果已存在则忽略错误
            try:
                win32gui.RegisterClass(wc)
            except win32gui.error as e:
                # 类已存在错误 (1410)，可以忽略
                if e.winerror != 1410:  # 如果不是"类已存在"错误，则重新抛出
                    raise
                print("窗口类已存在，继续使用...")
            
            # 创建窗口
            self.hwnd = win32gui.CreateWindow(
                wc.lpszClassName,
                "GlobalHotkeyWindow",
                0, 0, 0, 0, 0,
                0, 0, 0, None
            )
            
            if not self.hwnd:
                raise Exception("创建窗口失败，返回的hwnd为空")
                
        except Exception as e:
            print(f"创建热键窗口失败: {str(e)}")
            traceback.print_exc()
            # 确保hwnd至少有一个有效值，防止后续注册热键时出错
            if not self.hwnd:
                self.hwnd = 0

    def _window_proc(self, hwnd, msg, wparam, lparam):
        """窗口消息处理"""
        if msg == win32con.WM_HOTKEY:
            try:
                # 根据热键ID触发对应信号
                if wparam == HOTKEY_SHOW:
                    # 当按下 Alt+1 时，触发selection_to_input_triggered信号
                    self.selection_to_input_triggered.emit()
                elif wparam == HOTKEY_SHOW2:
                    self.triggered.emit()
                elif wparam == HOTKEY_SELECTION:
                    self.selection_triggered.emit()
                elif wparam == HOTKEY_SCREENSHOT:
                    self.screenshot_triggered.emit()
                elif wparam == HOTKEY_CHAT:
                    self.chat_triggered.emit()
                elif wparam == HOTKEY_COMMAND:
                    self.command_triggered.emit()
            except Exception as e:
                print(f"处理热键消息失败: {str(e)}")
                traceback.print_exc()
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _register_hotkeys(self):
        """注册热键"""
        try:
            # 检查窗口句柄是否有效
            if not hasattr(self, 'hwnd') or self.hwnd is None:
                print("窗口句柄无效，尝试重新创建窗口...")
                self._create_hotkey_window()
                
                # 再次检查窗口是否创建成功
                if not hasattr(self, 'hwnd') or self.hwnd is None:
                    raise Exception("无法创建有效的窗口句柄，无法注册热键")
            
            # 先取消注册所有热键
            self._unregister_hotkeys()
            
            # 定义要注册的热键
            hotkeys = [
                (HOTKEY_SHOW, self.hotkey1),
                (HOTKEY_SHOW2, self.hotkey2),
                (HOTKEY_SELECTION, self.selection_hotkey),
                (HOTKEY_SCREENSHOT, self.screenshot_hotkey),
                (HOTKEY_CHAT, self.chat_hotkey),
                (HOTKEY_COMMAND, self.command_hotkey)
            ]
            
            print("开始注册热键...")  # 调试输出
            # 注册每个热键
            for hotkey_id, (modifier, key) in hotkeys:
                try:
                    # 转换修饰键
                    mod_flag = self._get_modifier_flag(modifier)
                    # 转换键码
                    vk_code = self._get_virtual_key_code(key)
                    
                    print(f"注册热键: ID={hotkey_id}, 修饰键={modifier}({mod_flag}), 键={key}({vk_code})")  # 调试输出
                    
                    # 使用 user32.dll 直接注册热键
                    if ctypes.windll.user32.RegisterHotKey(self.hwnd, hotkey_id, mod_flag, vk_code):
                        self.registered_hotkeys[hotkey_id] = (mod_flag, vk_code)
                        print(f"成功注册热键: {modifier}+{key}")
                    else:
                        error = ctypes.get_last_error()
                        print(f"注册热键失败: {modifier}+{key}, 错误码: {error}")
                        self.hotkey_failed.emit(f"注册热键失败: {modifier}+{key}, 错误码: {error}")
                        
                except Exception as e:
                    print(f"注册热键 {modifier}+{key} 失败: {str(e)}")
                    traceback.print_exc()
                    self.hotkey_failed.emit(f"注册热键 {modifier}+{key} 失败: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"注册热键失败: {str(e)}")
            traceback.print_exc()
            self.hotkey_failed.emit(f"注册热键失败: {str(e)}")

    def _get_modifier_flag(self, modifier):
        """转换修饰键为win32 flag"""
        modifier = modifier.lower()
        if modifier == 'alt':
            return win32con.MOD_ALT
        elif modifier == 'control':
            return win32con.MOD_CONTROL
        elif modifier == 'shift':
            return win32con.MOD_SHIFT
        elif modifier == 'win':
            return win32con.MOD_WIN
        return 0

    def _get_virtual_key_code(self, key):
        """转换键名为虚拟键码"""
        try:
            # 如果是数字键
            if key.isdigit():
                return ord(key)  # 直接返回数字的ASCII码
            # 如果是字母键
            elif len(key) == 1 and key.isalpha():
                return ord(key.upper())
            # 如果是反引号
            elif key == '`':
                return 0xC0  # 反引号的虚拟键码
            # 如果是其他特殊键，可以继续添加
            
            # 调试输出
            print(f"键码转换: {key} -> {ord(key) if len(key) == 1 else 'unknown'}")
            
            return ord(key) if len(key) == 1 else 0
        except Exception as e:
            print(f"键码转换失败: {str(e)}")
            return 0

    def _unregister_hotkeys(self):
        """取消注册的热键"""
        try:
            # 检查窗口句柄是否有效
            if not hasattr(self, 'hwnd') or self.hwnd is None:
                print("窗口句柄无效，无法取消注册热键")
                self.registered_hotkeys.clear()
                return
                
            for hotkey_id in list(self.registered_hotkeys.keys()):
                try:
                    ctypes.windll.user32.UnregisterHotKey(self.hwnd, hotkey_id)
                except Exception as e:
                    print(f"取消注册热键ID={hotkey_id}失败: {str(e)}")
            self.registered_hotkeys.clear()
        except Exception as e:
            print(f"取消注册热键失败: {str(e)}")
            traceback.print_exc()

    def stop(self):
        """停止热键监听"""
        try:
            self._unregister_hotkeys()
            if hasattr(self, 'hwnd') and self.hwnd:
                try:
                    win32gui.DestroyWindow(self.hwnd)
                except Exception as e:
                    print(f"销毁窗口失败: {str(e)}")
                self.hwnd = None
        except Exception as e:
            print(f"停止热键监听失败: {str(e)}")
            traceback.print_exc()

    def restart(self):
        """重启热键监听"""
        try:
            print("正在重启热键监听...")
            self.stop()
            time.sleep(0.2)  # 短暂延迟确保资源释放
            self._create_hotkey_window()
            if hasattr(self, 'hwnd') and self.hwnd:
                print(f"成功创建窗口，句柄: {self.hwnd}")
                self._register_hotkeys()
            else:
                print("窗口创建失败，无法注册热键")
                self.hotkey_failed.emit("窗口创建失败，无法注册热键")
        except Exception as e:
            print(f"重启热键监听失败: {str(e)}")
            traceback.print_exc()
            self.hotkey_failed.emit(f"重启热键监听失败: {str(e)}")

    def load_hotkey_config(self):
        """从配置文件加载快捷键设置"""
        try:
            with open('config/config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 转换配置中的快捷键为元组格式
                self.hotkey1 = self._parse_shortcut(config.get('hotkey1', 'Alt+1'))
                self.hotkey2 = self._parse_shortcut(config.get('hotkey2', 'Alt+2'))
                self.selection_hotkey = self._parse_shortcut(config.get('selection_hotkey', 'Alt+3'))
                self.screenshot_hotkey = self._parse_shortcut(config.get('screenshot_hotkey', 'Alt+4'))
                self.chat_hotkey = self._parse_shortcut(config.get('chat_hotkey', 'Control+4'))
                self.command_hotkey = self._parse_shortcut(config.get('command_hotkey', 'Alt+5'))
        except Exception as e:
            print(f"加载热键配置失败: {str(e)}")
            traceback.print_exc()

    def _parse_shortcut(self, shortcut):
        """解析快捷键字符串为元组格式"""
        if not shortcut:
            return ('Alt', '1')
        parts = shortcut.split('+')
        if len(parts) != 2:
            return ('Alt', '1')
        return (parts[0].capitalize(), parts[1])

    def _handle_selection_to_input(self):
        """处理Alt+1热键"""
        try:
            self.selection_to_input_triggered.emit()
        except Exception as e:
            print(f"处理Alt+1热键失败: {str(e)}")
            self.hotkey_failed.emit(str(e))
