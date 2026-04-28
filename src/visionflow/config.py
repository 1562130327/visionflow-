from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # App
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"
    output_dir: str = "./outputs"

    # ComfyUI
    comfyui_host: str = "127.0.0.1"
    comfyui_port: int = 8188
    comfyui_timeout: int = 300
    comfyui_output_dir: str = "./outputs"

    # LLM
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"

    # Storage
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/visionflow"
    qdrant_url: str = "http://localhost:6333"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def comfyui_url(self) -> str:
        return f"http://{self.comfyui_host}:{self.comfyui_port}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
