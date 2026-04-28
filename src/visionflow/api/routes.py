"""API 路由"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from visionflow.pipelines.image_pipeline import ImagePipeline
from visionflow.pipelines.video_pipeline import VideoPipeline
from visionflow.models.intent import Intent, TaskType

router = APIRouter()


class GenerateRequest(BaseModel):
    prompt: str
    task_type: str = "image"
    style: str = "custom"
    aspect_ratio: str = "1:1"
    quality: str = "standard"
    num_candidates: int = 4


@router.post("/generate")
async def generate(req: GenerateRequest):
    """提交生成任务"""
    try:
        intent = Intent(
            description=req.prompt,
            task_type=TaskType(req.task_type),
            aspect_ratio=req.aspect_ratio,
            quality_target=req.quality,
        )
        if req.task_type == "video":
            pipeline = VideoPipeline()
        else:
            pipeline = ImagePipeline()

        task = await pipeline.run(intent, num_candidates=req.num_candidates)
        return {
            "task_id": task.id,
            "status": task.status.value,
            "output_urls": task.output_urls,
            "prompt_used": task.prompt_used,
        }
    except Exception as e:
        logger.error(f"生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    return {"status": "ok"}
