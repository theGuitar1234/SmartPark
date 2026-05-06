from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=4, max_length=100)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=1, max_length=100)


class UpdateUserRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=120)
    new_password: str | None = Field(default=None, min_length=4, max_length=100)


class UserResponse(BaseModel):
    user_id: int
    full_name: str
    email: str


class SlotResponse(BaseModel):
    slot_id: int
    zone: str
    slot_number: str
    status: str


class DashboardResponse(BaseModel):
    total_slots: int
    occupied: int
    available: int
    reserved: int
    slots: list[SlotResponse]


class ItemRequest(BaseModel):
    field1: str = Field(..., min_length=1, max_length=200)
    field2: str = Field(..., min_length=1, max_length=200)
    field3: str = Field(..., min_length=1, max_length=200)


class ItemResponse(ItemRequest):
    id: int
