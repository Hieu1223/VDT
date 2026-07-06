"""Supervisor entrypoint shim.

Supervisor runs `uvicorn server:app` from /app/backend. The real
application lives in gateway/main.py per the modular backend layout;
this file just re-exports it so the process manager config never needs
to change.
"""
from gateway.main import app  # noqa: F401
