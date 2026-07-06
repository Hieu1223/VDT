from pathlib import Path
from typing import Optional

import httpx

from helpdesk_vtech_sdk.auth import TokenManager
from helpdesk_vtech_sdk.exceptions import ApiError
from helpdesk_vtech_sdk.models import Attachment, EscalationRequest, Message, Ticket


class VTechClient:
    """Async HTTP client wrapping every `/api/vtech/*` endpoint for a Virtual
    Technician account. Handles login, token refresh, and 401 auto-retry.

    Example:
        async with VTechClient(base_url="https://helpdesk.example.com", username="bot1", password="...") as client:
            tickets = await client.get_queue()
            await client.send_message(tickets[0].id, "Working on it...")
            await client.resolve(tickets[0].id, "Fixed.")
    """

    def __init__(self, base_url: str, username: str, password: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self._tokens = TokenManager(base_url, username, password)
        self._http = httpx.AsyncClient(timeout=timeout)

    async def connect(self) -> None:
        await self._tokens.login(self._http)

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "VTechClient":
        await self.connect()
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.close()

    @property
    def access_token(self) -> Optional[str]:
        return self._tokens.access_token

    async def _request(self, method: str, path: str, retry: bool = True, **kwargs) -> httpx.Response:
        url = f"{self.base_url}/api/vtech{path}"
        headers = {**self._tokens.auth_header, **kwargs.pop("headers", {})}
        resp = await self._http.request(method, url, headers=headers, **kwargs)

        if resp.status_code == 401 and retry:
            await self._tokens.refresh(self._http)
            return await self._request(method, path, retry=False, **kwargs)

        if resp.status_code >= 400:
            detail = resp.text
            try:
                detail = resp.json().get("detail", detail)
            except Exception:
                pass
            raise ApiError(resp.status_code, str(detail))
        return resp

    # ---- Queue / tickets ----

    async def get_queue(self) -> list[Ticket]:
        resp = await self._request("GET", "/queue")
        return [Ticket(**t) for t in resp.json()]

    async def get_ticket(self, ticket_id: str) -> Ticket:
        resp = await self._request("GET", f"/tickets/{ticket_id}")
        return Ticket(**resp.json())

    async def resolve(self, ticket_id: str, resolution_note: str) -> Ticket:
        resp = await self._request("POST", f"/tickets/{ticket_id}/resolve", json={"resolution_note": resolution_note})
        return Ticket(**resp.json())

    async def reject(self, ticket_id: str, rejection_reason: str) -> Ticket:
        resp = await self._request("POST", f"/tickets/{ticket_id}/reject", json={"rejection_reason": rejection_reason})
        return Ticket(**resp.json())

    async def escalate(self, ticket_id: str, reason: str, suggested_target_id: Optional[str] = None) -> EscalationRequest:
        resp = await self._request(
            "POST", f"/tickets/{ticket_id}/escalate", json={"reason": reason, "suggested_target_id": suggested_target_id}
        )
        return EscalationRequest(**resp.json())

    async def reassign_request(self, ticket_id: str, reason: str, target_technician_id: str) -> EscalationRequest:
        resp = await self._request(
            "POST", f"/tickets/{ticket_id}/reassign-request",
            json={"reason": reason, "target_technician_id": target_technician_id},
        )
        return EscalationRequest(**resp.json())

    # ---- Locking ----

    async def acquire_lock(self, ticket_id: str) -> Ticket:
        resp = await self._request("POST", f"/tickets/{ticket_id}/lock")
        return Ticket(**resp.json())

    async def refresh_lock(self, ticket_id: str) -> Ticket:
        resp = await self._request("POST", f"/tickets/{ticket_id}/lock/refresh")
        return Ticket(**resp.json())

    async def release_lock(self, ticket_id: str) -> Ticket:
        resp = await self._request("DELETE", f"/tickets/{ticket_id}/lock")
        return Ticket(**resp.json())

    # ---- Messages / attachments ----

    async def list_messages(self, ticket_id: str) -> list[Message]:
        resp = await self._request("GET", f"/tickets/{ticket_id}/messages")
        return [Message(**m) for m in resp.json()]

    async def send_message(
        self, ticket_id: str, content: str, reply_to_message_id: Optional[str] = None, attachments: Optional[list[dict]] = None
    ) -> Message:
        payload = {"content": content, "reply_to_message_id": reply_to_message_id, "attachments": attachments or []}
        resp = await self._request("POST", f"/tickets/{ticket_id}/messages", json=payload)
        return Message(**resp.json())

    async def upload_attachment(self, ticket_id: str, file_path: str) -> Attachment:
        path = Path(file_path)
        with open(path, "rb") as f:
            files = {"file": (path.name, f)}
            resp = await self._request("POST", f"/tickets/{ticket_id}/messages/upload", files=files)
        return Attachment(**resp.json())
