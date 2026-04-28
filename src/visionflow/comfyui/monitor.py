"""生成任务监控器"""

import time
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from visionflow.comfyui.client import ComfyUIClient


class TaskState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class GenerationTask:
    prompt_id: str
    state: TaskState = TaskState.QUEUED
    progress: float = 0.0
    output_urls: list[str] = field(default_factory=list)
    error: str | None = None


class ComfyUIMonitor:
    """ComfyUI 任务监控器"""

    def __init__(self, client: ComfyUIClient):
        self.client = client
        self._tasks: dict[str, GenerationTask] = {}

    async def submit_and_wait(
        self,
        workflow: dict,
        save_dir: str | None = None,
    ) -> GenerationTask:
        """提交工作流并等待完成"""
        prompt_id = await self.client.queue_prompt(workflow)
        task = GenerationTask(prompt_id=prompt_id, state=TaskState.RUNNING)
        self._tasks[prompt_id] = task
        try:
            await self.client.wait_for_completion(prompt_id)
            task.state = TaskState.COMPLETED
            file_urls = await self.client.get_output_images(prompt_id)
            task.output_urls = file_urls
            if save_dir:
                from pathlib import Path
                for i, url in enumerate(file_urls):
                    # 根据 URL 后缀决定保存格式
                    ext = ".png"
                    if "gif" in url or ".gif" in url:
                        ext = ".gif"
                    elif "mp4" in url or ".mp4" in url:
                        ext = ".mp4"
                    elif "webp" in url or ".webp" in url:
                        ext = ".webp"
                    import uuid as _uuid
                    save_path = f"{save_dir}/{prompt_id}_{i}{ext}"
                    await self.client.download_image(url, save_path)
            logger.info(f"任务完成: {prompt_id} | 输出: {len(file_urls)} 个文件")
        except Exception as e:
            task.state = TaskState.FAILED
            task.error = str(e)
            logger.error(f"任务失败: {prompt_id} | {e}")
        return task

    def get_task(self, prompt_id: str) -> GenerationTask | None:
        return self._tasks.get(prompt_id)
