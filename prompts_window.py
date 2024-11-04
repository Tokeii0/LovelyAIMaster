from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QLabel, QLineEdit, QTextEdit)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon
import json
import traceback
import os

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
            
            # 添加防抖定时器
            self.save_timer = QTimer()
            self.save_timer.setSingleShot(True)  # 设置为单次触发
            self.save_timer.timeout.connect(self._delayed_save)
            
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
            self.title_input.textChanged.connect(self._schedule_save)  # 使用防抖
            title_layout.addWidget(title_label)
            title_layout.addWidget(self.title_input)
            right_layout.addLayout(title_layout)
            
            # 内容输入
            content_label = QLabel("内容:")
            self.content_input = QTextEdit()
            self.content_input.textChanged.connect(self._schedule_save)  # 使用防抖
            right_layout.addWidget(content_label)
            right_layout.addWidget(self.content_input)
            
            layout.addLayout(right_layout)
            
            # 初始化提示词列表
            self.prompts = []
            self.load_prompts()
            
            # 设置窗口大小
            self.resize(800, 600)
            
        except Exception as e:
            traceback.print_exc()
    
    def _schedule_save(self):
        """使用防抖定时器延迟保存"""
        self.save_timer.stop()  # 停止之前的定时器
        self.save_timer.start(500)  # 500ms 后触发保存
    
    def _delayed_save(self):
        """延迟保存的实际执行函数"""
        try:
            current_row = self.prompts_list.currentRow()
            if current_row >= 0:
                title = self.title_input.text()
                content = self.content_input.toPlainText()
                
                # 更新数据
                if len(self.prompts) > current_row:
                    self.prompts[current_row] = {
                        'title': title,
                        'content': content
                    }
                    
                    # 更新列表显示
                    current_item = self.prompts_list.item(current_row)
                    if current_item:
                        current_item.setText(title)
                    
                    # 保存到文件
                    self.save_prompts()
        except Exception as e:
            traceback.print_exc()
    
    def save_prompts(self):
        """保存提示词到文件"""
        try:
            # 确保提示词列表不为空
            if not self.prompts:
                self.prompts = []
            
            # 使用临时文件保存
            temp_file = 'prompts.json.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, indent=4, ensure_ascii=False)
            
            # 成功写入后替换原文件
            if os.path.exists(temp_file):
                if os.path.exists('prompts.json'):
                    os.replace(temp_file, 'prompts.json')
                else:
                    os.rename(temp_file, 'prompts.json')
            
            # 发送更新信号
            self.prompts_updated.emit()
            
        except Exception as e:
            traceback.print_exc()
            # 清理临时文件
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
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
    
    def on_item_selected(self, current, previous):
        """当列表选择改变时更新编辑区"""
        if current:
            row = self.prompts_list.row(current)
            prompt = self.prompts[row]
            self.title_input.setText(prompt['title'])
            self.content_input.setText(prompt['content'])
    
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
    
    def load_prompts(self):
        """加载提示词列表"""
        try:
            # 检查文件是否存在
            if not os.path.exists('prompts.json'):
                #print("提示词文件不存在，创建默认文件")
                default_prompts = [
                    {
                        "title": "例提示词",
                        "content": "这是一个示例提示词"
                    }
                ]
                with open('prompts.json', 'w', encoding='utf-8') as f:
                    json.dump(default_prompts, f, ensure_ascii=False, indent=4)
                self.prompts = default_prompts
            else:
                # 读取提示词文件
                with open('prompts.json', 'r', encoding='utf-8') as f:
                    self.prompts = json.load(f)
            
            # 更新列表显示
            self.prompts_list.clear()
            for prompt in self.prompts:
                self.prompts_list.addItem(prompt['title'])
                
        except json.JSONDecodeError as e:
            print(f"提示词文件格式错误: {str(e)}")
            self.prompts = []
        except Exception as e:
            #print(f"加载提示词失败: {str(e)}")
            traceback.print_exc()
            self.prompts = []