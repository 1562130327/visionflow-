# ComfyUI 工作流模板

## 使用方式

1. 在 ComfyUI 中设计并调试工作流
2. 导出为 API 格式 JSON（开发者模式 → Save API Format）
3. 将需要动态替换的值替换为 `{{占位符}}`
4. 保存到对应目录

## 占位符列表

| 占位符 | 说明 | 默认值 |
|--------|------|--------|
| `{{PROMPT}}` | 正向提示词 | - |
| `{{NEGATIVE}}` | 负向提示词 | low quality... |
| `{{WIDTH}}` | 宽度 | 1024 |
| `{{HEIGHT}}` | 高度 | 1024 |
| `{{STEPS}}` | 采样步数 | 25 |
| `{{CFG}}` | CFG Scale | 7.0 |
| `{{SEED}}` | 随机种子 | -1 (随机) |
| `{{CHECKPOINT}}` | 模型文件名 | - |
| `{{LORA_NAME}}` | LoRA 文件名 | None |
| `{{IMAGE_INPUT}}` | 输入图片 | - |
| `{{DURATION}}` | 视频帧数 | 16 |

## 导出工作流

在 ComfyUI 中：
1. 打开开发者模式：Settings → Enable Dev mode
2. 设计好工作流
3. 点击右侧 "Save (API Format)" 按钮
4. 将 JSON 中需要动态化的值替换为占位符
5. 放入对应目录
