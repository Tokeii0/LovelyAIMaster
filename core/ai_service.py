from services.ai_client import AIClient
from services.ai_image_client import AIImageClient

class AIService(AIClient):
    @classmethod
    def from_config(cls, cfg: dict) -> "AIService":
        return cls(
            api_key=cfg.get("api_key", ""),
            base_url=cfg.get("base_url"),
            model=cfg.get("model", "gpt-4o"),
            api_type=cfg.get("api_type", "OpenAI"),
            proxy=cfg.get("proxy", "127.0.0.1:1090"),
            proxy_enabled=cfg.get("proxy_enabled", False),
        )

class AIImageService(AIImageClient):
    @classmethod
    def from_config(cls, cfg: dict) -> "AIImageService":
        return cls(
            api_key=cfg.get("image_api_key", ""),
            base_url=cfg.get("image_base_url"),
            model=cfg.get("image_model", "yi-vision"),
            proxy=cfg.get("image_proxy", "127.0.0.1:1090"),
            proxy_enabled=cfg.get("image_proxy_enabled", False),
        )
