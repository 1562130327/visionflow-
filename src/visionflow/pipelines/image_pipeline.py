"""生图 Pipeline — 基于 ComfyUI"""

import random
from loguru import logger
from visionflow.models.task import Task, TaskStatus
from visionflow.comfyui import ComfyUIClient, WorkflowBuilder, ComfyUIMonitor
from visionflow.agents.workflow_agent import WorkflowAgent


class ImagePipeline:
    """基于 ComfyUI 的图像生成流水线"""

    def __init__(self):
        self.client = ComfyUIClient()
        self.builder = WorkflowBuilder()
        self.monitor = ComfyUIMonitor(self.client)
        self.workflow_agent = WorkflowAgent()

    async def run(self, intent, num_candidates: int = 4) -> Task:
        """完整的图像生成流程"""
        task = Task(
            id="task_" + str(random.randint(10000, 99999)),
            user_input=intent.description,
            status=TaskStatus.PLANNING,
        )

        # 1. 选择工作流 + 构建 Prompt
        wf_plan = await self.workflow_agent.plan_workflow(intent)
        template = wf_plan["template"]

        label = "flux" if "flux" in template else "sdxl"
        prompt_text = intent.description
        task.prompt_used = prompt_text
        logger.info(f"Prompt: {prompt_text[:80]}...")

        # 2. 组装并提交
        params = wf_plan["params"]
        params["PROMPT"] = prompt_text

        task.status = TaskStatus.GENERATING
        all_candidates = []

        for i in range(num_candidates):
            params["SEED"] = random.randint(0, 2**32 - 1)
            workflow = self.builder.build(template, params)

            if wf_plan.get("needs_lora") and wf_plan.get("lora_config"):
                lora = wf_plan["lora_config"]
                workflow = self.builder.add_lora(workflow, lora["name"], lora.get("strength", 1.0))

            logger.info(f"生成候选 {i+1}/{num_candidates} (seed: {params['SEED']})")
            result = await self.monitor.submit_and_wait(workflow, save_dir=f"./outputs/{task.id}")

            if result.output_urls:
                all_candidates.extend(result.output_urls)

        task.status = TaskStatus.COMPLETED
        task.output_urls = all_candidates
        logger.info("图像生成完成")
        return task
