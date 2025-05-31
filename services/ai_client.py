from openai import AsyncOpenAI
from typing import AsyncGenerator, Union
import httpx
import logging
import traceback

class AIClient:
    def __init__(self, api_key: str, base_url: str = None, model: str = "yi-lightning", 
                 api_type: str = "OpenAI", proxy: str = None, proxy_enabled: bool = False,
                 temperature: float = 0.7, max_tokens: int = 2000):
        client_params = {"api_key": api_key}
        
        self.model = model
        self.api_type = api_type
        self.base_url = base_url or "https://api.openai.com/v1"
        self.proxy_enabled = proxy_enabled
        self.proxy = proxy
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        print(f"温度: {self.temperature}")
        print(f"最大令牌数: {self.max_tokens}")
        
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
        
    async def get_response_stream(self, prompt: str, stream: bool = True, messages: list = None,
                                temperature: float = None, max_tokens: int = None) -> AsyncGenerator[str, None]:
        """获取AI响应，支持流式和非流式模式"""
        try:
            # 使用传入的参数或默认值
            current_temperature = temperature if temperature is not None else self.temperature
            current_max_tokens = max_tokens if max_tokens is not None else self.max_tokens
            
            if messages is None:
                messages = [{
                    "role": "system",
                    "content": "你是一名AI助理，请直接回答问题"
                }, {
                    "role": "user",
                    "content": prompt
                }]
            
            call_params = {
                "model": self.model,
                "messages": messages,
                "stream": stream,
                "temperature": current_temperature,
                "max_tokens": current_max_tokens
            }
            
            if self.api_type == "Azure":
                call_params["api_version"] = "2024-02-15-preview"
            
            print("\n实际API调用参数:")
            print(f"URL: {self.client.base_url}")
            print(f"代理状态: {'启用' if self.proxy_enabled else '未启用'}")
            if self.proxy_enabled and self.proxy:
                print(f"代理设置: http://{self.proxy}")
            print(f"温度: {current_temperature}")
            print(f"最大令牌数: {current_max_tokens}")
            print(f"参数: {call_params}\n")
            
            # 根据不同的API类型设置不同的参数
            if self.api_type == "Azure":
                response = await self.client.chat.completions.create(**call_params)
            else:  # OpenAI 和其他API
                response = await self.client.chat.completions.create(**call_params)
            
            if stream:
                # 流式模式
                async for chunk in response:
                    # if (hasattr(chunk, 'choices') and len(chunk.choices) > 0):
                    #     print(f"响应块的choices: {chunk.choices}")  # 添加调试输出
                    if (hasattr(chunk, 'choices') and 
                        len(chunk.choices) > 0 and 
                        chunk.choices[0].delta and 
                        hasattr(chunk.choices[0].delta, 'content') and 
                        chunk.choices[0].delta.content):
                        yield chunk.choices[0].delta.content
                print("流式模式结束")
            else:
                # 非流式模式，直接返回完整响应
                if hasattr(response, 'choices') and len(response.choices) > 0:
                    complete_response = response.choices[0].message.content
                    yield complete_response
                else:
                    error_msg = "API响应格式错误：未找到有效的响应内容"
                    print(error_msg)
                    yield error_msg
                print("非流式模式结束")
                    
        except Exception as e:
            error_msg = f"API调用错误: {str(e)}"
            print(error_msg)  # 在控制台打印错误
            print("详细错误信息:")
            traceback.print_exc()  # 打印详细的堆栈跟踪
            yield error_msg

    async def get_response(self, prompt: str, messages: list = None, temperature: float = None, max_tokens: int = None) -> str:
        """获取非流式响应的辅助方法"""
        response = ""
        async for chunk in self.get_response_stream(
            prompt, 
            stream=False, 
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            response += chunk
        return response