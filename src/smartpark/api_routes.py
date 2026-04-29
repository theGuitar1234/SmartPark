import sqlite3

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse

from . import db
from .schemas import (
    RegisterRequest,
    LoginRequest,
    UpdateUserRequest,
    UserResponse,
    DashboardResponse,
)

router = APIRouter(prefix="/api", tags=["SmartPark API"])


@router.get("/", include_in_schema=False)
def api_root():
    return RedirectResponse(url="/docs")


@router.get("/health")
def health_check():
    return {"status": "ok", "message": "SmartPark API is running"}


@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(payload: RegisterRequest):
    try:
        user = db.create_user(
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
        )
        return user

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists.",
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.post("/auth/login", response_model=UserResponse)
def login_user(payload: LoginRequest):
    user = db.authenticate_user(payload.email, payload.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    return user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UpdateUserRequest):
    try:
        updated_user = db.update_user(
            user_id=user_id,
            full_name=payload.full_name,
            email=payload.email,
            new_password=payload.new_password,
        )
        return updated_user

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That email already exists.",
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard():
    return db.get_dashboard_data()
