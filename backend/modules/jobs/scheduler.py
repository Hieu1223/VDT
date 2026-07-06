import asyncio
import logging

from common.config import settings
from modules.locks.service import janitor_sweep
from modules.sla.job import run_sla_check

logger = logging.getLogger("jobs.scheduler")


async def sla_checker_loop(bus):
    while True:
        try:
            await run_sla_check(bus)
        except Exception:
            logger.exception("SLA checker iteration failed")
        await asyncio.sleep(settings.sla_check_interval_seconds)


async def lock_janitor_loop(bus):
    while True:
        try:
            released = await janitor_sweep(bus)
            if released:
                logger.info("Lock janitor released %d expired lock(s)", released)
        except Exception:
            logger.exception("Lock janitor iteration failed")
        await asyncio.sleep(settings.lock_janitor_interval_seconds)


def start_background_jobs(bus) -> list[asyncio.Task]:
    return [
        asyncio.create_task(sla_checker_loop(bus)),
        asyncio.create_task(lock_janitor_loop(bus)),
    ]
