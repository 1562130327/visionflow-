"""API 路由 — 直接调用 ComfyUI 出图/视频"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from visionflow.pipelines.image_pipeline import ImagePipeline
from visionflow.pipelines.video_pipeline import VideoPipeline

router = APIRouter()


class GenerateRequest(BaseModel):
    prompt: str
    task_type: str = "image"  # image | video
    width: int = 1024
    height: int = 1024
    steps: int = 20
    cfg: float = 5.0


@router.post("/generate")
async def generate(req: GenerateRequest):
    """提交生成任务到 ComfyUI"""
    try:
        params = {
            "width": req.width,
            "height": req.height,
            "steps": req.steps,
            "cfg": req.cfg,
        }

        if req.task_type == "video":
            pipeline = VideoPipeline()
            # 视频需要先上传图片（暂不支持直接调用，需要图片路径）
            task = await pipeline.run(req.prompt, "", params)
        else:
            pipeline = ImagePipeline()
            task = await pipeline.run(req.prompt, params)

        return {
            "task_id": task.id,
            "status": task.status.value,
            "output_urls": task.output_urls,
            "prompt_used": task.prompt_used,
            "error": task.error,
        }
    except Exception as e:
        logger.error(f"生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class VideoFromImageRequest(BaseModel):
    prompt: str
    image_path: str  # 本地图片路径
    width: int = 640
    height: int = 640
    length: int = 81  # 帧数


@router.post("/video-from-image")
async def video_from_image(req: VideoFromImageRequest):
    """上传本地图片并生成视频"""
    try:
        pipeline = VideoPipeline()
        task = await pipeline.run_with_upload(
            prompt=req.prompt,
            local_image_path=req.image_path,
            params={"width": req.width, "height": req.height, "length": req.length},
        )
        return {
            "task_id": task.id,
            "status": task.status.value,
            "output_urls": task.output_urls,
            "error": task.error,
        }
    except Exception as e:
        logger.error(f"视频生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
