from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QWidget, QApplication, QDialog, QVBoxLayout, QLabel
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import Signal, Qt, QRect
import traceback

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFixedSize(1024, 1024)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建支持透明通道的图片标签
        image_label = QLabel()
        pixmap = QPixmap("assets/app.png")
        # 确保支持透明通道
        if not pixmap.hasAlphaChannel():
            pixmap = pixmap.convertToFormat(QPixmap.Format.Format_ARGB32)
        pixmap = pixmap.scaled(1024, 1024, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # 创建一个透明的新pixmap
        final_pixmap = QPixmap(pixmap.size())
        final_pixmap.fill(Qt.transparent)
        
        # 在新pixmap上绘制
        painter = QPainter(final_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 先绘制原图
        painter.drawPixmap(0, 0, pixmap)
        
        # 计算文本框的位置和大小 - 调整为长方形并往下移动
        box_width = 300
        box_height = 200
        x = (pixmap.width() - box_width) // 2
        y = (pixmap.height() - box_height) // 2 + 100  # 往下移动100像素
        
        # 绘制半透明背景
        bg_color = QColor(255, 255, 255, 178)  # 70% 透明度的白色
        painter.fillRect(x, y, box_width, box_height, bg_color)
        
        # 设置文本样式
        painter.setPen(QColor(51, 51, 51))  # 深灰色文字
        font = painter.font()
        font.setPointSize(14)
        painter.setFont(font)
        
        # 绘制文本 - 移除多余的换行和空格
        text = "AI高手高手高高手 v0.3\n\n作者：Tokeii\n感谢：猫捉鱼铃酒吧"
        
        # 计算文本区域并绘制 - 直接使用文本框的矩形区域
        text_rect = QRect(x, y, box_width, box_height)
        
        # 使用 AlignCenter 确保文本在矩形内完全居中
        painter.drawText(text_rect, Qt.AlignCenter, text)
        
        # 绘制文本框边框
        painter.setPen(QColor(200, 200, 200))
        painter.drawRect(x, y, box_width, box_height)
        
        painter.end()
        
        # 显示最终图片
        image_label.setPixmap(final_pixmap)
        layout.addWidget(image_label)
        
        # 设置窗口背景透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 添加点击事件处理
        self.mousePressEvent = lambda event: self.hide()

class SystemTrayIcon(QSystemTrayIcon):
    show_settings_signal = Signal()
    show_prompts_signal = Signal()
    show_selection_keywords_signal = Signal()
    reset_hotkeys_signal = Signal()
    quit_signal = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            self.setIcon(QIcon("assets/logo.ico"))
            self.setToolTip("AI高手高手高高手 v0.3 ")
            
            # 创建右键菜单
            self.menu = QMenu()
            
            # 添加菜单项
            self.settings_action = self.menu.addAction("设置")
            self.prompts_action = self.menu.addAction("提示词管理")
            self.selection_keywords_action = self.menu.addAction("划词关键词管理")
            self.menu.addSeparator()
            #self.reset_hotkeys_action = self.menu.addAction("重置热键")
            self.menu.addSeparator()
            self.about_action = self.menu.addAction("关于")
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
            # self.reset_hotkeys_action.triggered.connect(
            #     lambda: self.reset_hotkeys_signal.emit()
            # )
            self.about_action.triggered.connect(self.show_about_dialog)
            self.quit_action.triggered.connect(
                lambda: self.quit_signal.emit()
            )
            
            # 显示托盘图标
            self.show()
        except Exception as e:
            print(f"托盘图标初始化错误: {str(e)}")
            print("错误详情:")
            traceback.print_exc()
    
    def show_about_dialog(self):
        """显示关于对话框"""
        # if not hasattr(self, 'about_dialog'):
        #     self.about_dialog = AboutDialog()
        # self.about_dialog.show()
        pass