"""ComfyUI API 客户端

支持本地（WebSocket 实时监控）和云端（HTTP 轮询）双模式。
"""

import json
import uuid
import asyncio
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
from loguru import logger

from visionflow.config import get_settings


def is_cloud_url(url: str) -> bool:
    """判断是否是云端 ComfyUI（非 localhost/127.0.0.1）"""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    return not (
        host in ("localhost", "127.0.0.1", "0.0.0.0")
        or host.endswith(".local")
    )


class ComfyUIClient:
    """ComfyUI API 客户端"""

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.comfyui_url.rstrip("/")
        self.timeout = settings.comfyui_timeout
        self.client_id = str(uuid.uuid4())
        self._is_cloud = is_cloud_url(self.base_url)
        self._poll_interval = 2  # 轮询间隔（秒）

    # ─── 连接检测 ───

    async def health_check(self) -> bool:
        """检测 ComfyUI 是否在线"""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/system_stats", timeout=10)
                if resp.status_code == 200:
                    stats = resp.json()
                    vram = (
                        stats.get("devices", [{}])[0].get("vram_free", "N/A")
                        if "devices" in stats
                        else stats.get("system", {}).get("vram_free", "N/A")
                    )
                    logger.info(
                        f"ComfyUI 在线 [{ '☁️ 云端' if self._is_cloud else '💻 本地' }] | "
                        f"VRAM: {vram}"
                    )
                    return True
        except Exception as e:
            logger.error(f"ComfyUI 连接失败: {e}")
        return False

    # ─── 提交工作流 ───

    async def queue_prompt(self, workflow: dict) -> str:
        """提交工作流到 ComfyUI 执行队列"""
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
        """
        等待任务完成

        本地模式 → 用 WebSocket 实时监控
        云端模式 → 用 HTTP 轮询 get_queue / get_history
        """
        if self._is_cloud:
            return await self._wait_polling(prompt_id)
        else:
            return await self._wait_ws(prompt_id)

    async def _wait_ws(self, prompt_id: str) -> dict:
        """本地模式：WebSocket 实时监控"""
        import websockets

        ws_host = self.base_url.replace("https://", "").replace("http://", "")
        ws_url = f"ws://{ws_host}/ws?clientId={self.client_id}"
        logger.info(f"[WS] 开始监听: {prompt_id}")

        try:
            async with websockets.connect(ws_url, ping_interval=30) as ws:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=self.timeout)
                    data = json.loads(msg)

                    if data["type"] == "progress":
                        value = data["data"]["value"]
                        max_val = data["data"]["max"]
                        logger.info(f"[WS] 进度: {value}/{max_val}")

                    elif data["type"] == "executed":
                        if data["data"]["prompt_id"] == prompt_id:
                            logger.info(f"[WS] 任务完成: {prompt_id}")
                            return data["data"]

                    elif data["type"] == "execution_error":
                        if data["data"]["prompt_id"] == prompt_id:
                            error = data["data"]
                            logger.error(f"[WS] 执行出错: {error}")
                            raise RuntimeError(f"ComfyUI 执行错误: {error}")

        except asyncio.TimeoutError:
            raise TimeoutError(f"任务超时 ({self.timeout}s): {prompt_id}")

    async def _wait_polling(self, prompt_id: str) -> dict:
        """云端模式：HTTP 轮询等待（绕过 WebSocket）"""
        import time as _time
        logger.info(f"[轮询] 开始等待: {prompt_id} (间隔 {self._poll_interval}s)")
        deadline = _time.time() + self.timeout

        async with httpx.AsyncClient() as client:
            while _time.time() < deadline:
                await asyncio.sleep(self._poll_interval)

                # 只检查 history（简单可靠）
                try:
                    hist_resp = await client.get(
                        f"{self.base_url}/history/{prompt_id}", timeout=8
                    )
                    if hist_resp.status_code == 200:
                        hist_data = hist_resp.json()
                        if prompt_id in hist_data:
                            entry = hist_data[prompt_id]
                            status = entry.get("status", {})
                            completed = status.get("completed", False)
                            if completed:
                                logger.info(f"[轮询] 任务完成: {prompt_id}")
                                return entry
                except Exception:
                    pass

            # 超时后最后一次检查
            try:
                hist_resp = await client.get(
                    f"{self.base_url}/history/{prompt_id}", timeout=8
                )
                if hist_resp.status_code == 200:
                    hist_data = hist_resp.json()
                    if prompt_id in hist_data:
                        return hist_data[prompt_id]
            except Exception:
                pass

            raise TimeoutError(f"任务超时 ({self.timeout}s) | prompt_id: {prompt_id}")

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
        """获取生成的输出文件 URL（图片/视频/GIF 自动识别）"""
        history = await self.get_history(prompt_id)
        files = []
        if prompt_id not in history:
            return files
        outputs = history[prompt_id].get("outputs", {})

        # ComfyUI 输出可能放在 images / gifs / files 任一字段
        for node_id, node_output in outputs.items():
            for key in ["images", "gifs", "files"]:
                items = node_output.get(key, [])
                for item in items:
                    filename = item["filename"]
                    subfolder = item.get("subfolder", "")
                    img_type = item.get("type", "output")
                    url = (
                        f"{self.base_url}/view?"
                        f"filename={filename}&subfolder={subfolder}&type={img_type}"
                    )
                    files.append(url)

        return files

    # ─── 下载文件 ───

    async def download_image(self, url: str, save_path: str) -> str:
        """下载文件（图片/视频/GIF）到本地"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=60)
            resp.raise_for_status()
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(resp.content)
            logger.info(f"已下载: {save_path}")
            return save_path

    # ─── 上传图片 ───

    async def upload_image(self, image_path: str, subfolder: str = "") -> dict:
        """上传图片到 ComfyUI（用于 img2img / ControlNet / IP-Adapter 等）"""
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
                result = resp.json()
                logger.info(f"图片已上传: {result['name']}")
                return result

    # ─── 获取节点/模型信息 ───

    async def get_node_info(self) -> dict:
        """获取所有已安装的节点信息"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/object_info", timeout=15)
            resp.raise_for_status()
            return resp.json()

    async def get_available_models_by_type(self, node_type: str = "CheckpointLoaderSimple") -> list[str]:
        """获取某类节点可用的模型列表"""
        try:
            node_info = await self.get_node_info()
            node = node_info.get(node_type, {})
            inputs = node.get("input", {}).get("required", {})
            for key, val in inputs.items():
                if isinstance(val, list) and len(val) >= 1 and isinstance(val[0], list):
                    return val[0]
        except Exception as e:
            logger.warning(f"获取 {node_type} 模型列表失败: {e}")
        return []

    async def get_available_models(self) -> list[str]:
        return await self.get_available_models_by_type("CheckpointLoaderSimple")

    async def get_available_loras(self) -> list[str]:
        return await self.get_available_models_by_type("LoraLoader")
