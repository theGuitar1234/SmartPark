from __future__ import annotations

from fastapi import Header, HTTPException, status

from .. import db


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication token is required.")
    token = authorization.removeprefix("Bearer ").strip()
    user = db.fetch_one(
        """
        SELECT u.user_id, u.full_name, u.email, u.role, u.is_active, u.created_at
        FROM auth_tokens t
        JOIN users u ON u.user_id = t.user_id
        WHERE t.token = ? AND u.is_active = 1
        """,
        (token,),
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired authentication token.")
    user["is_active"] = bool(user["is_active"])
    return user


def handle_integrity_error(ex: Exception) -> HTTPException:
    message = str(ex)
    if "UNIQUE" in message:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A record with the same unique value already exists.")
    if "FOREIGN KEY" in message:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This operation would break an existing relationship.")
    if "CHECK" in message:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The submitted value violates a database constraint.")
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Database integrity validation failed.")
