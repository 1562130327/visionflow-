"""VisionFlow 主入口"""

import httpx
from fastapi import FastAPI
from loguru import logger
from contextlib import asynccontextmanager

from visionflow.config import get_settings
from visionflow.comfyui import ComfyUIClient, NodeRegistry
from visionflow.api.routes import router

settings = get_settings()
comfyui_client = ComfyUIClient()
node_registry = NodeRegistry(comfyui_client)


async def check_comfyui_http() -> bool:
    """独立检测 ComfyUI，不依赖可能过期的 client 实例"""
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
    """应用生命周期管理"""
    logger.info("🎨 VisionFlow 启动中...")
    is_online = await check_comfyui_http()
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
        "comfyui": await check_comfyui_http(),
        "capabilities": node_registry.get_capabilities(),
    }


@app.get("/health")
async def health():
    comfyui_ok = await check_comfyui_http()
    return {
        "status": "ok" if comfyui_ok else "degraded",
        "comfyui": comfyui_ok,
    }
