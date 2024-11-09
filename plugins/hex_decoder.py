from .base_plugin import BasePlugin

class HexDecoder(BasePlugin):
    @property
    def name(self) -> str:
        return "Hex解码器"
    
    @property
    def description(self) -> str:
        return "将16进制字符串转换为普通文本"
    
    def process(self, text: str) -> str:
        try:
            # 移除可能存在的空格和0x前缀
            text = text.replace(" ", "").replace("0x", "")
            
            # 检查是否是有效的16进制字符串
            if not all(c in '0123456789ABCDEFabcdef' for c in text):
                return "错误: 输入包含非16进制字符"
            
            if len(text) % 2 != 0:
                return "错误: 16进制字符串长度必须是2的倍数"
            
            # 将16进制字符串转换为字节，然后解码为字符串
            bytes_data = bytes.fromhex(text)
            return bytes_data.decode('utf-8', errors='replace')
            
        except ValueError as e:
            return f"解码错误: {str(e)}"
        except Exception as e:
            return f"发生错误: {str(e)}" 