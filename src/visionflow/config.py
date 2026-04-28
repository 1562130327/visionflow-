import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # App
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"
    output_dir: str = "./outputs"

    # ComfyUI — 两种方式选一：
    # 1. COMFYUI_URL（完整 URL，会覆盖 HOST+PORT）
    # 2. COMFYUI_HOST + COMFYUI_PORT（分别指定）
    comfyui_url_override: str = ""       # 对应 .env 的 COMFYUI_URL
    comfyui_host: str = "127.0.0.1"
    comfyui_port: int = 8188
    comfyui_timeout: int = 300
    comfyui_output_dir: str = "./outputs"

    # LLM - DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # LLM (MiMo) - 用于 TTS
    mimo_api_key: str = ""
    mimo_base_url: str = "https://api.xiaomimimo.com/v1"
    mimo_model: str = "MiMo-V2.5-Pro"

    # Storage
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/visionflow"
    qdrant_url: str = "http://localhost:6333"

    model_config = {"env_file": os.path.join(os.path.dirname(__file__), "../../.env"), "env_file_encoding": "utf-8"}

    @property
    def comfyui_url(self) -> str:
        """返回 ComfyUI 完整 URL
        
        优先级：COMFYUI_URL > COMFYUI_HOST:COMFYUI_PORT
        """
        if self.comfyui_url_override:
            return self.comfyui_url_override.rstrip("/")
        return f"http://{self.comfyui_host}:{self.comfyui_port}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
