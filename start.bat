@echo off
cd /d D:\dowloads\TrainTime\backend
python -m uvicorn app.main:app --port 8000
