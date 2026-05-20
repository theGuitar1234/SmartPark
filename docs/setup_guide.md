# Setup Guide

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src pytest -q
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH='src'
pytest -q
```

The final package intentionally excludes `.venv`, caches, compiled Python files, and SQLite WAL/SHM files.
