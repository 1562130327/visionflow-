"""
工作流模板加载器

加载 workflows/ 目录下的 JSON 模板，并支持参数注入
"""

import json
from pathlib import Path
from loguru import logger


WORKFLOW_DIR = Path(__file__).resolve().parent.parent.parent.parent / "workflows"


class WorkflowLoader:
    """工作流模板加载与管理"""

    def __init__(self, workflow_dir: Path | None = None):
        self.workflow_dir = workflow_dir or WORKFLOW_DIR

    def list_workflows(self, category: str | None = None) -> list[dict]:
        """列出所有可用的工作流模板"""
        workflows = []
        search_dir = self.workflow_dir / category if category else self.workflow_dir
        if not search_dir.exists():
            return workflows
        for json_file in search_dir.rglob("*.json"):
            rel_path = json_file.relative_to(self.workflow_dir)
            workflows.append({
                "name": json_file.stem,
                "path": str(rel_path),
                "category": rel_path.parts[0] if len(rel_path.parts) > 1 else "root",
            })
        return workflows

    def load(self, name: str) -> dict:
        """
        加载工作流模板

        Args:
            name: 工作流名称或路径，如 'image/txt2img_flux'

        Returns:
            工作流 JSON 字典
        """
        if not name.endswith(".json"):
            name = f"{name}.json"
        path = self.workflow_dir / name
        if not path.exists():
            matches = list(self.workflow_dir.rglob(name))
            if matches:
                path = matches[0]
            else:
                raise FileNotFoundError(f"工作流模板不存在: {name}")
        with open(path, "r", encoding="utf-8") as f:
            workflow = json.load(f)
        logger.info(f"加载工作流: {path.name} ({len(workflow)} 个节点)")
        return workflow

    def load_raw(self, name: str) -> str:
        """加载原始 JSON 字符串"""
        if not name.endswith(".json"):
            name = f"{name}.json"
        path = self.workflow_dir / name
        if not path.exists():
            matches = list(self.workflow_dir.rglob(name))
            if matches:
                path = matches[0]
            else:
                raise FileNotFoundError(f"工作流模板不存在: {name}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
