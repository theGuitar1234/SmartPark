from __future__ import annotations

from fastapi import APIRouter, Depends

from .. import db
from ..schemas import OptimizerRequest, OptimizerResponse
from ..services.slot_optimizer import find_best_slot
from .deps import get_current_user

router = APIRouter(prefix="/optimizer", tags=["Slot Optimizer"], dependencies=[Depends(get_current_user)])


@router.post("/recommend", response_model=OptimizerResponse)
def recommend(payload: OptimizerRequest):
    with db.get_connection() as conn:
        return find_best_slot(conn, payload.vehicle_type.value, payload.zone_id)
