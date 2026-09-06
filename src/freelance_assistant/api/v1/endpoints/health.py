from fastapi import APIRouter, Depends
from freelance_assistant.core.config import settings
from pydantic import BaseModel

router = APIRouter()

class HealthStatus(BaseModel):
    status: str

@router.get("/health", response_model=HealthStatus)
async def health_check():
    return HealthStatus(status="ok")