"""Priority matrix + SLA policy seed data. Idempotent on startup."""
from common.enums import Level, Priority
from persistence.db import db

# (impact, urgency) -> priority
PRIORITY_MATRIX = {
    (Level.HIGH, Level.HIGH): Priority.P1,
    (Level.HIGH, Level.MEDIUM): Priority.P1,
    (Level.HIGH, Level.LOW): Priority.P2,
    (Level.MEDIUM, Level.HIGH): Priority.P2,
    (Level.MEDIUM, Level.MEDIUM): Priority.P3,
    (Level.MEDIUM, Level.LOW): Priority.P3,
    (Level.LOW, Level.HIGH): Priority.P3,
    (Level.LOW, Level.MEDIUM): Priority.P4,
    (Level.LOW, Level.LOW): Priority.P4,
}

DEFAULT_SLA_POLICIES = {
    Priority.P1: {"first_response_minutes": 15, "resolve_minutes": 240},
    Priority.P2: {"first_response_minutes": 30, "resolve_minutes": 480},
    Priority.P3: {"first_response_minutes": 60, "resolve_minutes": 1440},
    Priority.P4: {"first_response_minutes": 120, "resolve_minutes": 2880},
}


def resolve_priority(impact: str, urgency: str) -> str:
    return PRIORITY_MATRIX.get((Level(impact), Level(urgency)), Priority.P3).value


async def seed_priority_matrix_and_sla() -> None:
    for (impact, urgency), priority in PRIORITY_MATRIX.items():
        doc_id = f"{impact.value}_{urgency.value}"
        await db.priority_matrix.update_one(
            {"id": doc_id},
            {"$set": {"id": doc_id, "_id": doc_id, "impact": impact.value, "urgency": urgency.value, "priority": priority.value}},
            upsert=True,
        )
    for priority, policy in DEFAULT_SLA_POLICIES.items():
        await db.sla_policies.update_one(
            {"id": priority.value},
            {"$set": {"id": priority.value, "_id": priority.value, "priority": priority.value, **policy}},
            upsert=True,
        )


async def get_sla_policy(priority: str) -> dict:
    policy = await db.sla_policies.find_one({"id": priority})
    if not policy:
        policy = {"priority": priority, **DEFAULT_SLA_POLICIES[Priority(priority)]}
    return policy
