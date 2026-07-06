from starlette.middleware.cors import CORSMiddleware

from common.config import settings


def setup_cors(app) -> None:
    origins = [o.strip() for o in settings.cors_origins.split(",")] if settings.cors_origins != "*" else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
