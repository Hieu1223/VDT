import httpx

from helpdesk_vtech_sdk.exceptions import AuthenticationError


class TokenManager:
    """Handles login and access-token refresh for a Virtual Technician account."""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.access_token: str | None = None
        self.refresh_token: str | None = None

    async def login(self, http_client: httpx.AsyncClient) -> None:
        resp = await http_client.post(
            f"{self.base_url}/api/auth/login",
            json={"username": self.username, "password": self.password},
        )
        if resp.status_code != 200:
            raise AuthenticationError(f"Login failed ({resp.status_code}): {resp.text}")
        data = resp.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]

    async def refresh(self, http_client: httpx.AsyncClient) -> None:
        if not self.refresh_token:
            raise AuthenticationError("No refresh token available; call login() first.")
        resp = await http_client.post(
            f"{self.base_url}/api/auth/refresh",
            json={"refresh_token": self.refresh_token},
        )
        if resp.status_code != 200:
            # Refresh token expired/invalid -- fall back to a full re-login.
            await self.login(http_client)
            return
        data = resp.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]

    @property
    def auth_header(self) -> dict:
        if not self.access_token:
            raise AuthenticationError("Not authenticated; call login() first.")
        return {"Authorization": f"Bearer {self.access_token}"}
