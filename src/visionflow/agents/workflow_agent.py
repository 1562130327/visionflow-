"""
工作流组装 Agent

根据意图和规划，决定使用哪个工作流模板，
并组装具体参数，交给 WorkflowBuilder 执行。
"""

from loguru import logger
from visionflow.models.intent import TaskType


WORKFLOW_MAP = {
    ("image", "realistic"): "image/txt2img_flux",
    ("image", "product_photo"): "composite/product_photo",
    ("image", "anime"): "image/txt2img_sdxl",
    ("image", "ghibli"): "image/txt2img_sdxl",
    ("image", "cyberpunk"): "image/txt2img_flux",
    ("image", "minimalist"): "image/txt2img_flux",
    ("image", "oil_painting"): "image/txt2img_sdxl",
    ("image", "watercolor"): "image/txt2img_sdxl",
    ("image", "custom"): "image/txt2img_flux",
    ("video", "realistic"): "video/img2video_svd",
    ("video", "anime"): "video/txt2video_animatediff",
    ("video", "custom"): "video/img2video_cogvideo",
}

MODEL_MAP = {
    "image/txt2img_flux": "flux1-dev.safetensors",
    "image/txt2img_sdxl": "sd_xl_base_1.0.safetensors",
    "image/txt2img_sd35": "sd3.5_large.safetensors",
    "composite/product_photo": "flux1-dev.safetensors",
}

RATIO_SIZE = {
    "1:1": (1024, 1024),
    "16:9": (1344, 768),
    "9:16": (768, 1344),
    "4:3": (1152, 864),
    "3:4": (864, 1152),
}


class WorkflowAgent:
    """工作流组装 Agent"""

    async def plan_workflow(self, intent) -> dict:
        """根据意图选择工作流模板和参数"""
        task_type = intent.task_type.value
        style = intent.style.value if intent.style else "custom"
        template = WORKFLOW_MAP.get((task_type, style), f"{task_type}/txt2img_flux")
        logger.info(f"选择工作流模板: {template} (任务: {task_type}, 风格: {style})")
        params = self._build_params(intent, template)
        return {
            "template": template,
            "params": params,
            "needs_lora": self._needs_lora(intent),
            "lora_config": self._get_lora_config(intent) if self._needs_lora(intent) else None,
            "needs_controlnet": self._needs_controlnet(intent),
            "needs_upscale": self._needs_upscale(intent),
            "needs_face_restore": self._needs_face_restore(intent),
            "needs_remove_bg": self._needs_remove_bg(intent),
            "postprocess": self._get_postprocess(intent),
        }

    def _build_params(self, intent, template: str) -> dict:
        w, h = RATIO_SIZE.get(intent.aspect_ratio, (1024, 1024))
        checkpoint = MODEL_MAP.get(template, "flux1-dev.safetensors")
        params = {
            "WIDTH": w,
            "HEIGHT": h,
            "STEPS": 25,
            "CFG": 7.0,
            "SEED": -1,
            "CHECKPOINT": checkpoint,
        }
        if intent.task_type == TaskType.VIDEO:
            params["DURATION"] = int((intent.duration or 5) * 8)
        return params

    def _needs_lora(self, intent) -> bool:
        return False

    def _get_lora_config(self, intent) -> dict | None:
        return None

    def _needs_controlnet(self, intent) -> bool:
        return bool(intent.reference_images) and intent.task_type == TaskType.IMAGE

    def _needs_upscale(self, intent) -> bool:
        return intent.quality_target in ("4K", "ultra", "high")

    def _needs_face_restore(self, intent) -> bool:
        subjects_text = " ".join(s.name for s in intent.subjects)
        return any(kw in subjects_text for kw in ["人", "脸", "portrait"])

    def _needs_remove_bg(self, intent) -> bool:
        return any(kw in intent.description for kw in ["白底", "透明底", "抠图", "去背景"])

    def _get_postprocess(self, intent) -> list[str]:
        steps = []
        if self._needs_upscale(intent):
            steps.append("upscale")
        if self._needs_face_restore(intent):
            steps.append("face_restore")
        if self._needs_remove_bg(intent):
            steps.append("remove_bg")
        return steps
