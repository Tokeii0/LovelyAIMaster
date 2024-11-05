from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox, 
                             QInputDialog, QApplication)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QKeySequence
import json
import traceback

# 添加新的快捷键编辑组件
class HotkeyEdit(QLineEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setPlaceholderText("点击输入快捷键...")
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace:
            self.clear()
            return
            
        # 获取按键序列
        key = event.key()
        modifiers = event.modifiers()
        
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            return
            
        # 构建快捷键文本
        sequence = []
        if modifiers & Qt.AltModifier:
            sequence.append("Alt")
        if modifiers & Qt.ControlModifier:
            sequence.append("Ctrl")
        if modifiers & Qt.ShiftModifier:
            sequence.append("Shift")
            
        key_text = QKeySequence(key).toString()
        if key_text:
            sequence.append(key_text)
            
        self.setText("+".join(sequence))

class SettingsWindow(QMainWindow):
    settings_saved = Signal(dict)
    
    def __init__(self):
        super().__init__()
        try:
            self.setWindowTitle("设置")
            self.setWindowFlags(
                Qt.Window |
                Qt.WindowStaysOnTopHint |
                Qt.WindowSystemMenuHint |
                Qt.WindowCloseButtonHint
            )
            self.setWindowIcon(QIcon(r"icons\logo.ico"))
            # 确保窗口总是显示在最前面
            self.setAttribute(Qt.WA_ShowWithoutActivating, False)
            
            # 创建中心部件
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)
            
            # 添加分隔标签
            layout.addWidget(QLabel("文本AI设置"))

            # API设置
            api_layout = QHBoxLayout()
            api_label = QLabel("API Key:")
            self.api_key_input = QLineEdit()
            api_layout.addWidget(api_label)
            api_layout.addWidget(self.api_key_input)
            layout.addLayout(api_layout)
            
            # Base URL设置
            base_url_layout = QHBoxLayout()
            base_url_label = QLabel("Base URL:")
            self.base_url_input = QLineEdit()
            base_url_layout.addWidget(base_url_label)
            base_url_layout.addWidget(self.base_url_input)
            layout.addLayout(base_url_layout)
            
            # 模型选择
            model_layout = QHBoxLayout()
            model_label = QLabel("模型:")
            self.model_combo = QComboBox()
            self.model_combo.setEditable(True)  # 设置为可编辑
            self.model_combo.addItems(["yi-lightning", "gpt-4o"])
            self.model_combo.setInsertPolicy(QComboBox.InsertPolicy.InsertAtBottom)  # 新项添加到底部
            model_layout.addWidget(model_label)
            model_layout.addWidget(self.model_combo)
            layout.addLayout(model_layout)
            
            # API类型选择
            api_type_layout = QHBoxLayout()
            api_type_label = QLabel("API类型:")
            self.api_type_combo = QComboBox()
            self.api_type_combo.setEditable(True)  # 设置为可编辑
            self.api_type_combo.addItems(["OpenAI", "Azure", "Claude"])
            self.api_type_combo.setInsertPolicy(QComboBox.InsertPolicy.InsertAtBottom)
            api_type_layout.addWidget(api_type_label)
            api_type_layout.addWidget(self.api_type_combo)
            layout.addLayout(api_type_layout)
            
            # 代理设置
            proxy_layout = QHBoxLayout()
            proxy_label = QLabel("代理设置:")
            self.proxy_enabled = QCheckBox("启用代理")
            self.proxy_input = QLineEdit()
            self.proxy_input.setPlaceholderText("127.0.0.1:1090")
            proxy_layout.addWidget(proxy_label)
            proxy_layout.addWidget(self.proxy_enabled)
            proxy_layout.addWidget(self.proxy_input)
            layout.addLayout(proxy_layout)
            
            # 预设设置
            preset_layout = QHBoxLayout()
            preset_label = QLabel("预设配置:")
            self.preset_combo = QComboBox()
            self.load_presets()  # 加载预
            preset_layout.addWidget(preset_label)
            preset_layout.addWidget(self.preset_combo)
            layout.addLayout(preset_layout)
            
            # 添加预设管理按钮
            preset_buttons_layout = QHBoxLayout()
            save_preset_button = QPushButton("保存为预设")
            delete_preset_button = QPushButton("删除预设")
            save_preset_button.clicked.connect(self.save_preset)
            delete_preset_button.clicked.connect(self.delete_preset)
            preset_buttons_layout.addWidget(save_preset_button)
            preset_buttons_layout.addWidget(delete_preset_button)
            layout.addLayout(preset_buttons_layout)

            # 连接预设选择信号
            self.preset_combo.currentTextChanged.connect(self.load_preset_config)
            
            # 添加快捷键设置
            hotkey_layout = QHBoxLayout()
            hotkey_label = QLabel("快捷键设置:")
            self.hotkey1_edit = HotkeyEdit()
            self.hotkey2_edit = HotkeyEdit()
            hotkey_layout.addWidget(hotkey_label)
            hotkey_layout.addWidget(self.hotkey1_edit)
            hotkey_layout.addWidget(QLabel("或"))
            hotkey_layout.addWidget(self.hotkey2_edit)
            layout.addLayout(hotkey_layout)
            
            # 添加划词解释快捷键设置
            selection_hotkey_layout = QHBoxLayout()
            selection_hotkey_label = QLabel("划词解释快捷键:")
            self.selection_hotkey_edit = HotkeyEdit()
            selection_hotkey_layout.addWidget(selection_hotkey_label)
            selection_hotkey_layout.addWidget(self.selection_hotkey_edit)
            layout.addLayout(selection_hotkey_layout)

            # 添加图像AI设置分隔
            layout.addWidget(QLabel("\n图像AI设置"))

            # 图像API设置
            image_api_layout = QHBoxLayout()
            image_api_label = QLabel("图像API Key:")
            self.image_api_key_input = QLineEdit()
            image_api_layout.addWidget(image_api_label)
            image_api_layout.addWidget(self.image_api_key_input)
            layout.addLayout(image_api_layout)

            # 图像Base URL设置
            image_base_url_layout = QHBoxLayout()
            image_base_url_label = QLabel("图像Base URL:")
            self.image_base_url_input = QLineEdit()
            image_base_url_layout.addWidget(image_base_url_label)
            image_base_url_layout.addWidget(self.image_base_url_input)
            layout.addLayout(image_base_url_layout)

            # 图像模型选择
            image_model_layout = QHBoxLayout()
            image_model_label = QLabel("图像模型:")
            self.image_model_combo = QComboBox()
            self.image_model_combo.setEditable(True)  # 设置为可编辑
            self.image_model_combo.addItems(["yi-vision", "gpt-4-vision"])
            self.image_model_combo.setInsertPolicy(QComboBox.InsertPolicy.InsertAtBottom)
            image_model_layout.addWidget(image_model_label)
            image_model_layout.addWidget(self.image_model_combo)
            layout.addLayout(image_model_layout)

            # 图像API类型选择
            image_api_type_layout = QHBoxLayout()
            image_api_type_label = QLabel("图像API类型:")
            self.image_api_type_combo = QComboBox()
            self.image_api_type_combo.setEditable(True)  # 设置为可编辑
            self.image_api_type_combo.addItems(["OpenAI", "Azure"])
            self.image_api_type_combo.setInsertPolicy(QComboBox.InsertPolicy.InsertAtBottom)
            image_api_type_layout.addWidget(image_api_type_label)
            image_api_type_layout.addWidget(self.image_api_type_combo)
            layout.addLayout(image_api_type_layout)

            # 图像代理设置
            image_proxy_layout = QHBoxLayout()
            image_proxy_label = QLabel("图像代理设置:")
            self.image_proxy_enabled = QCheckBox("启用代理")
            self.image_proxy_input = QLineEdit()
            self.image_proxy_input.setPlaceholderText("127.0.0.1:1090")
            image_proxy_layout.addWidget(image_proxy_label)
            image_proxy_layout.addWidget(self.image_proxy_enabled)
            image_proxy_layout.addWidget(self.image_proxy_input)
            layout.addLayout(image_proxy_layout)

            # 添加截图快捷键设置
            screenshot_hotkey_layout = QHBoxLayout()
            screenshot_hotkey_label = QLabel("截图快捷键:")
            self.screenshot_hotkey_edit = HotkeyEdit()
            screenshot_hotkey_layout.addWidget(screenshot_hotkey_label)
            screenshot_hotkey_layout.addWidget(self.screenshot_hotkey_edit)
            layout.addLayout(screenshot_hotkey_layout)

            # 添加连续对话快捷键设置
            chat_hotkey_layout = QHBoxLayout()
            chat_hotkey_label = QLabel("连续对话快捷键:")
            self.chat_hotkey_edit = HotkeyEdit()
            chat_hotkey_layout.addWidget(chat_hotkey_label)
            chat_hotkey_layout.addWidget(self.chat_hotkey_edit)
            layout.addLayout(chat_hotkey_layout)

            # 保存按钮
            save_button = QPushButton("保存")
            save_button.clicked.connect(self.save_settings)
            layout.addWidget(save_button)
            
            # 加载设置
            self.load_settings()
            
            # 设置窗口大小
            self.resize(400, 200)
        except Exception as e:
            print(f"设置窗口初始化错误: {str(e)}")
            print("错误详情:")
            traceback.print_exc()
    
    def load_settings(self):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 文本AI设置
                self.api_key_input.setText(config.get('api_key', ''))
                self.base_url_input.setText(config.get('base_url', ''))
                self.model_combo.setCurrentText(config.get('model', ''))
                self.api_type_combo.setCurrentText(config.get('api_type', ''))
                self.proxy_enabled.setChecked(config.get('proxy_enabled', False))
                self.proxy_input.setText(config.get('proxy', ''))
                
                # 图像AI设置
                self.image_api_key_input.setText(config.get('image_api_key', ''))
                self.image_base_url_input.setText(config.get('image_base_url', ''))
                self.image_model_combo.setCurrentText(config.get('image_model', ''))
                self.image_api_type_combo.setCurrentText(config.get('image_api_type', ''))
                self.image_proxy_enabled.setChecked(config.get('image_proxy_enabled', False))
                self.image_proxy_input.setText(config.get('image_proxy', ''))
                
                # 快捷键设置
                self.hotkey1_edit.setText(config.get('hotkey1', 'Alt+Q'))
                self.hotkey2_edit.setText(config.get('hotkey2', 'Alt+W'))
                self.selection_hotkey_edit.setText(config.get('selection_hotkey', 'Alt+2'))
                self.screenshot_hotkey_edit.setText(config.get('screenshot_hotkey', 'Alt+3'))

                # 添加连续对话快捷键设置
                self.chat_hotkey_edit.setText(config.get('chat_hotkey', 'ctrl+4'))

                # 设置模型，如果是自定义值则添加到列表中
                current_model = config.get('model', 'gpt-4o')
                if current_model not in [self.model_combo.itemText(i) for i in range(self.model_combo.count())]:
                    self.model_combo.addItem(current_model)
                self.model_combo.setCurrentText(current_model)

                # 设置API类型，如果是自定义值则添加到列表中
                current_api_type = config.get('api_type', 'OpenAI')
                if current_api_type not in [self.api_type_combo.itemText(i) for i in range(self.api_type_combo.count())]:
                    self.api_type_combo.addItem(current_api_type)
                self.api_type_combo.setCurrentText(current_api_type)

                # 设置图像模型，如果是自定义值则添加到列表中
                current_image_model = config.get('image_model', 'yi-vision')
                if current_image_model not in [self.image_model_combo.itemText(i) for i in range(self.image_model_combo.count())]:
                    self.image_model_combo.addItem(current_image_model)
                self.image_model_combo.setCurrentText(current_image_model)

                # 设置图像API类型，如果是自定义值则添加到列表中
                current_image_api_type = config.get('image_api_type', 'OpenAI')
                if current_image_api_type not in [self.image_api_type_combo.itemText(i) for i in range(self.image_api_type_combo.count())]:
                    self.image_api_type_combo.addItem(current_image_api_type)
                self.image_api_type_combo.setCurrentText(current_image_api_type)
        except Exception as e:
            print(f"加载设置失败: {str(e)}")
    
    def save_settings(self):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                old_config = json.load(f)

            config = {
                # 文本AI设置
                'api_key': self.api_key_input.text(),
                'base_url': self.base_url_input.text(),
                'model': self.model_combo.currentText(),
                'api_type': self.api_type_combo.currentText(),
                'proxy_enabled': bool(self.proxy_enabled.isChecked()),
                'proxy': self.proxy_input.text(),
                
                # 图像AI设置
                'image_api_key': self.image_api_key_input.text(),
                'image_base_url': self.image_base_url_input.text(),
                'image_model': self.image_model_combo.currentText(),
                'image_api_type': self.image_api_type_combo.currentText(),
                'image_proxy_enabled': bool(self.image_proxy_enabled.isChecked()),
                'image_proxy': self.image_proxy_input.text(),
                
                # 快捷键设置
                'hotkey1': self.hotkey1_edit.text() or 'Alt+Q',
                'hotkey2': self.hotkey2_edit.text() or 'Alt+W',
                'selection_hotkey': self.selection_hotkey_edit.text() or 'Alt+2',
                'screenshot_hotkey': self.screenshot_hotkey_edit.text() or 'Alt+3',
                'chat_hotkey': self.chat_hotkey_edit.text() or 'ctrl+4',
            }

            # 检查热键是否发生变化
            hotkeys_changed = (
                config['hotkey1'].lower() != old_config.get('hotkey1', '').lower() or
                config['hotkey2'].lower() != old_config.get('hotkey2', '').lower() or
                config['selection_hotkey'].lower() != old_config.get('selection_hotkey', '').lower() or
                config['screenshot_hotkey'].lower() != old_config.get('screenshot_hotkey', '').lower() or
                config['chat_hotkey'].lower() != old_config.get('chat_hotkey', '').lower()
            )

            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            self.settings_saved.emit({"config": config, "hotkeys_changed": hotkeys_changed})
            self.hide()
        except Exception as e:
            print(f"保存设置失败: {str(e)}")
            traceback.print_exc()
    
    def load_presets(self):
        """加载预设配置列表"""
        try:
            with open('presets.json', 'r', encoding='utf-8') as f:
                presets = json.load(f)
            self.preset_combo.clear()
            self.preset_combo.addItem("选择预设...")
            self.preset_combo.addItems(presets.keys())
        except FileNotFoundError:
            with open('presets.json', 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"加载预设失败: {str(e)}")
    
    def save_preset(self):
        """保存当前配置为预设"""
        try:
            preset_name, ok = QInputDialog.getText(self, "保存预设", "请输入预设名称:")
            if ok and preset_name:
                config = {
                    'api_key': self.api_key_input.text(),
                    'base_url': self.base_url_input.text(),
                    'model': self.model_combo.currentText(),
                    'api_type': self.api_type_combo.currentText(),
                    'proxy_enabled': self.proxy_enabled.isChecked(),
                    'proxy': self.proxy_input.text()
                }
                
                try:
                    with open('presets.json', 'r', encoding='utf-8') as f:
                        presets = json.load(f)
                except FileNotFoundError:
                    presets = {}
                
                presets[preset_name] = config
                
                with open('presets.json', 'w', encoding='utf-8') as f:
                    json.dump(presets, f, indent=4, ensure_ascii=False)
                
                self.load_presets()
        except Exception as e:
            print(f"保存预设失败: {str(e)}")
    
    def delete_preset(self):
        """删除当前选择的预设"""
        current_preset = self.preset_combo.currentText()
        if current_preset and current_preset != "选择预设...":
            try:
                with open('presets.json', 'r', encoding='utf-8') as f:
                    presets = json.load(f)
                
                if current_preset in presets:
                    del presets[current_preset]
                    
                    with open('presets.json', 'w', encoding='utf-8') as f:
                        json.dump(presets, f, indent=4, ensure_ascii=False)
                    
                    self.load_presets()
            except Exception as e:
                print(f"删除预设失败: {str(e)}")
    
    def load_preset_config(self, preset_name):
        """加载选中的预设配置"""
        if preset_name and preset_name != "选择预设...":
            try:
                with open('presets.json', 'r', encoding='utf-8') as f:
                    presets = json.load(f)
                
                if preset_name in presets:
                    config = presets[preset_name]
                    self.api_key_input.setText(config.get('api_key', ''))
                    self.base_url_input.setText(config.get('base_url', ''))
                    self.model_combo.setCurrentText(config.get('model', ''))
                    self.api_type_combo.setCurrentText(config.get('api_type', ''))
                    self.proxy_enabled.setChecked(config.get('proxy_enabled', False))
                    self.proxy_input.setText(config.get('proxy', ''))
                    
                    # 立即保存并发送配置
                    self.save_settings()
            except Exception as e:
                print(f"加载预设置失败: {str(e)}")
    
    def closeEvent(self, event):
        """重写关闭事件，使窗口关闭时只隐藏而不退出程序"""
        event.ignore()  # 忽略原始的关闭事件
        self.hide()     # 只隐藏窗口
    
    def showEvent(self, event):
        """重写显示事件以确保窗口正确显示"""
        super().showEvent(event)
        self.raise_()
        self.activateWindow()
    
    def show(self):
        """重写show方法，确保窗口显示在最前面"""
        try:
            super().show()
            self.raise_()
            self.activateWindow()
            QApplication.processEvents()
        except Exception as e:
            traceback.print_exc()