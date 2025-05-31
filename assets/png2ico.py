from PIL import Image
import os

def convert_png_to_ico(png_path, ico_path):
    """将PNG图像转换为ICO图标文件"""
    try:
        # 打开PNG图像
        img = Image.open(png_path)
        
        # 转换为RGBA模式(如果不是的话)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        # 调整图像大小为标准图标尺寸(如32x32)
        img = img.resize((128, 128), Image.Resampling.LANCZOS)
        
        # 保存为ICO文件
        img.save(ico_path, format='ICO')
        
        print(f"成功将 {png_path} 转换为 {ico_path}")
        return True
        
    except Exception as e:
        print(f"转换失败: {str(e)}")
        return False

if __name__ == '__main__':
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 设置输入和输出文件路径
    png_path = os.path.join(current_dir, 'app.png')
    ico_path = os.path.join(current_dir, 'logo.ico')
    
    # 执行转换
    convert_png_to_ico(png_path, ico_path)
