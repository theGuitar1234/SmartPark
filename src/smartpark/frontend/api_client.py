from __future__ import annotations

import os
from typing import Any

import httpx


class ApiError(Exception):
    pass


class SmartParkClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or os.getenv("SMARTPARK_API_URL", "http://127.0.0.1:8000/api")).rstrip("/")
        self.token: str | None = None

    def set_token(self, token: str | None) -> None:
        self.token = token

    def request(self, method: str, path: str, json: dict | None = None, params: dict | None = None) -> Any:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            with httpx.Client(timeout=12) as client:
                response = client.request(method, f"{self.base_url}{path}", json=json, params=params, headers=headers)
        except httpx.RequestError as ex:
            raise ApiError(f"Backend is unavailable: {ex}") from ex
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise ApiError(str(detail))
        if not response.content:
            return None
        return response.json()


    def request_text(self, method: str, path: str, params: dict | None = None) -> str:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            with httpx.Client(timeout=12) as client:
                response = client.request(method, f"{self.base_url}{path}", params=params, headers=headers)
        except httpx.RequestError as ex:
            raise ApiError(f"Backend is unavailable: {ex}") from ex
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise ApiError(str(detail))
        return response.text

    def login(self, email: str, password: str) -> dict:
        data = self.request("POST", "/auth/login", json={"email": email, "password": password})
        self.set_token(data["token"])
        return data

    def register(self, full_name: str, email: str, password: str) -> dict:
        return self.request("POST", "/auth/register", json={"full_name": full_name, "email": email, "password": password, "role": "admin"})

    def dashboard(self) -> dict:
        return self.request("GET", "/dashboard")

    def page(self, resource: str, **params) -> dict:
        return self.request("GET", f"/{resource}", params=params)

    def create(self, resource: str, payload: dict) -> dict:
        return self.request("POST", f"/{resource}", json=payload)

    def update(self, resource: str, record_id: str, payload: dict) -> dict:
        return self.request("PUT", f"/{resource}/{record_id}", json=payload)

    def delete(self, resource: str, record_id: str) -> dict:
        return self.request("DELETE", f"/{resource}/{record_id}")

    def post(self, path: str, payload: dict | None = None) -> dict:
        return self.request("POST", path, json=payload or {})

    def report_summary(self) -> dict:
        return self.request("GET", "/reports/summary")

    def slot_detail(self, slot_id: str) -> dict:
        return self.request("GET", f"/slots/{slot_id}/detail")

    def receipt(self, session_id: str) -> dict:
        return self.request("GET", f"/payments/receipt/{session_id}")

    def bulk_preview(self, payload: dict) -> dict:
        return self.request("POST", "/slots/bulk-preview", json=payload)

    def bulk_create(self, payload: dict) -> dict:
        return self.request("POST", "/slots/bulk-create", json=payload)

    def optimizer(self, payload: dict) -> dict:
        return self.request("POST", "/optimizer/recommend", json=payload)

    def export_csv(self, kind: str) -> str:
        allowed = {"summary", "payments", "sessions"}
        if kind not in allowed:
            raise ApiError("Unsupported export type.")
        return self.request_text("GET", f"/reports/{kind}.csv")
