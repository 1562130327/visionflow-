"""API 路由 — ComfyUI 出图/视频 + Agent 创作 + TTS"""

import json
import os
import tempfile
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from visionflow.pipelines.image_pipeline import ImagePipeline
from visionflow.pipelines.video_pipeline import VideoPipeline
from visionflow.agents.story_agent import StoryAgent
from visionflow.agents.tts_agent import TTSAgent

router = APIRouter()

story_agent = StoryAgent()
tts_agent = TTSAgent()


# ══════════════════════════════════════════
# ComfyUI 出图
# ══════════════════════════════════════════

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
    image_url: str = ""     # ComfyUI 输出图 URL（云端）
    image_path: str = ""     # 本地图片路径
    width: int = 640
    height: int = 640
    length: int = 81


@router.post("/video-from-image")
async def video_from_image(req: VideoFromImageRequest):
    """用图片生成视频"""
    try:
        # 如果有 image_url，下载到临时文件
        local_path = req.image_path
        if not local_path and req.image_url:
            import httpx
            from io import BytesIO
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            async with httpx.AsyncClient() as client:
                resp = await client.get(req.image_url, timeout=30)
                tmp.write(resp.content)
                tmp.close()
                local_path = tmp.name

        if not local_path:
            raise HTTPException(status_code=400, detail="需要 image_url 或 image_path")

        pipeline = VideoPipeline()
        task = await pipeline.run_with_upload(
            prompt=req.prompt,
            local_image_path=local_path,
            params={"width": req.width, "height": req.height, "length": req.length},
        )
        # 清理临时文件
        if not req.image_path and local_path and os.path.exists(local_path):
            try: os.unlink(local_path)
            except: pass

        return {
            "task_id": task.id,
            "status": task.status.value,
            "output_urls": task.output_urls,
            "error": task.error,
        }
    except Exception as e:
        logger.error(f"视频生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════
# Agent 创作 API
# ══════════════════════════════════════════

class UnderstandRequest(BaseModel):
    text: str


@router.post("/agent/understand")
async def understand_theme(req: UnderstandRequest):
    """Step 1: 理解用户想法 → 生成主题/角色/大纲"""
    try:
        data = story_agent.understand_theme(req.text)
        return data
    except Exception as e:
        logger.error(f"主题理解失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ScenesRequest(BaseModel):
    theme: dict
    count: int = 6


@router.post("/agent/generate-scenes")
async def generate_scenes(req: ScenesRequest):
    """Step 2: 根据主题生成分镜"""
    try:
        scenes = story_agent.generate_scenes(req.theme, req.count)
        return {"scenes": [s.to_dict() for s in scenes]}
    except Exception as e:
        logger.error(f"分镜生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════
# TTS 配音
# ══════════════════════════════════════════

class TTSRequest(BaseModel):
    text: str
    mood: str = "平静"
    voice: str = "冰糖"


@router.post("/tts")
async def text_to_speech(req: TTSRequest):
    """文本转语音"""
    try:
        audio_bytes = tts_agent.synthesize(req.text, req.mood, req.voice)

        # 保存到临时文件并返回 URL
        os.makedirs("outputs/audio", exist_ok=True)
        filename = f"tts_{hash(req.text) % 100000}.wav"
        filepath = f"outputs/audio/{filename}"
        with open(filepath, "wb") as f:
            f.write(audio_bytes)

        return {"audio_url": f"/static/outputs/audio/{filename}"}
    except Exception as e:
        logger.error(f"TTS 失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
