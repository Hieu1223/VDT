import logging

from modules.assignment.service import assign_ticket_automatically

logger = logging.getLogger("assignment.consumer")


def make_assignment_consumer(bus):
    async def handle(routing_key: str, event: dict):
        if routing_key == "ticket.TICKET_CREATED":
            ticket_id = event.get("ticket_id")
            if ticket_id:
                await assign_ticket_automatically(bus, ticket_id)

    return handle
