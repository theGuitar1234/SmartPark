# Run Guide

## Backend

```bash
PYTHONPATH=src uvicorn smartpark.backend_app:app --reload --port 8000
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

OpenAPI docs:

```text
http://127.0.0.1:8000/docs
```

## Frontend

Native desktop window:

```bash
PYTHONPATH=src python -m smartpark.frontend_app
```

Browser mode:

```bash
SMARTPARK_FLET_VIEW=web FLET_PORT=8550 PYTHONPATH=src python -m smartpark.frontend_app
```

## Database reset

The app seeds demo data automatically on first database creation. To reset local demo data, stop the app, remove `data/smartpark.db`, and start the backend again.
