# ComfyUI 环境搭建

## 安装 ComfyUI

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
pip install -r requirements.txt
```

## 推荐模型

### 生图
| 模型 | 文件名 | 用途 |
|------|--------|------|
| SDXL 1.0 | sd_xl_base_1.0.safetensors | 通用 |
| Flux Dev | flux1-dev.safetensors | 写实 |
| SD 3.5 Large | sd3.5_large.safetensors | 通用 |

### 视频
| 模型 | 文件名 | 用途 |
|------|--------|------|
| SVD XT 1.1 | svd_xt_1_1.safetensors | 图生视频 |
| AnimateDiff | mm_sd_v15_v2.ckpt | 文生视频 |

### 必装自定义节点

```bash
cd ComfyUI/custom_nodes

# ControlNet
git clone https://github.com/Fannovel16/comfyui_controlnet_aux

# IP-Adapter
git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus

# AnimateDiff
git clone https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved

# 超分辨率
git clone https://github.com/WASasquatch/was-node-suite-comfyui

# 人脸修复
git clone https://github.com/scraed/ComfyUI-FaceRestore
```

## 启动

```bash
python main.py --listen 0.0.0.0 --port 8188
```

## 验证

```bash
curl http://127.0.0.1:8188/system_stats
```
