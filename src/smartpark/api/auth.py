from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from .. import db
from ..schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from ..security import hash_password, make_token, verify_password
from .deps import get_current_user, handle_integrity_error

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest):
    user_id = db.new_id("usr")
    try:
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO users (user_id, full_name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
                (user_id, payload.full_name.strip(), str(payload.email).lower(), hash_password(payload.password), payload.role.value),
            )
            user = dict(conn.execute("SELECT user_id, full_name, email, role, is_active, created_at FROM users WHERE user_id = ?", (user_id,)).fetchone())
            user["is_active"] = bool(user["is_active"])
            return user
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    with db.transaction() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (str(payload.email).lower(),)).fetchone()
        if not row or not verify_password(payload.password, row["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
        token = make_token()
        conn.execute("INSERT INTO auth_tokens (token, user_id) VALUES (?, ?)", (token, row["user_id"]))
        user = dict(conn.execute("SELECT user_id, full_name, email, role, is_active, created_at FROM users WHERE user_id = ?", (row["user_id"],)).fetchone())
        user["is_active"] = bool(user["is_active"])
        return {"token": token, "user": user}


@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user), authorization: str | None = None):
    return {"message": "Logout is handled client-side by clearing the token."}


@router.get("/me", response_model=UserResponse)
def me(current_user: dict = Depends(get_current_user)):
    return current_user
