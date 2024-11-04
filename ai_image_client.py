import base64
import aiohttp
import json

class AIImageClient:
    def __init__(self, api_key, base_url=None, model="yi-vision", proxy=None, proxy_enabled=False):
        self.api_key = api_key
        self.base_url = base_url or "https://api.lingyiwanwu.com/v1"
        self.model = model
        self.proxy = proxy
        self.proxy_enabled = proxy_enabled

    async def get_response(self, prompt: str, image_data: bytes) -> str:
        """获取单次响应"""
        try:
            # 将图片转换为base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 构建请求数据
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 2000
            }
            
            # 设置代理
            proxy = f"http://{self.proxy}" if self.proxy_enabled and self.proxy else None
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    proxy=proxy
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API请求失败: {error_text}")
                    
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                    
        except Exception as e:
            raise Exception(f"获取AI响应失败: {str(e)}")

    async def get_response_stream(self, prompt: str, image_data: bytes):
        """获取流式响应"""
        try:
            # 将图片转换为base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 构建请求数据
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 2000,
                "stream": True
            }
            
            # 设置代理
            proxy = f"http://{self.proxy}" if self.proxy_enabled and self.proxy else None
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    proxy=proxy
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API请求失败: {error_text}")
                    
                    # 处理流式响应
                    async for line in response.content:
                        if line:
                            try:
                                line = line.decode('utf-8').strip()
                                if line.startswith('data: ') and line != 'data: [DONE]':
                                    json_str = line[6:]  # 移除 "data: " 前缀
                                    data = json.loads(json_str)
                                    if len(data['choices']) > 0:
                                        delta = data['choices'][0]['delta']
                                        if 'content' in delta:
                                            yield delta['content']
                            except Exception as e:
                                print(f"处理响应流出错: {str(e)}")
                                continue
                    
        except Exception as e:
            raise Exception(f"获取AI响应失败: {str(e)}") 