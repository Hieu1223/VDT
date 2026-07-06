"""helpdesk-vtech-sdk

Async Python SDK for building Virtual Technician agents that connect to
the Helpdesk / ITSM platform's `/api/vtech/*` endpoints.
"""
from helpdesk_vtech_sdk.client import VTechClient
from helpdesk_vtech_sdk.exceptions import ApiError, AuthenticationError, HelpdeskSDKError, WebSocketError
from helpdesk_vtech_sdk.models import Attachment, EscalationRequest, LockBlock, Message, SlaBlock, Ticket
from helpdesk_vtech_sdk.ws_listener import WSListener

__all__ = [
    "VTechClient",
    "WSListener",
    "Ticket",
    "Message",
    "Attachment",
    "EscalationRequest",
    "SlaBlock",
    "LockBlock",
    "HelpdeskSDKError",
    "AuthenticationError",
    "ApiError",
    "WebSocketError",
]

__version__ = "0.1.0"
