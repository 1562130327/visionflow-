"""VisionFlow 主入口 — ComfyUI + Agent + 前端"""

import os
import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger
from contextlib import asynccontextmanager

from visionflow.config import get_settings
from visionflow.comfyui import ComfyUIClient, NodeRegistry
from visionflow.api.routes import router

settings = get_settings()
comfyui_client = ComfyUIClient()
node_registry = NodeRegistry(comfyui_client)


async def check_comfyui_http() -> bool:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.comfyui_url}/system_stats", timeout=8
            )
            return resp.status_code == 200
    except Exception:
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🎨 VisionFlow 启动中...")
    is_online = await check_comfyui_http()
    if is_online:
        logger.info("✅ ComfyUI 连接成功")
        await node_registry.scan()
    else:
        logger.warning("⚠️ ComfyUI 未连接")
    try:
        models = await comfyui_client.get_available_models()
        logger.info(f"可用模型: {len(models)} 个")
        for m in models[:5]:
            logger.info(f" - {m}")
    except Exception:
        pass
    logger.info("✅ VisionFlow 已就绪")
    yield
    logger.info("VisionFlow 关闭")


app = FastAPI(
    title="VisionFlow",
    description="AI 视觉创作智能体 — 基于 ComfyUI",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api/v1")

# ─── 前端静态文件 ───
frontend_dir = os.path.join(os.path.dirname(__file__), "../../frontend")
os.makedirs(frontend_dir, exist_ok=True)

# 静态文件目录（outputs 中的图片/音频可访问）
os.makedirs("outputs/audio", exist_ok=True)
app.mount("/static", StaticFiles(directory="."), name="static")


@app.get("/")
async def root_html():
    """返回前端页面"""
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "name": "VisionFlow",
        "version": "0.1.0",
        "status": "running",
        "comfyui": await check_comfyui_http(),
        "capabilities": node_registry.get_capabilities(),
    }


@app.get("/health")
async def health():
    comfyui_ok = await check_comfyui_http()
    return {"status": "ok" if comfyui_ok else "degraded", "comfyui": comfyui_ok}
