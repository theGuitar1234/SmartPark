from __future__ import annotations

from enum import Enum
from typing import Any
import re

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class Role(str, Enum):
    admin = "admin"
    operator = "operator"


class SlotStatus(str, Enum):
    available = "Available"
    occupied = "Occupied"
    reserved = "Reserved"
    maintenance = "Maintenance"
    disabled = "Disabled"


class SlotType(str, Enum):
    standard = "Standard"
    motorcycle = "Motorcycle"
    ev = "EV"
    disabled_access = "Disabled Access"
    truck = "Truck"
    vip = "VIP"


class VehicleType(str, Enum):
    car = "Car"
    motorcycle = "Motorcycle"
    ev = "EV"
    disabled_access = "Disabled Access"
    truck = "Truck"
    vip = "VIP"


class SessionStatus(str, Enum):
    active = "Active"
    completed = "Completed"
    cancelled = "Cancelled"


class PaymentStatus(str, Enum):
    unpaid = "Unpaid"
    pending = "Pending"
    paid = "Paid"
    failed = "Failed"
    refunded = "Refunded"


class PaymentMethod(str, Enum):
    cash = "Cash"
    card = "Card"
    online = "Online"
    wallet = "Wallet"


class SensorStatus(str, Enum):
    clear = "Clear"
    occupied = "Occupied"
    fault = "Fault"
    unknown = "Unknown"


class TokenResponse(BaseModel):
    token: str
    user: dict[str, Any]


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    role: Role = Role.admin


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=100)


class UserResponse(BaseModel):
    user_id: str
    full_name: str
    email: EmailStr
    role: Role
    is_active: bool
    created_at: str


class ParkingLotCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    address: str = Field(min_length=2, max_length=220)
    description: str = Field(default="", max_length=500)


class ParkingLotUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    address: str | None = Field(default=None, min_length=2, max_length=220)
    description: str | None = Field(default=None, max_length=500)


class ParkingLotResponse(BaseModel):
    lot_id: str
    name: str
    address: str
    description: str
    created_at: str
    updated_at: str


class ParkingZoneCreate(BaseModel):
    lot_id: str
    name: str = Field(min_length=1, max_length=80)
    floor_level: int = Field(default=0, ge=-5, le=80)
    zone_type: SlotType = SlotType.standard
    priority_score: int = Field(default=50, ge=0, le=100)


class ParkingZoneUpdate(BaseModel):
    lot_id: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=80)
    floor_level: int | None = Field(default=None, ge=-5, le=80)
    zone_type: SlotType | None = None
    priority_score: int | None = Field(default=None, ge=0, le=100)


class ParkingZoneResponse(BaseModel):
    zone_id: str
    lot_id: str
    lot_name: str | None = None
    name: str
    floor_level: int
    zone_type: SlotType
    priority_score: int
    created_at: str
    updated_at: str


class ParkingSlotCreate(BaseModel):
    zone_id: str
    slot_code: str = Field(min_length=1, max_length=40)
    slot_type: SlotType = SlotType.standard
    status: SlotStatus = SlotStatus.available
    distance_score: int = Field(default=50, ge=0, le=100)
    priority_score: int = Field(default=50, ge=0, le=100)
    override_reason: str | None = Field(default=None, max_length=300)

    @field_validator("slot_code")
    @classmethod
    def normalize_slot_code(cls, value: str) -> str:
        return value.strip().upper()


