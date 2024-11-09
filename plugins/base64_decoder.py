import base64
from .base_plugin import BasePlugin

class Base64DecoderPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "Base64解码"
    
    @property
    def description(self) -> str:
        return "将Base64编码的文本解码为普通文本"
    
    def process(self, text: str) -> str:
        try:
            decoded = base64.b64decode(text.encode()).decode()
            return f"解码结果:\n{decoded}"
        except:
            return "无法解码:输入的不是有效的Base64文本" 