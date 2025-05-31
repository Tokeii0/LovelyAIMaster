import win32gui
import win32api
import win32con
from ctypes import windll, Structure, c_long, byref

class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]

class CursorManager:
    @staticmethod
    def get_cursor_pos():
        """获取当前光标位置"""
        try:
            # 尝试使用GetCaretPos
            pt = POINT()
            if windll.user32.GetCaretPos(byref(pt)):
                return (pt.x, pt.y)
        except:
            pass
        
        try:
            # 尝试使用GetGUIThreadInfo
            from ctypes import POINTER, WINFUNCTYPE, c_void_p, c_ulong
            from ctypes.wintypes import BOOL, HWND, DWORD, WORD

            class GUITHREADINFO(Structure):
                _fields_ = [
                    ("cbSize", DWORD),
                    ("flags", DWORD),
                    ("hwndActive", HWND),
                    ("hwndFocus", HWND),
                    ("hwndCapture", HWND),
                    ("hwndMenuOwner", HWND),
                    ("hwndMoveSize", HWND),
                    ("hwndCaret", HWND),
                    ("rcCaret", POINT)
                ]

            gui_info = GUITHREADINFO(cbSize=sizeof(GUITHREADINFO))
            if windll.user32.GetGUIThreadInfo(0, byref(gui_info)):
                return (gui_info.rcCaret.x, gui_info.rcCaret.y)
        except:
            pass
        
        try:
            # 如果上述方法都失败，使用鼠标位置
            return win32gui.GetCursorPos()
        except:
            return None

    @staticmethod
    def set_cursor_pos(x, y):
        """设置光标位置"""
        try:
            # 尝试移动光标
            win32api.SetCursorPos((x, y))
            # 模拟鼠标点击
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
            return True
        except:
            return False
