"""生视频 Pipeline — 基于 ComfyUI + Wan2.2-14B"""

import random
from loguru import logger
from visionflow.models.task import Task, TaskStatus
from visionflow.comfyui import ComfyUIClient, WorkflowBuilder, ComfyUIMonitor


class VideoPipeline:
    """基于 ComfyUI Wan2.2-14B 的视频生成流水线"""

    def __init__(self):
        self.client = ComfyUIClient()
        self.builder = WorkflowBuilder()
        self.monitor = ComfyUIMonitor(self.client)

    async def run(
        self,
        prompt: str,
        image_input: str,  # ComfyUI 上已上传的图片文件名
        params: dict | None = None,
    ) -> Task:
        """完整的视频生成流程"""
        task = Task(
            id="vid_" + str(random.randint(10000, 99999)),
            user_input=prompt,
            status=TaskStatus.PLANNING,
        )

        task.prompt_used = prompt
        logger.info(f"视频 Prompt: {prompt[:60]}... | 输入图: {image_input}")

        build_params = {
            "prompt": prompt,
            "negative_text": "low quality, blurry, deformed, watermark, text",
            "image_input": image_input,
            "width": params.get("width", 640) if params else 640,
            "height": params.get("height", 640) if params else 640,
            "length": params.get("length", 81) if params else 81,
            "filename_prefix": params.get("filename_prefix", "VisionFlowVideo") if params else "VisionFlowVideo",
        }

        task.status = TaskStatus.GENERATING
        workflow = self.builder.build("img2video_wan", build_params)

        logger.info("提交 Wan2.2 视频任务")
        result = await self.monitor.submit_and_wait(workflow, save_dir=f"./outputs/{task.id}")

        task.status = TaskStatus.COMPLETED if result.error is None else TaskStatus.FAILED
        task.output_urls = result.output_urls
        task.error = result.error

        if result.error:
            logger.error(f"视频生成失败: {result.error}")
        else:
            logger.info(f"视频生成完成: {len(result.output_urls)} 个文件")
        return task

    async def run_with_upload(
        self,
        prompt: str,
        local_image_path: str,
        params: dict | None = None,
    ) -> Task:
        """上传本地图片 → 生成视频"""
        upload_result = await self.client.upload_image(local_image_path)
        image_filename = upload_result["name"]
        return await self.run(prompt, image_filename, params)
