import json
import os

class ConfigManager:
    def __init__(self):
        self.default_config = {
            'api_key': '',
            'base_url': 'https://api.openai.com/v1',
            'model': 'gpt-4-mini',
            'api_type': 'OpenAI',
            'proxy_enabled': False,
            'proxy': '127.0.0.1:1090'
        }
        self.config = self.load_config()
    
    def load_config(self):
        try:
            if os.path.exists('config/config.json'):
                with open('config/config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'proxy_enabled' in config:
                        config['proxy_enabled'] = bool(config['proxy_enabled'])
                    return config
            return self.create_default_config()
        except Exception as e:
            return self.create_default_config()
            
    def create_default_config(self):
        try:
            with open('config/config.json', 'w', encoding='utf-8') as f:
                json.dump(self.default_config, f, indent=4, ensure_ascii=False)
            return self.default_config.copy()
        except Exception:
            return self.default_config.copy() 