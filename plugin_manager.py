import os
import sys
import importlib
import inspect
from typing import List, Type
from plugins.base_plugin import BasePlugin

class PluginManager:
    def __init__(self):
        self.plugins = []
        self._load_plugins()
    
    def _get_plugins_dir(self):
        """获取插件目录的绝对路径"""
        if getattr(sys, 'frozen', False):
            # 如果是打包后的可执行文件
            base_path = sys._MEIPASS
        else:
            # 如果是开发环境
            base_path = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(base_path, 'plugins')
    
    def _load_plugins(self):
        """动态加载plugins目录下的所有插件"""
        plugins_dir = self._get_plugins_dir()
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)
            return
            
        # 确保plugins目录在Python路径中
        if plugins_dir not in sys.path:
            sys.path.insert(0, os.path.dirname(plugins_dir))
            
        for filename in os.listdir(plugins_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = f"plugins.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BasePlugin) and 
                            obj != BasePlugin):
                            self.plugins.append(obj())
                except Exception as e:
                    print(f"加载插件 {filename} 失败: {str(e)}")
    
    def get_plugins(self) -> List[BasePlugin]:
        """获取所有已加载的插件"""
        return self.plugins