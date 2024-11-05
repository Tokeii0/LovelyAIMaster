from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QListWidget, QPushButton, QLineEdit, QTextEdit, 
                              QLabel)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
import json
import os
import traceback
from PySide6.QtCore import QTimer

class SelectionKeywordsWindow(QMainWindow):
    keywords_updated = Signal()  # 当关键词更新时发出信号
    
    def __init__(self):
        super().__init__()
        try:
            self.setWindowTitle("划词关键词管理")
            self.setWindowFlags(Qt.WindowStaysOnTopHint)
            
            # 创建中心部件
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QHBoxLayout(central_widget)
            
            # 添加防抖定时器
            self.save_timer = QTimer()
            self.save_timer.setSingleShot(True)
            self.save_timer.timeout.connect(self._delayed_save)
            
            # 设置图标
            self.setWindowIcon(QIcon(r"icons\logo.ico"))
            
            # 左侧列表
            left_layout = QVBoxLayout()
            self.keywords_list = QListWidget()
            self.keywords_list.currentItemChanged.connect(self.on_item_selected)
            left_layout.addWidget(self.keywords_list)
            
            # 添加和删除按钮
            buttons_layout = QHBoxLayout()
            add_button = QPushButton("新增")
            delete_button = QPushButton("删除")
            add_button.clicked.connect(self.add_keyword)
            delete_button.clicked.connect(self.delete_keyword)
            buttons_layout.addWidget(add_button)
            buttons_layout.addWidget(delete_button)
            left_layout.addLayout(buttons_layout)
            
            layout.addLayout(left_layout)
            
            # 右侧编辑区
            right_layout = QVBoxLayout()
            
            # 标题输入
            title_layout = QHBoxLayout()
            title_label = QLabel("标题:")
            self.title_input = QLineEdit()
            self.title_input.textChanged.connect(self._schedule_save)
            title_layout.addWidget(title_label)
            title_layout.addWidget(self.title_input)
            right_layout.addLayout(title_layout)
            
            # 提示词输入
            prompt_label = QLabel("提示词:")
            self.prompt_input = QTextEdit()
            self.prompt_input.textChanged.connect(self._schedule_save)
            right_layout.addWidget(prompt_label)
            right_layout.addWidget(self.prompt_input)
            
            layout.addLayout(right_layout)
            
            # 初始化关键词列表
            self.keywords = []
            self.load_keywords()
            
            # 设置窗口大小
            self.resize(800, 600)
            
        except Exception as e:
            traceback.print_exc()
    
    def _schedule_save(self):
        """使用防抖定时器调度保存操作"""
        self.save_timer.start(500)  # 500ms 后执行保存
    
    def _delayed_save(self):
        """延迟保存操作"""
        try:
            current_row = self.keywords_list.currentRow()
            if current_row >= 0:
                # 更新当前选中项的内容
                self.keywords[current_row] = {
                    'title': self.title_input.text(),
                    'prompt': self.prompt_input.toPlainText()
                }
                # 更新列表显示
                self.keywords_list.currentItem().setText(self.title_input.text())
                # 保存到文件
                self.save_keywords()
                # 发出更新信号
                self.keywords_updated.emit()
        except Exception as e:
            traceback.print_exc()
    
    def add_keyword(self):
        """添加新关键词"""
        self.keywords.append({
            'title': '新关键词',
            'prompt': ''
        })
        self.keywords_list.addItem('新关键词')
        self.keywords_list.setCurrentRow(len(self.keywords) - 1)
        self.save_keywords()
        self.keywords_updated.emit()
    
    def delete_keyword(self):
        """删除当前选中的关键词"""
        current_row = self.keywords_list.currentRow()
        if current_row >= 0:
            self.keywords.pop(current_row)
            self.keywords_list.takeItem(current_row)
            self.save_keywords()
            self.keywords_updated.emit()
            
            # 清空输入框
            self.title_input.clear()
            self.prompt_input.clear()
    
    def on_item_selected(self, current, previous):
        """当列表选择改变时更新编辑区"""
        if current:
            row = self.keywords_list.row(current)
            keyword = self.keywords[row]
            self.title_input.setText(keyword['title'])
            self.prompt_input.setText(keyword['prompt'])
    
    def closeEvent(self, event):
        """窗口关闭时的处理"""
        try:
            # 保存最后的更改
            if self.save_timer.isActive():
                self._delayed_save()
            # 停止定时器
            self.save_timer.stop()
        except:
            pass
        event.ignore()
        self.hide()
    
    def load_keywords(self):
        """加载关键词列表"""
        try:
            # 检查文件是否存在
            if not os.path.exists('selection_keywords.json'):
                default_keywords = [
                    {
                        "title": "翻译成中文",
                        "prompt": "请将以下文本翻译成中文："
                    }
                ]
                with open('selection_keywords.json', 'w', encoding='utf-8') as f:
                    json.dump(default_keywords, f, ensure_ascii=False, indent=4)
                self.keywords = default_keywords
            else:
                # 读取关键词文件
                with open('selection_keywords.json', 'r', encoding='utf-8') as f:
                    self.keywords = json.load(f)
            
            # 更新列表显示
            self.keywords_list.clear()
            for keyword in self.keywords:
                self.keywords_list.addItem(keyword['title'])
                
        except Exception as e:
            traceback.print_exc()
            self.keywords = []
    
    def save_keywords(self):
        """保存关键词到文件"""
        try:
            with open('selection_keywords.json', 'w', encoding='utf-8') as f:
                json.dump(self.keywords, f, ensure_ascii=False, indent=4)
        except Exception as e:
            traceback.print_exc() 