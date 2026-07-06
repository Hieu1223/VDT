"""aio-pika backed implementation of the topic-exchange event bus.

Exchange: helpdesk.events (topic)
Queues declared + bound here so the app is fully wired even before any
consumer attaches. External Virtual Technician SDK processes can bind
their own additional routing keys onto `vtech.queue`.
"""
import json
import logging
from typing import Awaitable, Callable

import aio_pika
from aio_pika import ExchangeType

from common.config import settings
from common.event_bus.base import EventBus

logger = logging.getLogger("event_bus")

QUEUE_BINDINGS = {
    "notification.queue": ["#"],
    "sla.queue": ["sla.*"],
    "assignment.queue": ["ticket.TICKET_CREATED"],
    "escalation.queue": ["escalation.*", "reassign.*"],
    "vtech.queue": ["#"],
}


class RabbitEventBus(EventBus):
    def __init__(self):
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None
        self._consumer_tasks = []

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)
        self._exchange = await self._channel.declare_exchange(
            settings.rabbitmq_exchange, ExchangeType.TOPIC, durable=True
        )
        for queue_name, routing_keys in QUEUE_BINDINGS.items():
            queue = await self._channel.declare_queue(queue_name, durable=True)
            for rk in routing_keys:
                await queue.bind(self._exchange, routing_key=rk)
        logger.info("RabbitMQ event bus connected, exchange=%s", settings.rabbitmq_exchange)

    async def disconnect(self) -> None:
        if self._connection:
            await self._connection.close()

    async def publish(self, routing_key: str, payload: dict) -> None:
        if not self._exchange:
            logger.warning("Event bus not connected, dropping event %s", routing_key)
            return
        body = json.dumps(payload, default=str).encode()
        message = aio_pika.Message(body=body, content_type="application/json", delivery_mode=aio_pika.DeliveryMode.PERSISTENT)
        await self._exchange.publish(message, routing_key=routing_key)

    async def subscribe(self, queue_name: str, callback: Callable[[str, dict], Awaitable[None]]) -> None:
        queue = await self._channel.declare_queue(queue_name, durable=True)

        async def _on_message(message: aio_pika.abc.AbstractIncomingMessage):
            async with message.process():
                try:
                    payload = json.loads(message.body.decode())
                    await callback(message.routing_key, payload)
                except Exception:
                    logger.exception("Error handling message on %s (routing_key=%s)", queue_name, message.routing_key)

        await queue.consume(_on_message)
        logger.info("Subscribed consumer to %s", queue_name)
