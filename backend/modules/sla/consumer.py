import logging

logger = logging.getLogger("sla.consumer")


def make_sla_consumer():
    """Placeholder downstream consumer for sla.* events (e.g. audit logging,
    future integrations). The events collection already persists every SLA
    event for the Timeline/Monitor views; this keeps sla.queue fully wired."""

    async def handle(routing_key: str, event: dict):
        logger.info("sla.queue received %s for ticket %s", routing_key, event.get("ticket_id"))

    return handle
