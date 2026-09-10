import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from freelance_assistant.api.v1.endpoints import analyze, health
from freelance_assistant.services.notification_listener import listen_for_new_orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Стартуем слушателя в фоне
    listener_task = asyncio.create_task(listen_for_new_orders())
    print("[app] Notification listener started")
    try:
        yield
    finally:
        # Аккуратно останавливаем при выключении
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass
        print("[app] Notification listener stopped")


app = FastAPI(
    title="Freelance Assistant",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(analyze.router, prefix="/api/v1", tags=["analysis"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])