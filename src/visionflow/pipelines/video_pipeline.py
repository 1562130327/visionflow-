"""生视频 Pipeline"""

import random
from loguru import logger
from visionflow.models.task import Task, TaskStatus
from visionflow.comfyui import ComfyUIClient, WorkflowBuilder, ComfyUIMonitor
from visionflow.agents.workflow_agent import WorkflowAgent


class VideoPipeline:
    """基于 ComfyUI 的视频生成流水线"""

    def __init__(self):
        self.client = ComfyUIClient()
        self.builder = WorkflowBuilder()
        self.monitor = ComfyUIMonitor(self.client)
        self.workflow_agent = WorkflowAgent()

    async def run(self, intent, num_candidates: int = 1) -> Task:
        task = Task(
            id="vid_" + str(random.randint(10000, 99999)),
            user_input=intent.description,
            status=TaskStatus.PLANNING,
        )
        wf_plan = await self.workflow_agent.plan_workflow(intent)
        template = wf_plan["template"]
        params = wf_plan["params"]
        params["PROMPT"] = intent.description
        task.prompt_used = intent.description

        task.status = TaskStatus.GENERATING
        for i in range(num_candidates):
            params["SEED"] = random.randint(0, 2**32 - 1)
            workflow = self.builder.build(template, params)
            logger.info(f"生成视频候选 {i+1}/{num_candidates}")
            result = await self.monitor.submit_and_wait(workflow, save_dir=f"./outputs/{task.id}")
            if result.output_urls:
                task.output_urls.extend(result.output_urls)

        task.status = TaskStatus.COMPLETED
        logger.info("视频生成完成")
        return task
