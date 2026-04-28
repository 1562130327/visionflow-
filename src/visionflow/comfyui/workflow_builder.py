"""
工作流动态组装器

直接操作工作流 JSON 的节点字段（ComfyUI API 格式），
不再依赖 {{占位符}} 模板替换。
"""

import json
import random
from loguru import logger
from visionflow.comfyui.workflow_loader import WorkflowLoader


class WorkflowBuilder:
    """工作流动态组装器"""

    # Flux2-Klein-9B 文生图节点映射
    FLUX_IMAGE_NODES = {
        "prompt_node": "76",          # PrimitiveStringMultiline → 正面 prompt
        "neg_prompt": "75:67",        # CLIPTextEncode → 负面 prompt
        "width_node": "75:68",        # PrimitiveInt → 宽度
        "height_node": "75:69",       # PrimitiveInt → 高度
        "steps_node": "75:62",        # Flux2Scheduler → steps
        "cfg_node": "75:63",          # CFGGuider → cfg
        "seed_node": "75:73",         # RandomNoise → seed
        "save_prefix": "9",           # SaveImage → 前缀
    }

    # Wan2.2-14B 图生视频节点映射
    WAN_VIDEO_NODES = {
        "prompt_node": "93",          # CLIPTextEncode → 正面 prompt
        "neg_prompt": "89",           # CLIPTextEncode → 负面 prompt
        "image_node": "97",           # LoadImage → 输入图片
        "params_node": "98",          # WanImageToVideo → 宽/高/帧数
        "video_prefix": "117",        # VHS_VideoCombine → 前缀
    }

    def __init__(self):
        self.loader = WorkflowLoader()

    def build(self, template_name: str, params: dict) -> dict:
        """构建最终可执行的工作流"""
        workflow = self.loader.load(template_name)

        if template_name == "txt2img_flux":
            self._inject_flux(workflow, params)
        elif template_name == "img2video_wan":
            self._inject_wan(workflow, params)
        else:
            logger.warning(f"未知模板类型: {template_name}，跳过注入")

        logger.info(f"工作流构建完成 | 模板: {template_name} | 节点数: {len(workflow)}")
        return workflow

    def _inject_flux(self, workflow: dict, params: dict) -> dict:
        """注入 Flux2-Klein-9B 文生图参数"""
        nodes = self.FLUX_IMAGE_NODES

        # prompt
        prompt = params.get("prompt", "")
        if prompt and nodes["prompt_node"] in workflow:
            workflow[nodes["prompt_node"]]["inputs"]["value"] = prompt
            logger.info(f"注入正面 prompt: {prompt[:60]}...")

        # 负面 prompt
        neg = params.get("negative_text", "low quality, blurry, deformed, watermark")
        if nodes["neg_prompt"] in workflow:
            workflow[nodes["neg_prompt"]]["inputs"]["text"] = neg

        # 宽高
        width = params.get("width", 1024)
        height = params.get("height", 1024)
        if nodes["width_node"] in workflow:
            workflow[nodes["width_node"]]["inputs"]["value"] = width
        if nodes["height_node"] in workflow:
            workflow[nodes["height_node"]]["inputs"]["value"] = height

        # steps
        steps = params.get("steps", 20)
        if nodes["steps_node"] in workflow:
            workflow[nodes["steps_node"]]["inputs"]["steps"] = steps

        # cfg
        cfg = params.get("cfg", 5)
        if nodes["cfg_node"] in workflow:
            workflow[nodes["cfg_node"]]["inputs"]["cfg"] = cfg

        # seed（随机）
        seed = params.get("seed", random.randint(0, 2**32 - 1))
        if nodes["seed_node"] in workflow:
            workflow[nodes["seed_node"]]["inputs"]["noise_seed"] = seed

        # 输出文件名前缀
        prefix = params.get("filename_prefix", "VisionFlow")
        if nodes["save_prefix"] in workflow:
            workflow[nodes["save_prefix"]]["inputs"]["filename_prefix"] = prefix

        logger.info(f"Flux2 参数: {width}x{height} | steps={steps} | cfg={cfg} | seed={seed}")
        return workflow

    def _inject_wan(self, workflow: dict, params: dict) -> dict:
        """注入 Wan2.2-14B 图生视频参数"""
        nodes = self.WAN_VIDEO_NODES

        # prompt（CLIPTextEncode）
        prompt = params.get("prompt", "")
        if prompt and nodes["prompt_node"] in workflow:
            workflow[nodes["prompt_node"]]["inputs"]["text"] = prompt
            logger.info(f"注入视频 prompt: {prompt[:60]}...")

        # 负面 prompt
        neg = params.get("negative_text", "low quality, blurry, deformed, watermark")
        if nodes["neg_prompt"] in workflow:
            workflow[nodes["neg_prompt"]]["inputs"]["text"] = neg

        # 输入图片（已上传到 ComfyUI）
        image_name = params.get("image_input", "")
        if image_name and nodes["image_node"] in workflow:
            workflow[nodes["image_node"]]["inputs"]["image"] = image_name
            logger.info(f"注入输入图片: {image_name}")

        # 视频参数
        width = params.get("width", 640)
        height = params.get("height", 640)
        length = params.get("length", 81)  # 81帧 ≈ 5秒 @ 16fps
        if nodes["params_node"] in workflow:
            workflow[nodes["params_node"]]["inputs"]["width"] = width
            workflow[nodes["params_node"]]["inputs"]["height"] = height
            workflow[nodes["params_node"]]["inputs"]["length"] = length

        # 输出前缀
        prefix = params.get("filename_prefix", "VisionFlowVideo")
        if nodes["video_prefix"] in workflow:
            workflow[nodes["video_prefix"]]["inputs"]["filename_prefix"] = prefix

        logger.info(f"Wan 参数: {width}x{height} | {length}帧")
        return workflow

    def set_image_input(self, workflow: dict, uploaded_filename: str) -> dict:
        """设置输入图片（兼容旧占位符模式）"""
        return self._inject_wan(workflow, {"image_input": uploaded_filename})
