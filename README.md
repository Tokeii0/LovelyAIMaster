<!-- markdownlint-disable MD033 MD041 -->
<p align="center">
  <a href="https://ctf.mzy0.com"><img src="https://github.com/Tokeii0/LovelyAImamaster/blob/main/icons/app.png" width="250" height="250" alt="lovelyAImamaster"></a>
</p>
<div align="center">

# lovelyAImamaster

<!-- prettier-ignore-start -->
<!-- markdownlint-disable-next-line MD036 -->
_✨ 纯AI开发的AI工具，可以在windows任何地方调用AI进行输入 ✨_
<!-- prettier-ignore-end -->
<a href="https://jq.qq.com/?_wv=1027&k=DzOtbzU4"><img src="https://img.shields.io/badge/QQ%E7%BE%A4-856729462-orange?style=flat-square" alt="QQGroup"></a>
  <a href="http://ctf.dog"><img src="https://img.shields.io/badge/CTF%E5%AF%BC%E8%88%AA%E7%AB%99-ctf.dog-5492ff?style=flat-square" alt="ctfnav"></a>
  <a href=".."><img src="https://img.shields.io/badge/Python%20-%203.13.0-def1f2?style=flat-square" alt="python"></a>
</div>

## 💰请我吃份黄焖鸡
![QQ20241106-082434](https://github.com/user-attachments/assets/0e916223-996c-4e69-9789-400218125fcb)



## 😆使用

自己pip一下缺少的库,然后使用python main.py就可以啦

运行之后在托盘找到图标，右键设置里面配置baseurl apikey 以及对应的模型名称 代理配置

推荐几家：

**零一万物**:https://platform.lingyiwanwu.com/details

**deepbricks**:https://deepbricks.ai/

**智谱**:https://open.bigmodel.cn/

### 默认情况下 
**ALT+1 任意输入框调起AI写作**

**ALT+2 划词后菜单选择可询问划词内容**

**ALT+3 进行截图，并调起AI提问，需单独配置API**

**ALT+4 进行多轮对话**

## 🐲本地大模型对接
 - 下载 https://lmstudio.ai/
 - 下载模型(无法连接就开启TUN模式)
 - 按照下面如图配置
  
  ![image](https://github.com/user-attachments/assets/10bdee64-0e6b-4742-bd1d-3233ef3f17af)
 - 软件设置如图配置，主要的就是apikey随便填，baseurl填你lmstudio中设置的，模型为你加载的
   ![image](https://github.com/user-attachments/assets/01bb1593-89d7-44d1-9ba4-5226ed12363e)

就OJBK了

笔记本4060、4070推荐**llama-3-8b**模型

## 📎划词插件开发

 - 可以通过源码进行开发
 - 或者在软件目录下 \_internal\plugins查看插件的代码详情
比如下面的base64解码

```python
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
```

## 🐔使用截图
![image](https://github.com/user-attachments/assets/6633a4a1-71fd-410c-b811-868dead0881a)

![image](https://github.com/user-attachments/assets/92695864-0d87-4d57-a33c-46a68cd4680a)

![image](https://github.com/user-attachments/assets/82787dea-a07d-49f8-a2b8-c907550a2948)

![image](https://github.com/user-attachments/assets/b01e70c5-9ea6-44cf-a3f7-9d58ecfbb387)



## 🔩其他
使用过程中如果无法正常调用流模式，就取消流模式的勾勾，比如wps，等等




