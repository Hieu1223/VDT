class HelpdeskSDKError(Exception):
    """Base exception for all helpdesk-vtech-sdk errors."""


class AuthenticationError(HelpdeskSDKError):
    """Raised when login or token refresh fails."""


class ApiError(HelpdeskSDKError):
    """Raised for non-2xx API responses (after auth-retry has been exhausted)."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API error {status_code}: {detail}")


class WebSocketError(HelpdeskSDKError):
    """Raised when the real-time WebSocket listener fails to connect or drops unexpectedly."""
