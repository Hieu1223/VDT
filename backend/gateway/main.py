import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from common.config import ROOT_DIR, settings
from common.errors import register_exception_handlers
from common.event_bus.rabbit_bus import RabbitEventBus
from common.presence import presence
from common.redis_client import init as redis_init, disconnect as redis_disconnect
from common.security import decode_token
from common.ws.manager import manager as ws_manager
from gateway.middleware import setup_cors
from gateway.router_registry import api_router
from gateway.seed import run_seed
from modules.assignment.consumer import make_assignment_consumer
from modules.escalation.consumer import make_escalation_consumer
from modules.jobs.scheduler import start_background_jobs
from modules.notifications.consumer import make_notification_consumer
from modules.sla.consumer import make_sla_consumer
from persistence.db import create_indexes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")

UPLOAD_ROOT = ROOT_DIR / settings.upload_dir
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_indexes()
    await run_seed()

    bus = RabbitEventBus()
    await bus.connect()
    app.state.event_bus = bus

    await bus.subscribe("notification.queue", make_notification_consumer())
    await bus.subscribe("assignment.queue", make_assignment_consumer(bus))
    await bus.subscribe("sla.queue", make_sla_consumer())
    await bus.subscribe("escalation.queue", make_escalation_consumer())

    await redis_init()
    app.state.background_tasks = start_background_jobs(bus)
    logger.info("Helpdesk backend startup complete")

    yield

    for task in app.state.background_tasks:
        task.cancel()
    await bus.disconnect()
    await redis_disconnect()


app = FastAPI(title="Helpdesk / ITSM API", lifespan=lifespan)
setup_cors(app)
register_exception_handlers(app)
app.include_router(api_router)
app.mount("/uploads", StaticFiles(directory=str(ROOT_DIR / "uploads")), name="uploads")


@app.get("/api")
async def root():
    return {"message": "Helpdesk / ITSM API"}


@app.websocket("/api/ws")
async def ws_endpoint(websocket: WebSocket, token: str):
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("invalid token type")
    except Exception:
        await websocket.close(code=4401)
        return

    user_id, role = payload["sub"], payload.get("role", "")
    await presence.touch(user_id)
    await ws_manager.connect(user_id, role, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)
        if not ws_manager.is_online(user_id):
            await presence.mark_offline(user_id)
    except Exception:
        ws_manager.disconnect(user_id, websocket)
        if not ws_manager.is_online(user_id):
            await presence.mark_offline(user_id)
