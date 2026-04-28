"""
工作流动态组装器

根据意图 + 规划，将工作流模板中的占位符替换为实际参数，
动态添加/移除节点，生成最终可执行的工作流 JSON。
"""

import copy
import json
from loguru import logger
from visionflow.comfyui.workflow_loader import WorkflowLoader


class WorkflowBuilder:
    """工作流动态组装器"""

    DEFAULTS = {
        "PROMPT": "",
        "NEGATIVE": "low quality, blurry, deformed, watermark",
        "WIDTH": 1024,
        "HEIGHT": 1024,
        "STEPS": 25,
        "CFG": 7.0,
        "SEED": -1,
        "CHECKPOINT": "sd_xl_base_1.0.safetensors",
        "LORA_NAME": "None",
        "LORA_STRENGTH": 1.0,
        "IMAGE_INPUT": "",
        "CONTROLNET_MODEL": "None",
        "DURATION": 16,
    }

    def __init__(self):
        self.loader = WorkflowLoader()

    def build(
        self,
        template_name: str,
        params: dict,
        extra_nodes: list[dict] | None = None,
    ) -> dict:
        """构建最终可执行的工作流"""
        workflow = self.loader.load(template_name)
        final_params = {**self.DEFAULTS, **params}
        workflow = self._inject_params(workflow, final_params)
        if extra_nodes:
            for node in extra_nodes:
                node_id = str(len(workflow) + 1)
                workflow[node_id] = node
                logger.info(f"添加额外节点: {node_id} - {node.get('class_type')}")
        logger.info(f"工作流构建完成 | 模板: {template_name} | 节点数: {len(workflow)}")
        return workflow

    def _inject_params(self, workflow: dict, params: dict) -> dict:
        """递归替换工作流 JSON 中的占位符"""
        json_str = json.dumps(workflow)
        for key, value in params.items():
            placeholder = "{{" + key + "}}"
            if placeholder in json_str:
                json_str = json_str.replace(placeholder, str(value))
        return json.loads(json_str)

    def add_lora(
        self,
        workflow: dict,
        lora_name: str,
        strength_model: float = 1.0,
        strength_clip: float = 1.0,
    ) -> dict:
        """动态添加 LoRA 节点"""
        ckpt_node_id = None
        for node_id, node in workflow.items():
            if node.get("class_type") in ("CheckpointLoaderSimple", "CheckpointLoader", "unCLIPCheckpointLoader"):
                ckpt_node_id = node_id
                break
        if not ckpt_node_id:
            logger.warning("未找到 Checkpoint 节点，无法添加 LoRA")
            return workflow
        lora_node_id = f"lora_{lora_name.replace('.','_')}"
        workflow[lora_node_id] = {
            "class_type": "LoraLoader",
            "inputs": {
                "lora_name": lora_name,
                "strength_model": strength_model,
                "strength_clip": strength_clip,
                "model": [ckpt_node_id, 0],
                "clip": [ckpt_node_id, 1],
            },
        }
        for node_id, node in workflow.items():
            if node_id == lora_node_id:
                continue
            inputs = node.get("inputs", {})
            for key, value in inputs.items():
                if isinstance(value, list) and len(value) == 2:
                    if value[0] == ckpt_node_id and value[1] == 0:
                        inputs[key] = [lora_node_id, 0]
                    elif value[0] == ckpt_node_id and value[1] == 1:
                        inputs[key] = [lora_node_id, 1]
        logger.info(f"已添加 LoRA: {lora_name}")
        return workflow

    def set_image_input(self, workflow: dict, uploaded_filename: str) -> dict:
        """设置输入图片"""
        for node_id, node in workflow.items():
            if node.get("class_type") == "LoadImage":
                node["inputs"]["image"] = uploaded_filename
                logger.info(f"设置输入图片: {uploaded_filename}")
                break
        return workflow

    def set_model(self, workflow: dict, checkpoint_name: str) -> dict:
        """设置 checkpoint 模型"""
        for node_id, node in workflow.items():
            if node.get("class_type") in ("CheckpointLoaderSimple", "CheckpointLoader"):
                node["inputs"]["ckpt_name"] = checkpoint_name
                logger.info(f"设置模型: {checkpoint_name}")
                break
        return workflow
