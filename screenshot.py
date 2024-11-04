from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QPoint, QRect, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QPixmap
import os
from datetime import datetime

class ScreenshotOverlay(QWidget):
    screenshot_taken = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.start_pos = None
        self.end_pos = None
        self.is_drawing = False
        self.background = None
        
        # 设置全屏无边框窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 获取主屏幕大小
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        # 确保tmp目录存在
        if not os.path.exists('tmp'):
            os.makedirs('tmp')
    
    def showEvent(self, event):
        """窗口显示时捕获整个屏幕"""
        if not self.background:
            screen = QApplication.primaryScreen()
            self.background = screen.grabWindow(0)
        super().showEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        
        # 绘制半透明遮罩
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        if self.start_pos and self.end_pos and self.is_drawing:
            # 计算选区
            rect = self.get_selection_rect()
            
            # 绘制选区内的实际截图内容
            if self.background:
                target_rect = rect
                source_rect = QRect(rect)
                painter.drawPixmap(target_rect, self.background, source_rect)
            
            # 绘制选区边框
            pen = QPen(QColor(0, 174, 255), 2)
            painter.setPen(pen)
            painter.drawRect(rect)
            
            # 显示选区大小
            size_text = f"{rect.width()} × {rect.height()}"
            text_rect = painter.boundingRect(rect, Qt.AlignCenter, size_text)
            
            # 在选区上方绘制尺寸信息
            text_y = rect.top() - 25 if rect.top() > 25 else rect.bottom() + 25
            text_x = rect.center().x() - text_rect.width() / 2
            
            # 绘制文本背景
            text_bg_rect = text_rect.adjusted(-5, -5, 5, 5)
            text_bg_rect.moveCenter(QPoint(rect.center().x(), text_y))
            painter.fillRect(text_bg_rect, QColor(0, 0, 0, 160))
            
            # 绘制文本
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(text_bg_rect, Qt.AlignCenter, size_text)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            self.is_drawing = True
    
    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.end_pos = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_drawing:
            self.end_pos = event.pos()
            self.is_drawing = False
            
            # 保存截图
            rect = self.get_selection_rect()
            if rect.width() > 10 and rect.height() > 10:
                self.save_screenshot(rect)
            
            self.hide()
            self.start_pos = None
            self.end_pos = None
            self.background = None
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
            self.start_pos = None
            self.end_pos = None
            self.is_drawing = False
            self.background = None
    
    def get_selection_rect(self):
        if not self.start_pos or not self.end_pos:
            return QRect()
            
        return QRect(
            min(self.start_pos.x(), self.end_pos.x()),
            min(self.start_pos.y(), self.end_pos.y()),
            abs(self.end_pos.x() - self.start_pos.x()),
            abs(self.end_pos.y() - self.start_pos.y())
        )
    
    def save_screenshot(self, rect):
        """保存截图到tmp文件夹"""
        try:
            if self.background:
                # 从背景图中截取选定区域
                cropped = self.background.copy(rect)
                
                # 生成文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"tmp/screenshot_{timestamp}.png"
                
                # 保存图片
                cropped.save(filename)
                
                # 发送保存的文件路径
                self.screenshot_taken.emit(filename)
                
        except Exception as e:
            print(f"保存截图失败: {str(e)}")