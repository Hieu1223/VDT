import logging

logger = logging.getLogger("escalation.consumer")


def make_escalation_consumer():
    """Placeholder downstream consumer for escalation.*/reassign.* events.
    Approval/rejection business logic runs synchronously in the API layer
    for immediate admin feedback; this keeps escalation.queue fully wired
    for any future downstream integrations."""

    async def handle(routing_key: str, event: dict):
        logger.info("escalation.queue received %s for ticket %s", routing_key, event.get("ticket_id"))

    return handle
