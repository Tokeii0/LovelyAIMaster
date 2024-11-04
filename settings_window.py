from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox, QInputDialog)
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
    settings_saved = Signal(object)
    
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
            
            # 确保窗口总是显示在最前面
            self.setAttribute(Qt.WA_ShowWithoutActivating, False)
            
            # 创建中心部件
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)
            
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
            self.model_combo.addItems(["yi-lightning", "gpt-4o"])
            model_layout.addWidget(model_label)
            model_layout.addWidget(self.model_combo)
            layout.addLayout(model_layout)
            
            # API类型选择
            api_type_layout = QHBoxLayout()
            api_type_label = QLabel("API类型:")
            self.api_type_combo = QComboBox()
            self.api_type_combo.addItems(["OpenAI", "Azure", "Claude"])
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
                self.api_key_input.setText(config.get('api_key', ''))
                self.base_url_input.setText(config.get('base_url', 'https://api.openai.com/v1'))
                self.model_combo.setCurrentText(config.get('model', 'yi-lightning'))
                self.api_type_combo.setCurrentText(config.get('api_type', 'OpenAI'))
                self.proxy_enabled.setChecked(config.get('proxy_enabled', False))
                self.proxy_input.setText(config.get('proxy', '127.0.0.1:1090'))
                
                # 加载快捷键设置
                self.hotkey1_edit.setText(config.get('hotkey1', 'Alt+Q'))
                self.hotkey2_edit.setText(config.get('hotkey2', 'Alt+W'))
        except Exception as e:
            print(f"加载设置失败: {str(e)}")
    
    def save_settings(self):
        try:
            # 先获取旧的配置
            try:
                with open('config.json', 'r', encoding='utf-8') as f:
                    old_config = json.load(f)
            except:
                old_config = {}

            # 准备新的配置
            config = {
                'api_key': self.api_key_input.text(),
                'base_url': self.base_url_input.text(),
                'model': self.model_combo.currentText(),
                'api_type': self.api_type_combo.currentText(),
                'proxy_enabled': bool(self.proxy_enabled.isChecked()),
                'proxy': self.proxy_input.text(),
                'hotkey1': self.hotkey1_edit.text() or 'Alt+Q',
                'hotkey2': self.hotkey2_edit.text() or 'Alt+W'
            }

            # 检查热键是否发生变化
            hotkeys_changed = (
                config['hotkey1'].lower() != old_config.get('hotkey1', 'Alt+Q').lower() or
                config['hotkey2'].lower() != old_config.get('hotkey2', 'Alt+W').lower()
            )

            # 保存配���
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            # 发送信号时包含热键变化状态
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
        """重写show方法"""
        super().show()
        self.repaint()
        QApplication.processEvents()