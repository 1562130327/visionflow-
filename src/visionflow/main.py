"""VisionFlow 主入口"""

from fastapi import FastAPI
from loguru import logger
from contextlib import asynccontextmanager

from visionflow.config import get_settings
from visionflow.comfyui import ComfyUIClient, NodeRegistry
from visionflow.api.routes import router

settings = get_settings()
comfyui_client = ComfyUIClient()
node_registry = NodeRegistry(comfyui_client)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🎨 VisionFlow 启动中...")
    is_online = await comfyui_client.health_check()
    if is_online:
        logger.info("✅ ComfyUI 连接成功")
        await node_registry.scan()
    else:
        logger.warning("⚠️ ComfyUI 未连接，请确认 ComfyUI 已启动")
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


@app.get("/")
async def root():
    return {
        "name": "VisionFlow",
        "version": "0.1.0",
        "status": "running",
        "comfyui": await comfyui_client.health_check(),
        "capabilities": node_registry.get_capabilities(),
    }


@app.get("/health")
async def health():
    comfyui_ok = await comfyui_client.health_check()
    return {
        "status": "ok" if comfyui_ok else "degraded",
        "comfyui": comfyui_ok,
    }
