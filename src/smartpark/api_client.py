import os
import httpx

API_BASE_URL = os.getenv("SMARTPARK_API_URL", "http://127.0.0.1:8000/api")


class APIError(Exception):
    pass


def request(method: str, path: str, json: dict | None = None, params: dict | None = None):
    url = f"{API_BASE_URL}{path}"

    try:
        with httpx.Client(timeout=10) as client:
            response = client.request(method, url, json=json, params=params)

    except httpx.RequestError as ex:
        raise APIError(f"Could not connect to API: {ex}")

    if response.status_code >= 400:
        try:
            data = response.json()
            detail = data.get("detail", response.text)
        except Exception:
            detail = response.text

        raise APIError(str(detail))

    if not response.content:
        return None

    return response.json()


def register_user(full_name: str, email: str, password: str):
    return request(
        "POST",
        "/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "password": password,
        },
    )


def login_user(email: str, password: str):
    return request(
        "POST",
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def update_user(
    user_id: int, full_name: str, email: str, new_password: str | None = None
):
    return request(
        "PUT",
        f"/users/{user_id}",
        json={
            "full_name": full_name,
            "email": email,
            "new_password": new_password,
        },
    )


def get_dashboard():
    return request("GET", "/dashboard")


def get_items(search: str | None = None):
    params = {"search": search} if search else None
    return request("GET", "/items", params=params)


def create_item(field1: str, field2: str, field3: str):
    return request(
        "POST",
        "/items",
        json={
            "field1": field1,
            "field2": field2,
            "field3": field3,
        },
    )


def update_item(item_id: int, field1: str, field2: str, field3: str):
    return request(
        "PUT",
        f"/items/{item_id}",
        json={
            "field1": field1,
            "field2": field2,
            "field3": field3,
        },
    )


def delete_item(item_id: int):
    return request("DELETE", f"/items/{item_id}")
