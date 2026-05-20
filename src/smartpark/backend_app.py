from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .api import auth, dashboard, lots, optimizer, payments, reports, sensors, sessions, slots, tariffs, vehicles, zones


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(seed=True)
    yield


app = FastAPI(
    title="SmartPark API",
    description="FastAPI backend for the SmartPark parking management and slot optimization system.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["System"])
def health():
    return {"status": "ok", "service": "SmartPark API"}


for router in [auth.router, dashboard.router, lots.router, zones.router, slots.router, sensors.router, vehicles.router, sessions.router, tariffs.router, payments.router, optimizer.router, reports.router]:
    app.include_router(router, prefix="/api")
