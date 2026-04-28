# VisionFlow

> AI 视觉创作智能体 — 基于 ComfyUI 的自动生图生视频系统

## 架构

```
用户描述 → Agent 理解意图 → 选择/组装 ComfyUI 工作流 → 自动提交生成 → 质量评估 → 交付
```

ComfyUI 作为核心生成引擎，Agent 层负责智能编排。

## 核心特性

- 🧠 **意图理解**：自然语言 → 结构化视觉需求
- 🔧 **工作流动态组装**：根据需求自动选择模板、注入参数、添加节点
- 🎨 **多模型支持**：Flux / SDXL / SD3.5 / AnimateDiff / SVD / CogVideoX
- 🔄 **质量闭环**：自动生成多候选 → 评估 → 迭代优化
- 📦 **工作流模板库**：可复用、可版本管理的 JSON 工作流模板

## 快速开始

### 前置条件

1. ComfyUI 已安装并运行（[搭建指南](docs/comfyui_setup.md)）
2. Python >= 3.11

### 安装

```bash
git clone https://github.com/your-username/visionflow.git
cd visionflow
cp .env.example .env
# 编辑 .env 配置 ComfyUI 地址
make install
```

### 运行

```bash
# 确保 ComfyUI 在 8188 端口运行
make run
```

### 测试

```bash
# 测试 ComfyUI 连接
curl http://localhost:8000/health

# 提交生成请求
curl -X POST http://localhost:8000/api/v1/generate \
 -H "Content-Type: application/json" \
 -d '{"prompt": "一只柴犬在樱花树下奔跑，日系动漫风格"}'
```

## 技术栈

| 层级 | 技术 |
|------|------|
| Agent 编排 | LangGraph + LangChain |
| 后端 | FastAPI + WebSocket |
| 生成引擎 | ComfyUI |
| LLM | OpenAI / Claude / 本地模型 |
| 存储 | PostgreSQL + Qdrant |

## 项目状态

🚧 **早期开发阶段**

## License

MIT
