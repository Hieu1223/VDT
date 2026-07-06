"""Abstract event bus contract."""
from abc import ABC, abstractmethod
from typing import Awaitable, Callable


class EventBus(ABC):
    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    async def publish(self, routing_key: str, payload: dict) -> None: ...

    @abstractmethod
    async def subscribe(self, queue_name: str, callback: Callable[[str, dict], Awaitable[None]]) -> None: ...
