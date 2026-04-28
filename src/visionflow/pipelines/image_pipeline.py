"""生图 Pipeline — 基于 ComfyUI"""

import random
from loguru import logger
from visionflow.models.task import Task, TaskStatus
from visionflow.comfyui import ComfyUIClient, WorkflowBuilder, ComfyUIMonitor


class ImagePipeline:
    """基于 ComfyUI 的图像生成流水线"""

    def __init__(self):
        self.client = ComfyUIClient()
        self.builder = WorkflowBuilder()
        self.monitor = ComfyUIMonitor(self.client)

    async def run(self, prompt: str, params: dict | None = None) -> Task:
        """完整的图像生成流程"""
        task = Task(
            id="task_" + str(random.randint(10000, 99999)),
            user_input=prompt,
            status=TaskStatus.PLANNING,
        )

        task.prompt_used = prompt
        logger.info(f"Prompt: {prompt[:80]}...")

        # 构建参数
        build_params = {
            "prompt": prompt,
            "negative_text": "low quality, blurry, deformed, watermark, text, signature",
            "width": params.get("width", 1024) if params else 1024,
            "height": params.get("height", 1024) if params else 1024,
            "steps": params.get("steps", 20) if params else 20,
            "cfg": params.get("cfg", 5) if params else 5,
            "filename_prefix": params.get("filename_prefix", "VisionFlow") if params else "VisionFlow",
        }

        task.status = TaskStatus.GENERATING
        workflow = self.builder.build("txt2img_flux", build_params)

        logger.info(f"提交 Flux 任务")
        result = await self.monitor.submit_and_wait(workflow, save_dir=f"./outputs/{task.id}")

        task.status = TaskStatus.COMPLETED if result.error is None else TaskStatus.FAILED
        task.output_urls = result.output_urls
        task.error = result.error

        if result.error:
            logger.error(f"图像生成失败: {result.error}")
        else:
            logger.info(f"图像生成完成: {len(result.output_urls)} 张图")
        return task
