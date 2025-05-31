from PySide6.QtWidgets import QMenu, QWidget, QApplication
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon
from utils.plugin_manager import PluginManager
import json
import os
import traceback

class SelectionMenu(QMenu):
    plugin_triggered = Signal(object)  # 修改：只需要传递插件对象
    ai_query_triggered = Signal()  # 修改：不需要传递参数
    keyword_query_triggered = Signal(str)  # 修改：只需要传递提示词
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plugin_manager = PluginManager()
        self.keywords = []  # 添加关键词列表
        self.load_keywords()  # 加载关键词
        self.setup_menu()
    
    def setup_menu(self):
        # AI查询选项
        ai_action = QAction("询问AI", self)
        ai_action.triggered.connect(lambda: self.ai_query_triggered.emit())  # 修改：不传参数
        self.addAction(ai_action)
        
        # 添加分隔线
        self.addSeparator()
        
        # 关键词选项
        for keyword in self.keywords:
            action = QAction(keyword['title'], self)
            action.setToolTip(keyword['prompt'])
            # 修改：只发送提示词
            action.triggered.connect(
                lambda checked, p=keyword['prompt']: self.keyword_query_triggered.emit(p)
            )
            self.addAction(action)
        
        # 添加分隔线
        if self.keywords:
            self.addSeparator()
        
        # 插件选项
        for plugin in self.plugin_manager.get_plugins():
            action = QAction(plugin.name, self)
            action.setToolTip(plugin.description)
            # 修改：只发送插件对象
            action.triggered.connect(
                lambda checked, p=plugin: self.plugin_triggered.emit(p)
            )
            self.addAction(action)
    
    def load_keywords(self):
        """加载关键词"""
        try:
            if os.path.exists('selection_keywords.json'):
                with open('selection_keywords.json', 'r', encoding='utf-8') as f:
                    self.keywords = json.load(f)
        except Exception as e:
            traceback.print_exc()
            self.keywords = []
    
    def refresh_menu(self):
        """刷新菜单内容"""
        self.clear()  # 清除所有现有菜单项
        self.load_keywords()  # 重新加载关键词
        self.setup_menu()  # 重新设置菜单
    
    def show_menu(self, pos, text):
        """显示菜单"""
        self.selected_text = text
        self.popup(pos) 