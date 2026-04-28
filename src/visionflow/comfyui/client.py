"""ComfyUI API 客户端"""

import json
import uuid
import asyncio
from pathlib import Path

import httpx
import websockets
from loguru import logger

from visionflow.config import get_settings


class ComfyUIClient:
    """ComfyUI API 客户端"""

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.comfyui_url
        self.timeout = settings.comfyui_timeout
        self.client_id = str(uuid.uuid4())

    # ─── 连接检测 ───

    async def health_check(self) -> bool:
        """检测 ComfyUI 是否在线"""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/system_stats", timeout=5)
                if resp.status_code == 200:
                    stats = resp.json()
                    logger.info(
                        f"ComfyUI 在线 | VRAM: "
                        f"{stats.get('devices', [{}])[0].get('vram_free', 'N/A')}"
                    )
                    return True
        except Exception as e:
            logger.error(f"ComfyUI 连接失败: {e}")
        return False

    # ─── 提交工作流 ───

    async def queue_prompt(self, workflow: dict) -> str:
        """
        提交工作流到 ComfyUI 执行队列

        Args:
            workflow: ComfyUI API 格式的工作流 JSON

        Returns:
            prompt_id: 任务 ID
        """
        payload = {
            "prompt": workflow,
            "client_id": self.client_id,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/prompt",
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()
            prompt_id = result["prompt_id"]
            logger.info(f"工作流已提交 | prompt_id: {prompt_id}")
            return prompt_id

    # ─── 监控进度 ───

    async def wait_for_completion(self, prompt_id: str) -> dict:
        """通过 WebSocket 监听任务进度"""
        ws_url = f"ws://{self.base_url_host}/ws?clientId={self.client_id}"
        logger.info(f"等待任务完成: {prompt_id}")

        try:
            async with websockets.connect(ws_url) as ws:
                while True:
                    msg = await asyncio.wait_for(
                        ws.recv(), timeout=self.timeout
                    )
                    data = json.loads(msg)

                    if data["type"] == "progress":
                        value = data["data"]["value"]
                        max_val = data["data"]["max"]
                        logger.info(f"进度: {value}/{max_val}")

                    elif data["type"] == "executed":
                        if data["data"]["prompt_id"] == prompt_id:
                            logger.info("任务执行完成")
                            return data["data"]

                    elif data["type"] == "execution_error":
                        if data["data"]["prompt_id"] == prompt_id:
                            error = data["data"]
                            logger.error(f"执行出错: {error}")
                            raise RuntimeError(f"ComfyUI 执行错误: {error}")

        except asyncio.TimeoutError:
            raise TimeoutError(f"任务超时 ({self.timeout}s): {prompt_id}")

    # ─── 获取结果 ───

    async def get_history(self, prompt_id: str) -> dict:
        """获取任务历史结果"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/history/{prompt_id}",
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_output_images(self, prompt_id: str) -> list[str]:
        """获取生成的图片 URL"""
        history = await self.get_history(prompt_id)
        images = []
        if prompt_id not in history:
            return images
        outputs = history[prompt_id].get("outputs", {})
        for node_id, node_output in outputs.items():
            for key in ["images", "gifs", "files"]:
                items = node_output.get(key, [])
                for item in items:
                    filename = item["filename"]
                    subfolder = item.get("subfolder", "")
                    img_type = item.get("type", "output")
                    url = f"{self.base_url}/view?filename={filename}&subfolder={subfolder}&type={img_type}"
                    images.append(url)
        return images

    # ─── 下载图片 ───

    async def download_image(self, url: str, save_path: str) -> str:
        """下载图片到本地"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=30)
            resp.raise_for_status()
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(resp.content)
            return save_path

    # ─── 上传图片 ───

    async def upload_image(self, image_path: str, subfolder: str = "") -> dict:
        """上传图片到 ComfyUI"""
        async with httpx.AsyncClient() as client:
            with open(image_path, "rb") as f:
                files = {"image": (Path(image_path).name, f, "image/png")}
                data = {"subfolder": subfolder, "overwrite": "true"}
                resp = await client.post(
                    f"{self.base_url}/upload/image",
                    files=files,
                    data=data,
                    timeout=30,
                )
                resp.raise_for_status()
                return resp.json()

    # ─── 获取节点/模型信息 ───

    async def get_node_info(self) -> dict:
        """获取所有已安装的节点信息"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/object_info", timeout=10)
            resp.raise_for_status()
            return resp.json()

    async def get_available_models(self) -> list[str]:
        """获取所有可用的 checkpoint 模型"""
        node_info = await self.get_node_info()
        ckpt_node = node_info.get("CheckpointLoaderSimple", {})
        inputs = ckpt_node.get("input", {}).get("required", {})
        models = inputs.get("ckpt_name", [[]])[0]
        return models

    async def get_available_loras(self) -> list[str]:
        """获取所有可用的 LoRA 模型"""
        node_info = await self.get_node_info()
        lora_node = node_info.get("LoraLoader", {})
        inputs = lora_node.get("input", {}).get("required", {})
        loras = inputs.get("lora_name", [[]])[0]
        return loras

    @property
    def base_url_host(self) -> str:
        return f"{get_settings().comfyui_host}:{get_settings().comfyui_port}"
