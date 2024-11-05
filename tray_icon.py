from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QWidget, QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal
import traceback

class SystemTrayIcon(QSystemTrayIcon):
    show_settings_signal = Signal()
    show_prompts_signal = Signal()
    show_selection_keywords_signal = Signal()
    reset_hotkeys_signal = Signal()
    quit_signal = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            self.setIcon(QIcon("icons/logo.ico"))
            self.setToolTip("AI高手高手高高手")
            
            # 创建右键菜单
            self.menu = QMenu()
            
            # 添加菜单项
            self.settings_action = self.menu.addAction("设置")
            self.prompts_action = self.menu.addAction("提示词管理")
            self.selection_keywords_action = self.menu.addAction("划词关键词管理")
            self.menu.addSeparator()
            self.reset_hotkeys_action = self.menu.addAction("重置热键")
            self.menu.addSeparator()
            self.quit_action = self.menu.addAction("退出")
            
            # 设置右键菜单
            self.setContextMenu(self.menu)
            
            # 连接信号
            self.settings_action.triggered.connect(
                lambda: self.show_settings_signal.emit()
            )
            self.prompts_action.triggered.connect(
                lambda: self.show_prompts_signal.emit()
            )
            self.selection_keywords_action.triggered.connect(
                lambda: self.show_selection_keywords_signal.emit()
            )
            self.reset_hotkeys_action.triggered.connect(
                lambda: self.reset_hotkeys_signal.emit()
            )
            self.quit_action.triggered.connect(
                lambda: self.quit_signal.emit()
            )
            
            # 显示托盘图标
            self.show()
        except Exception as e:
            print(f"托盘图标初始化错误: {str(e)}")
            print("错误详情:")
            traceback.print_exc()