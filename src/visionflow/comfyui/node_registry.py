"""ComfyUI 节点能力注册"""

from loguru import logger
from visionflow.comfyui.client import ComfyUIClient


CAPABILITY_MAP = {
    "txt2img": ["KSampler", "CheckpointLoaderSimple"],
    "img2img": ["KSampler", "LoadImage"],
    "inpaint": ["VAEEncodeForInpaint", "KSampler"],
    "controlnet": ["ControlNetLoader", "ControlNetApplyAdvanced"],
    "ipadapter": ["IPAdapterApply", "IPAdapterModelLoader"],
    "lora": ["LoraLoader"],
    "upscale": ["UpscaleModelLoader", "ImageUpscaleWithModel"],
    "face_restore": ["FaceRestoreModelLoader", "FaceRestoreCF"],
    "remove_bg": ["RemoveBackground"],
    "animatediff": ["AnimateDiffLoaderWithContext"],
    "svd": ["SVD_img2vid_Conditioning"],
    "cogvideo": ["CogVideoTextEncode"],
    "save_image": ["SaveImage", "PreviewImage"],
}


class NodeRegistry:
    """ComfyUI 节点能力注册"""

    def __init__(self, client: ComfyUIClient):
        self.client = client
        self._available_nodes: set[str] = set()
        self._capabilities: dict[str, bool] = {}

    async def scan(self):
        """扫描 ComfyUI 已安装的节点"""
        try:
            node_info = await self.client.get_node_info()
            self._available_nodes = set(node_info.keys())
            logger.info(f"扫描到 {len(self._available_nodes)} 个节点")
            for capability, required_nodes in CAPABILITY_MAP.items():
                available = all(n in self._available_nodes for n in required_nodes)
                self._capabilities[capability] = available
                status = "✅" if available else "❌"
                logger.info(f"  {status} {capability}")
        except Exception as e:
            logger.error(f"节点扫描失败: {e}")

    def has_capability(self, capability: str) -> bool:
        return self._capabilities.get(capability, False)

    def get_capabilities(self) -> dict[str, bool]:
        return dict(self._capabilities)

    def get_available_models_info(self) -> dict:
        return {
            "nodes": list(self._available_nodes),
            "capabilities": self._capabilities,
        }