class ParkingSlotUpdate(BaseModel):
    zone_id: str | None = None
    slot_code: str | None = Field(default=None, min_length=1, max_length=40)
    slot_type: SlotType | None = None
    status: SlotStatus | None = None
    distance_score: int | None = Field(default=None, ge=0, le=100)
    priority_score: int | None = Field(default=None, ge=0, le=100)
    override_reason: str | None = Field(default=None, max_length=300)

    @field_validator("slot_code")
    @classmethod
    def normalize_slot_code(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else value


class ParkingSlotResponse(BaseModel):
    slot_id: str
    zone_id: str
    zone_name: str | None = None
    lot_name: str | None = None
    slot_code: str
    slot_type: SlotType
    status: SlotStatus
    distance_score: int
    priority_score: int
    override_reason: str | None = None
    sensor_code: str | None = None
    active_plate: str | None = None
    created_at: str
    updated_at: str


class SlotStatusUpdate(BaseModel):
    status: SlotStatus
    reason: str = Field(min_length=3, max_length=300)


class BulkSlotPreviewRequest(BaseModel):
    zone_id: str
    prefix: str = Field(min_length=1, max_length=12)
    start_number: int = Field(ge=1, le=9999)
    count: int = Field(ge=1, le=250)
    slot_type: SlotType = SlotType.standard
    distance_score: int = Field(default=50, ge=0, le=100)
    priority_score: int = Field(default=50, ge=0, le=100)

    @field_validator("prefix")
    @classmethod
    def normalize_prefix(cls, value: str) -> str:
        return value.strip().upper()


class SensorCreate(BaseModel):
    sensor_code: str = Field(min_length=2, max_length=60)
    sensor_type: str = Field(default="Ultrasonic", min_length=2, max_length=80)
    slot_id: str | None = None
    is_active: bool = True
    battery_level: int = Field(default=100, ge=0, le=100)

    @field_validator("sensor_code")
    @classmethod
    def normalize_sensor_code(cls, value: str) -> str:
        return value.strip().upper()


class SensorUpdate(BaseModel):
    sensor_code: str | None = Field(default=None, min_length=2, max_length=60)
    sensor_type: str | None = Field(default=None, min_length=2, max_length=80)
    slot_id: str | None = None
    is_active: bool | None = None
    battery_level: int | None = Field(default=None, ge=0, le=100)

    @field_validator("sensor_code")
    @classmethod
    def normalize_sensor_code(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else value


class SensorResponse(BaseModel):
    sensor_id: str
    sensor_code: str
    sensor_type: str
    slot_id: str | None = None
    slot_code: str | None = None
    is_active: bool
    last_status: SensorStatus
    battery_level: int
    last_seen_at: str | None = None
    created_at: str
    updated_at: str


class SensorSimulationRequest(BaseModel):
    reported_status: SensorStatus
    raw_payload: str = Field(default="simulated update", max_length=500)


class VehicleCreate(BaseModel):
    plate_number: str = Field(min_length=2, max_length=24)
    vehicle_type: VehicleType = VehicleType.car
    owner_name: str = Field(default="", max_length=100)

    @field_validator("plate_number")
    @classmethod
    def normalize_plate(cls, value: str) -> str:
        plate = re.sub(r"\s+", "", value.upper())
        if not re.match(r"^[A-Z0-9-]{2,24}$", plate):
            raise ValueError("Plate number may contain letters, numbers, and hyphens only.")
        return plate


class VehicleUpdate(BaseModel):
    plate_number: str | None = Field(default=None, min_length=2, max_length=24)
    vehicle_type: VehicleType | None = None
    owner_name: str | None = Field(default=None, max_length=100)

    @field_validator("plate_number")
    @classmethod
    def normalize_plate(cls, value: str | None) -> str | None:
        if value is None:
            return value
        plate = re.sub(r"\s+", "", value.upper())
        if not re.match(r"^[A-Z0-9-]{2,24}$", plate):
            raise ValueError("Plate number may contain letters, numbers, and hyphens only.")
        return plate


class VehicleResponse(BaseModel):
    vehicle_id: str
    plate_number: str
    vehicle_type: VehicleType
    owner_name: str
    created_at: str
    updated_at: str


class TariffPlanCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    hourly_rate: float = Field(ge=0)
    grace_minutes: int = Field(default=0, ge=0, le=240)
    daily_max: float = Field(ge=0)
    vehicle_type: VehicleType | None = None
    zone_id: str | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_daily_max(self):
        if self.daily_max and self.hourly_rate and self.daily_max < self.hourly_rate:
            raise ValueError("Daily maximum cannot be below the hourly rate.")
        return self


class TariffPlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    hourly_rate: float | None = Field(default=None, ge=0)
    grace_minutes: int | None = Field(default=None, ge=0, le=240)
    daily_max: float | None = Field(default=None, ge=0)
    vehicle_type: VehicleType | None = None
    zone_id: str | None = None
    is_active: bool | None = None


class TariffPlanResponse(BaseModel):
    tariff_id: str
    name: str
    hourly_rate: float
    grace_minutes: int
    daily_max: float
    vehicle_type: VehicleType | None = None
    zone_id: str | None = None
    zone_name: str | None = None
    is_active: bool
    created_at: str
    updated_at: str


class StartSessionRequest(BaseModel):
    plate_number: str = Field(min_length=2, max_length=24)
    vehicle_type: VehicleType = VehicleType.car
    owner_name: str = Field(default="", max_length=100)
    zone_id: str | None = None
    slot_id: str | None = None
    tariff_id: str | None = None
    entry_time: str | None = None
    use_optimizer: bool = True

    @field_validator("plate_number")
    @classmethod
    def normalize_plate(cls, value: str) -> str:
        plate = re.sub(r"\s+", "", value.upper())
        if not re.match(r"^[A-Z0-9-]{2,24}$", plate):
            raise ValueError("Plate number may contain letters, numbers, and hyphens only.")
        return plate


class ExitSessionRequest(BaseModel):
    exit_time: str | None = None


class SessionResponse(BaseModel):
    session_id: str
    vehicle_id: str
    plate_number: str | None = None
    vehicle_type: VehicleType | None = None
    slot_id: str
    slot_code: str | None = None
    tariff_id: str
    tariff_name_snapshot: str
    hourly_rate_snapshot: float
    grace_minutes_snapshot: int
    daily_max_snapshot: float
    entry_time: str
    exit_time: str | None = None
    status: SessionStatus
    fee_amount: float
    payment_status: PaymentStatus
    created_at: str
    updated_at: str


class PaymentCreate(BaseModel):
    session_id: str
    paid_amount: float = Field(ge=0)
    method: PaymentMethod
    status: PaymentStatus = PaymentStatus.paid

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: PaymentStatus) -> PaymentStatus:
        if value == PaymentStatus.unpaid:
            raise ValueError("Payment status cannot be Unpaid for a payment record.")
        return value


class PaymentResponse(BaseModel):
    payment_id: str
    session_id: str
    paid_amount: float
    method: PaymentMethod
    status: PaymentStatus
    reference_number: str
    paid_at: str | None = None
    created_at: str
    updated_at: str


class OptimizerRequest(BaseModel):
    vehicle_type: VehicleType
    zone_id: str | None = None


class OptimizerResponse(BaseModel):
    slot: dict[str, Any] | None
    candidates_considered: int
    explanation: list[str]
    score_breakdown: dict[str, Any] | None


class PageResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[dict[str, Any]]
