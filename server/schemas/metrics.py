from pydantic import BaseModel, Field


class SimulationControl(BaseModel):
    enabled: bool = Field(..., description="True — включить накрутку, False — отключить накрутку")