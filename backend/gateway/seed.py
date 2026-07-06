"""Idempotent startup seed: admin, human technician, virtual technician,
demo employee + priority matrix / SLA policies.
"""
import logging
from datetime import datetime, timezone

from common.config import settings
from common.enums import UserRole, UserStatus
from common.security import hash_password, verify_password
from modules.tickets.sla_seed import seed_priority_matrix_and_sla
from persistence.db import db, new_id

logger = logging.getLogger("seed")

SEED_USERS = [
    (settings.admin_username, settings.admin_password, "Admin User", UserRole.ADMIN.value),
    (settings.seed_tech_human_username, settings.seed_tech_human_password, "Human Technician", UserRole.TECHNICIAN_HUMAN.value),
    (settings.seed_tech_virtual_username, settings.seed_tech_virtual_password, "Virtual Technician Bot", UserRole.TECHNICIAN_VIRTUAL.value),
    (settings.seed_employee_username, settings.seed_employee_password, "Demo Employee", UserRole.EMPLOYEE.value),
]


async def seed_users() -> None:
    now = datetime.now(timezone.utc)
    for username, password, full_name, role in SEED_USERS:
        existing = await db.users.find_one({"username": username})
        if existing is None:
            user = {
                "id": new_id(), "username": username, "password_hash": hash_password(password),
                "full_name": full_name, "email": f"{username}@helpdesk.io", "role": role,
                "status": UserStatus.ACTIVE.value, "online": False,
                "created_at": now, "updated_at": now, "last_login_at": None,
            }
            doc = dict(user)
            doc["_id"] = user["id"]
            await db.users.insert_one(doc)
            logger.info("Seeded user %s (%s)", username, role)
        elif not verify_password(password, existing["password_hash"]):
            await db.users.update_one({"username": username}, {"$set": {"password_hash": hash_password(password)}})


async def run_seed() -> None:
    await seed_priority_matrix_and_sla()
    await seed_users()
