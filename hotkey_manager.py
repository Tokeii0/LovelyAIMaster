import time
import threading
import traceback
from PySide6.QtCore import QObject, QTimer, Signal
import keyboard
import json

from threading import Thread

class GlobalHotkey(QObject):
    triggered = Signal()
    selection_triggered = Signal()
    hotkey_failed = Signal(str)
    screenshot_triggered = Signal()
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.hotkey_registered = False
        self.retry_count = 0
        self.max_retries = 3
        self.lock = threading.Lock()
        self.last_trigger_time = time.time()
        
        # 缩短检查间隔
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_hotkey_status)
        self.check_timer.start(2000)  # 改为2秒
        
        self.thread_check_timer = QTimer()
        self.thread_check_timer.timeout.connect(self._check_thread_status)
        self.thread_check_timer.start(1000)  # 改为1秒
        
        self.force_restart_timer = QTimer()
        self.force_restart_timer.timeout.connect(self.force_restart)
        self.force_restart_timer.start(60000)  # 改为1分钟
        
        # 添加快捷键配置
        self.hotkey1 = 'alt+q'  # 默认快捷键
        self.hotkey2 = 'alt+w'  # 默认快捷键
        self.selection_hotkey = 'alt+2'  # 划词搜索快捷键
        self.screenshot_hotkey = 'alt+3'  # 截图热键
        
        # 加载配置的快捷键
        self.load_hotkey_config()
        
        self._start_monitoring()
    
    def _check_thread_status(self):
        """检查监听线程状态"""
        try:
            if not hasattr(self, 'monitor_thread') or not self.monitor_thread.is_alive():
                self.restart()
            # 短无响应时间判断
            elif time.time() - self.last_trigger_time > 15:  # 改为15秒
                self.restart()
        except Exception as e:
            self.restart()  # 出现常时也重启
    
    def force_restart(self):
        """强制重启热键监听"""
        try:
            #print("执行定期强制重启")
            self.restart()
        except Exception as e:
            pass
    
    def restart(self):
        """重新启动热键监听"""
        with self.lock:
            try:
                # 先停止所有定时器
                self.check_timer.stop()
                self.thread_check_timer.stop()
                self.force_restart_timer.stop()

                # 确保旧的监听线程完全停止
                self.running = False
                self.hotkey_registered = False
                
                # 清理现有热键
                try:
                    keyboard.unhook_all()
                except:
                    pass

                # 等待旧线程结束
                if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
                    try:
                        self.monitor_thread.join(timeout=0.5)  # 最多等待0.5秒
                    except:
                        pass

                # 重置状态
                self.running = True
                self.retry_count = 0
                self.last_trigger_time = time.time()

                # 启动新的监听线程
                self._start_monitoring()

                # 重新启动定时器
                self.check_timer.start(2000)
                self.thread_check_timer.start(1000)
                self.force_restart_timer.start(60000)

            except Exception as e:
                traceback.print_exc()
                # 发送失败信号
                self.hotkey_failed.emit(f"重启失败: {str(e)}")
                # 确保定时器重新启动
                self._ensure_timers_running()

    def _ensure_timers_running(self):
        """确保所有定时器都在运行"""
        try:
            if not self.check_timer.isActive():
                self.check_timer.start(2000)
            if not self.thread_check_timer.isActive():
                self.thread_check_timer.start(1000)
            if not self.force_restart_timer.isActive():
                self.force_restart_timer.start(60000)
        except:
            pass

    def _start_monitoring(self):
        """启动热键监听线程"""
        try:
            # 确保之前的线程已经停止
            if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
                self.running = False
                try:
                    self.monitor_thread.join(timeout=0.5)
                except:
                    pass

            # 理现有热键
            self._clean_existing_hotkey()
            
            # 创建新线程
            self.monitor_thread = Thread(target=self._monitor_hotkey, daemon=True)
            self.monitor_thread.start()

            # 等待线程实际启动
            time.sleep(0.1)
            
            # 验证线程是否成功启动
            if not self.monitor_thread.is_alive():
                raise Exception("监听线程启动失败")

        except Exception as e:
            self.hotkey_failed.emit(str(e))
            # 确保定时器继续运行
            self._ensure_timers_running()

    def _monitor_hotkey(self):
        """热键监听主循环"""
        while self.running:
            try:
                with self.lock:
                    if not self.hotkey_registered:
                        # 确保清理现有热键
                        keyboard.unhook_all()
                        time.sleep(0.05)
                        
                        try:
                            # 注册配置的热键
                            keyboard.add_hotkey(self.hotkey1, self._on_hotkey_triggered, suppress=True)
                            keyboard.add_hotkey(self.hotkey2, self._on_hotkey_triggered, suppress=True)
                            # 添加划词搜索热键
                            keyboard.add_hotkey(self.selection_hotkey, self._on_selection_triggered, suppress=True)
                            keyboard.add_hotkey(self.screenshot_hotkey, self._on_screenshot_triggered, suppress=True)
                            self.hotkey_registered = True
                            self.retry_count = 0
                            self.last_trigger_time = time.time()
                        except Exception as e:
                            self.hotkey_registered = False
                            raise e

                # 更频繁但更轻量的检查
                for _ in range(100):
                    if not self.running or not self.hotkey_registered:
                        break
                    time.sleep(0.001)
                    
            except Exception as e:
                self.hotkey_registered = False
                self.retry_count += 1
                
                if self.retry_count > self.max_retries:
                    self.hotkey_failed.emit(str(e))
                    self.retry_count = 0
                
                # 短暂等待后继续尝试
                time.sleep(0.1)
    
    def stop(self):
        """停止热键监听"""
        with self.lock:
            try:
                self.running = False
                self.hotkey_registered = False
                keyboard.unhook_all()
            except:
                pass
            finally:
                # 确保定时器停止
                self.check_timer.stop()
                self.thread_check_timer.stop()
                self.force_restart_timer.stop()
    
    def _on_hotkey_triggered(self):
        """热键触发时的处理函数"""
        try:
            self.last_trigger_time = time.time()  # 更新最后触发时间
            self.triggered.emit()
        except Exception as e:
            traceback.print_exc()
            
    def _on_selection_triggered(self):
        """划词搜索热键触发时的处理函数"""
        try:
            self.last_trigger_time = time.time()  # 更新最后触发时间
            self.selection_triggered.emit()
        except Exception as e:
            traceback.print_exc()
    
    def _on_screenshot_triggered(self):
        """截图热键触发时的处理函数"""
        try:
            self.last_trigger_time = time.time()
            self.screenshot_triggered.emit()
        except Exception as e:
            traceback.print_exc()
    
    def _clean_existing_hotkey(self):
        """清理已存在的热键"""
        try:
            keyboard.unhook_all()
            time.sleep(0.1)
        except Exception as e:
            pass
            #print(f"清理现有热键失败: {str(e)}")
    
    def _check_hotkey_status(self):
        """定期检查热键状态"""
        try:
            # 缩短重新注册时间
            if time.time() - self.last_trigger_time > 30:  # 改为30秒
                self.restart()
        except Exception as e:
            self.restart()  # 出现异常时也重启
    
    def _heartbeat(self):
        """心跳检测，确保主线程正常运行"""
        try:
            if not self.monitor_thread.is_alive():
                #print("监线程已死，重新启动")
                self.restart()
        except Exception as e:
            pass

    def load_hotkey_config(self):
        """从配置文件加载快捷键设置"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.hotkey1 = config.get('hotkey1', 'alt+q').lower()
                self.hotkey2 = config.get('hotkey2', 'alt+w').lower()
                self.selection_hotkey = config.get('selection_hotkey', 'alt+2').lower()
                self.screenshot_hotkey = config.get('screenshot_hotkey', 'alt+3').lower()
        except:
            pass  # 使用默认值
