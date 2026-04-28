@echo off
title VisionFlow - AI 漫剧创作工坊
cd /d D:\visionflow

echo ============================================
echo   🦞 VisionFlow - AI 漫剧创作工坊
echo ============================================
echo.
echo [1/3] 设置环境变量...
set PYTHONPATH=D:\visionflow\src

echo [2/3] 检查依赖...
python -c "import pydantic, openai, httpx, loguru" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ 正在安装依赖，首次可能需要 2-3 分钟...
    pip install -e . -q
)

echo [3/3] 启动服务...
echo.
echo 🌐 打开浏览器访问: http://localhost:8000
echo.
echo 💡 提示: 按 Ctrl+C 停止服务
echo ============================================
echo.

uvicorn visionflow.main:app --host 0.0.0.0 --port 8000 --log-level info

if %errorlevel% neq 0 (
    echo.
    echo ❌ 启动失败，按任意键退出...
    pause
)
