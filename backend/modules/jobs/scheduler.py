import asyncio
import logging

from common.config import settings
from common.presence import presence
from common.ws.manager import manager as ws_manager
from modules.assignment.service import reassign_offline_tickets
from modules.locks.service import janitor_sweep
from modules.sla.job import run_sla_check
from persistence.db import db

logger = logging.getLogger("jobs.scheduler")

PRESENCE_SWEEP_INTERVAL_SECONDS = 10


async def sla_checker_loop(bus):
    while True:
        try:
            await run_sla_check(bus)
        except Exception:
            logger.exception("SLA checker iteration failed")
        await asyncio.sleep(settings.sla_check_interval_seconds)


async def reassignment_loop(bus):
    while True:
        try:
            moved = await reassign_offline_tickets(bus)
            if moved:
                logger.info("Reassignment sweep moved %d ticket(s) off offline technicians", moved)
        except Exception:
            logger.exception("Reassignment sweep iteration failed")
        await asyncio.sleep(settings.reassignment_check_interval_seconds)


async def lock_janitor_loop(bus):
    while True:
        try:
            released = await janitor_sweep(bus)
            if released:
                logger.info("Lock janitor released %d expired lock(s)", released)
        except Exception:
            logger.exception("Lock janitor iteration failed")
        await asyncio.sleep(settings.lock_janitor_interval_seconds)


async def presence_janitor_loop():
    while True:
        try:
            expired = presence.sweep_expired()
            for user_id in expired:
                user = await db.users.find_one({"id": user_id}, {"username": 1})
                await ws_manager.broadcast_to_roles(
                    ["admin"], {"kind": "presence", "data": {"user_id": user_id, "username": user.get("username") if user else None, "online": False}}
                )
        except Exception:
            logger.exception("Presence janitor iteration failed")
        await asyncio.sleep(PRESENCE_SWEEP_INTERVAL_SECONDS)


def start_background_jobs(bus) -> list[asyncio.Task]:
    return [
        asyncio.create_task(sla_checker_loop(bus)),
        asyncio.create_task(lock_janitor_loop(bus)),
        asyncio.create_task(presence_janitor_loop()),
        asyncio.create_task(reassignment_loop(bus)),
    ]
