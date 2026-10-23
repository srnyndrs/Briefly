from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


class StatusResponse(BaseModel):
    status: str
