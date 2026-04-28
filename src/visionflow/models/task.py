"""任务模型"""

from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class TaskStatus(str, Enum):
    PLANNING = "planning"
    GENERATING = "generating"
    EVALUATING = "evaluating"
    REFINING = "refining"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(BaseModel):
    id: str
    user_input: str
    status: TaskStatus = TaskStatus.PLANNING
    prompt_used: str = ""
    candidates: list[dict] = Field(default_factory=list)
    selected_index: int = -1
    output_urls: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    error: str | None = None
