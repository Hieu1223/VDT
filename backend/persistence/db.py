"""MongoDB connection + small helpers.

Every document stores its primary key as a plain string UUID in the `id`
field, and that same value is used as Mongo's `_id`. This means we never
have to coerce BSON ObjectId <-> str anywhere in the codebase - documents
read from Mongo are already JSON-serializable once `_id` is dropped.
"""
import uuid
from motor.motor_asyncio import AsyncIOMotorClient

from common.config import settings

_client = AsyncIOMotorClient(settings.mongo_url)
db = _client[settings.db_name]


def new_id() -> str:
    return str(uuid.uuid4())


def serialize_doc(doc: dict | None) -> dict | None:
    """Strip Mongo's internal _id before handing a document to a Pydantic model."""
    if doc is None:
        return None
    doc.pop("_id", None)
    return doc


async def create_indexes() -> None:
    await db.users.create_index("username", unique=True)
    await db.users.create_index("role")
    await db.tickets.create_index("requester_id")
    await db.tickets.create_index("assignee_id")
    await db.tickets.create_index("status")
    await db.messages.create_index("ticket_id")
    await db.tags.create_index("name", unique=True)
    await db.events.create_index("created_at")
    await db.events.create_index("ticket_id")
    await db.notifications.create_index("user_id")
    await db.escalation_requests.create_index("ticket_id")
    await db.csat_surveys.create_index("ticket_id", unique=True)
