from __future__ import annotations

from fastapi import FastAPI

from .backend_app import app as backend_app

app: FastAPI = backend_app
