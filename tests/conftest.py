from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from smartpark.backend_app import app
from smartpark.db import init_db


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SMARTPARK_DB_PATH", str(tmp_path / "smartpark_test.db"))
    init_db(reset=True, seed=True)
    with TestClient(app) as test_client:
        login = test_client.post("/api/auth/login", json={"email": "admin@smartpark.com", "password": "admin1234"})
        assert login.status_code == 200
        token = login.json()["token"]
        test_client.headers.update({"Authorization": f"Bearer {token}"})
        yield test_client
