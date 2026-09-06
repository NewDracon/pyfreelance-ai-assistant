from fastapi import FastAPI
from freelance_assistant.api.v1.endpoints import analyze, health
from freelance_assistant.core.database import engine
from freelance_assistant.models.analysis import Base

app = FastAPI(title="Freelance Assistant", version="0.1.0")

app.include_router(analyze.router, prefix="/api/v1", tags=["analysis"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])

@app.on_event("startup")
async def startup():
    # Создание таблиц (если не используется Alembic)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    pass