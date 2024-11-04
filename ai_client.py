from openai import AsyncOpenAI
from typing import AsyncGenerator, Union
import httpx
import logging

class AIClient:
    def __init__(self, api_key: str, base_url: str = None, model: str = "yi-lightning", 
                 api_type: str = "OpenAI", proxy: str = None, proxy_enabled: bool = False):
        client_params = {"api_key": api_key}
        
        self.model = model
        self.api_type = api_type
        self.base_url = base_url or "https://api.openai.com/v1"
        self.proxy_enabled = proxy_enabled
        self.proxy = proxy
        
        # 设置代理
        if self.proxy_enabled and self.proxy:
            proxy_url = f"http://{self.proxy}"
            proxy_config = {
                "http://": proxy_url,
                "https://": proxy_url
            }
            self.http_client = httpx.AsyncClient(
                proxies=proxy_config,
                verify=False  # 如果有SSL证书问题可以禁用验证
            )
            client_params["http_client"] = self.http_client
            print(f"代理已启用: {proxy_url}")
            print(f"代理配置: {proxy_config}")  # 直接打印代理配置字典
        else:
            self.http_client = None
            print(f"代理未启用 (enabled={proxy_enabled}, proxy={proxy})")
            
        if base_url:
            client_params["base_url"] = base_url
            
        print("\n初始化配置:")
        print(f"API类型: {self.api_type}")
        print(f"模型: {self.model}")
        print(f"API地址: {self.base_url}")
        print(f"代理状态: {'启用' if self.proxy_enabled else '未启用'}")
        print(f"代理设置: {self.proxy if self.proxy_enabled else '无'}")
        print(f"客户端参数: {client_params}\n")
            
        self.client = AsyncOpenAI(**client_params)
        
    async def get_response_stream(self, prompt: str, stream: bool = True) -> AsyncGenerator[str, None]:
        """获取AI响应，支持流式和非流式模式"""
        try:
            messages = [{
                "role": "system",
                "content": "请直接回答问题，不要使用markdown格式。"
            }, {
                "role": "user",
                "content": prompt
            }]
            
            # 打印实际调用参数
            call_params = {
                "model": self.model,
                "messages": messages,
                "stream": stream  # 使用传入的stream参数
            }
            
            if self.api_type == "Azure":
                call_params["api_version"] = "2024-02-15-preview"
            
            print("\n实际API调用参数:")
            print(f"URL: {self.client.base_url}")
            print(f"代理状态: {'启用' if self.proxy_enabled else '未启用'}")
            if self.proxy_enabled and self.proxy:
                print(f"代理设置: http://{self.proxy}")
            print(f"参数: {call_params}\n")
            
            # 根据不同的API类型设置不同的参数
            if self.api_type == "Azure":
                response = await self.client.chat.completions.create(**call_params)
            else:  # OpenAI 和其他API
                response = await self.client.chat.completions.create(**call_params)
            
            if stream:
                # 流式模式
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                print("流式模式结束")
            else:
                # 非流式模式，直接返回完整响应
                # 注意：非流式模式下，response不是异步迭代器，而是直接的响应对象
                complete_response = response.choices[0].message.content
                yield complete_response
                print("非流式模式结束")
                    
        except Exception as e:
            error_msg = f"API调用错误: {str(e)}"
            print(error_msg)  # 在控制台打印错误
            yield error_msg

    async def get_response(self, prompt: str) -> str:
        """获取非流式响应的辅助方法"""
        response = ""
        async for chunk in self.get_response_stream(prompt, stream=False):
            response += chunk
        return response