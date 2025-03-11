from fastapi import APIRouter
import numpy as np

router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get("/get_hourly_reservations")
async def get_hourly_reservations():
    hourly_reservations = np.random.binomial(n=24, p=0.8, size=24)
    return hourly_reservations.tolist()
