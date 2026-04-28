@echo off
cd /d D:\visionflow
set PYTHONPATH=D:\visionflow\src
uvicorn visionflow.main:app --reload --host 0.0.0.0 --port 8000
pause
