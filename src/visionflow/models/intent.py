"""意图模型"""

from enum import Enum
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    COMPOSITE = "composite"


class StylePreset(str, Enum):
    REALISTIC = "realistic"
    ANIME = "anime"
    CYBERPUNK = "cyberpunk"
    PRODUCT = "product_photo"
    GHIBLI = "ghibli"
    MINIMALIST = "minimalist"
    OIL_PAINTING = "oil_painting"
    WATERCOLOR = "watercolor"
    CUSTOM = "custom"


class Subject(BaseModel):
    name: str = ""
    description: str = ""


class Intent(BaseModel):
    """用户意图的结构化表示"""
    description: str
    task_type: TaskType = TaskType.IMAGE
    style: StylePreset | None = None
    aspect_ratio: str = "1:1"
    quality_target: str = "standard"
    duration: float = 5.0
    subjects: list[Subject] = Field(default_factory=list)
    reference_images: list[str] = Field(default_factory=list)
    negative_prompt: str = ""
