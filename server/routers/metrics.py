from fastapi import APIRouter, Response, Request, status
import asyncio
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter(tags=["simulation"])

from fastapi import APIRouter, Response, Request, status
import asyncio
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from server.schemas.metrics import SimulationControl
from server.services.metrics import simulate_day_and_metrics

router = APIRouter(tags=["simulation"])


@router.post("/simulation/control", status_code=status.HTTP_200_OK)
async def control_simulation(control: SimulationControl, request: Request):
    """
    Включает или выключает симуляцию статистики.
    Если "enabled" = true, запускается фоновая задача, которая каждую минуту
    обновляет метрики.
    Если "enabled" = false, фонова задача отменяется.
    """
    if control.enabled:
        if hasattr(request.app.state, "simulation_task") and not request.app.state.simulation_task.done():
            return {"status": "simulation already enabled"}
        request.app.state.simulation_task = asyncio.create_task(simulate_day_and_metrics())
        return {"status": "simulation enabled"}
    else:
        if hasattr(request.app.state, "simulation_task"):
            request.app.state.simulation_task.cancel()
            del request.app.state.simulation_task
            return {"status": "simulation disabled"}
        else:
            return {"status": "simulation not running"}
@router.get("/metrics", include_in_schema=False)
async def metrics_endpoint():
    """
    Экспортирует метрики в формате Prometheus.
    """
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
