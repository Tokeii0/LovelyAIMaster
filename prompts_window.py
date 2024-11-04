from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QLabel, QLineEdit, QTextEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
import json
import traceback

class PromptsWindow(QMainWindow):
    prompts_updated = Signal()
    
    def __init__(self):
        super().__init__()
        try:
            self.setWindowTitle("提示词管理")
            self.setWindowFlags(Qt.WindowStaysOnTopHint)
            
            # 创建中心部件
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QHBoxLayout(central_widget)
                
            # 左侧列表
            left_layout = QVBoxLayout()
            self.prompts_list = QListWidget()
            self.prompts_list.currentItemChanged.connect(self.on_item_selected)
            left_layout.addWidget(self.prompts_list)
            
            # 添加和删除按钮
            buttons_layout = QHBoxLayout()
            add_button = QPushButton("新增")
            delete_button = QPushButton("删除")
            add_button.clicked.connect(self.add_prompt)
            delete_button.clicked.connect(self.delete_prompt)
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
            title_layout.addWidget(title_label)
            title_layout.addWidget(self.title_input)
            right_layout.addLayout(title_layout)
            
            # 内容输入
            content_label = QLabel("内容:")
            self.content_input = QTextEdit()
            right_layout.addWidget(content_label)
            right_layout.addWidget(self.content_input)
            
            # 保存按钮
            save_button = QPushButton("保存")
            save_button.clicked.connect(self.save_prompt)
            right_layout.addWidget(save_button)
            
            layout.addLayout(right_layout)
            
            # 加载提示词
            self.load_prompts()
            
            # 设置窗口大小
            self.resize(600, 400)
        except Exception as e:
            #print(f"提示词管理窗口初始化错误: {str(e)}")
            #print("错误详情:")
            traceback.print_exc()
    
    def load_prompts(self):
        """加载提示词"""
        try:
            #print("正在加载提示词...")
            with open('prompts.json', 'r', encoding='utf-8') as f:
                self.prompts = json.load(f)
            self.prompts_list.clear()
            self.prompts_list.addItems([p['title'] for p in self.prompts])
            #print(f"成功加载 {len(self.prompts)} 个提示词")
        except Exception as e:
            #print(f"加载提示词失败: {str(e)}")
            #print("错误详情:")
            traceback.print_exc()
            self.prompts = []
    
    def save_prompts(self):
        """保存提示词到文件"""
        try:
            #print("正在保存提示词到文件...")
            #print(f"当前提示词列表: {self.prompts}")
            
            # 确保提示词列表不为空
            if not self.prompts:
                #print("警告: 提示词列表为空")
                self.prompts = []
            
            # 确保prompts.json文件存在
            try:
                with open('prompts.json', 'r', encoding='utf-8') as f:
                    pass
            except FileNotFoundError:
                #print("prompts.json不存在，将创建新文件")
                with open('prompts.json', 'w', encoding='utf-8') as f:
                    json.dump([], f)
            
            # 保存到文件
            with open('prompts.json', 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, indent=4, ensure_ascii=False)
            
            # 发送更新信号
            self.prompts_updated.emit()
            #print("提示词成功保存到文件")
            
        except Exception as e:
            #print(f"保存提示词到文件时出错: {str(e)}")
            traceback.print_exc()
    
    def add_prompt(self):
        """添加新提示词"""
        self.prompts.append({
            'title': '新提示词',
            'content': ''
        })
        self.prompts_list.addItem('新提示词')
        self.prompts_list.setCurrentRow(len(self.prompts) - 1)
        self.save_prompts()
    
    def delete_prompt(self):
        """删除当前选中的提示词"""
        current_row = self.prompts_list.currentRow()
        if current_row >= 0:
            self.prompts.pop(current_row)
            self.prompts_list.takeItem(current_row)
            self.save_prompts()
            
            # 清空输入框
            self.title_input.clear()
            self.content_input.clear()
    
    def save_prompt(self):
        """保存当前编辑的提示词"""
        try:
            current_row = self.prompts_list.currentRow()
            #print(f"当前选中行: {current_row}")
            
            if current_row >= 0:
                title = self.title_input.text()
                content = self.content_input.toPlainText()
                
                #print(f"正在保存提示词 - 标题: {title}, 内容长度: {len(content)}")
                
                # 确保 self.prompts 已初始化
                if not hasattr(self, 'prompts'):
                    #print("prompts列表未初始化，正在初始化...")
                    self.prompts = []
                
                # 确保索引有效
                while len(self.prompts) <= current_row:
                    self.prompts.append({})
                
                self.prompts[current_row] = {
                    'title': title,
                    'content': content
                }
                
                # 更新列表项显示
                current_item = self.prompts_list.item(current_row)
                if current_item:
                    current_item.setText(title)
                
                self.save_prompts()
                #print("提示词保存成功")
                
        except Exception as e:
            #print(f"保存提示词时出错: {str(e)}")
            traceback.print_exc()
    
    def on_item_selected(self, current, previous):
        """当列表选择改变时更新编辑区"""
        if current:
            row = self.prompts_list.row(current)
            prompt = self.prompts[row]
            self.title_input.setText(prompt['title'])
            self.content_input.setText(prompt['content'])
    
    def closeEvent(self, event):
        """重写关闭事件，使窗口关闭时只隐藏而不退出程序"""
        event.ignore()  # 忽略原始的关闭事件
        self.hide()     # 只隐藏窗口