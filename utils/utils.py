import re

def remove_markdown(text: str) -> str:
    """移除markdown格式"""
    # 移除代码块
    text = re.sub(r'```[\s\S]*?```', '', text)
    # 移除行内代码
    text = re.sub(r'`[^`]*`', '', text)
    # 移除标题
    text = re.sub(r'#{1,6}\s.*\n', '', text)
    # 移除粗体和斜体
    text = re.sub(r'\*\*.*?\*\*', '', text)
    text = re.sub(r'\*.*?\*', '', text)
    text = re.sub(r'__.*?__', '', text)
    text = re.sub(r'_.*?_', '', text)
    # 移除列表标记
    text = re.sub(r'^\s*[-*+]\s', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s', '', text, flags=re.MULTILINE)
    # 移除链接
    text = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', text)
    # 移除图片
    text = re.sub(r'!\[([^\]]*)\]\([^\)]*\)', '', text)
    # 移除引用
    text = re.sub(r'^\s*>\s', '', text, flags=re.MULTILINE)
    # 移除水平线
    text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)
    # 移除表格
    text = re.sub(r'\|.*\|', '', text)
    text = re.sub(r'^\s*[-:|\s]+$', '', text, flags=re.MULTILINE)
    # 清理多余的空行
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip() 