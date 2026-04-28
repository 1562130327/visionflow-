# VisionFlow 架构文档

## 整体架构

```
用户输入
 ▼
┌──────────────────────────────────────────┐
│ Agent 编排层                               │
│ Intent → Planner → Prompt → Critic        │
└────────────────┬─────────────────────────┘
 ▼
┌──────────────────────────────────────────┐
│ ComfyUI 调度层                            │
│                                            │
│ Workflow 模板库 ← 动态组装工作流 JSON      │
│ ↓                                          │
│ ComfyUI API Client → 提交/监控/获取结果    │
│ ↓                                          │
│ ComfyUI Server (本地 GPU / 远程 GPU)       │
│                                            │
│ ┌─────────┐ ┌────────┐ ┌────────────┐     │
│ │ SDXL/Flux│ │ControlNet│ │ IP-Adapter │     │
│ │ SD3.5    │ │ LoRA    │ │ AnimateDiff│     │
│ │ CogVideo │ │ Upscale │ │ SAM/RMBG   │     │
│ └─────────┘ └────────┘ └────────────┘     │
└──────────────────────────────────────────┘
```

## 目录结构

```
visionflow/
├── workflows/        # ComfyUI 工作流模板
│   ├── image/        # 生图工作流
│   ├── video/        # 生视频工作流
│   └── composite/    # 复合工作流
├── src/visionflow/
│   ├── agents/       # LLM Agent 层
│   ├── comfyui/     # ComfyUI 集成层
│   ├── pipelines/   # 生成流水线
│   ├── models/      # 数据模型
│   └── api/         # API 路由
└── docs/            # 文档
```

## 核心流程

1. 用户输入自然语言描述
2. Agent 层理解意图（任务类型、风格、参数）
3. 选择并组装 ComfyUI 工作流
4. 提交生成（支持多候选）
5. 质量评估和迭代
6. 交付结果

## 技术栈

| 层级 | 技术 |
|------|------|
| Agent 编排 | LangGraph + LangChain |
| 后端 | FastAPI + WebSocket |
| 生成引擎 | ComfyUI |
| LLM | OpenAI / Claude / 本地模型 |
| 存储 | PostgreSQL + Qdrant |
