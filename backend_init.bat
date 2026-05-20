@echo off
set "PYTHONPATH=src"
python -m uvicorn smartpark.backend_app:app --reload --reload-dir src --port 8000