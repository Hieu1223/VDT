"""Centralized application configuration read from environment variables."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


class Settings:
    mongo_url: str = os.environ["MONGO_URL"]
    db_name: str = os.environ["DB_NAME"]
    cors_origins: str = os.environ.get("CORS_ORIGINS", "*")

    jwt_secret: str = os.environ["JWT_SECRET"]
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_minutes: int = int(os.environ.get("JWT_ACCESS_TTL_MINUTES", "30"))
    jwt_refresh_ttl_days: int = int(os.environ.get("JWT_REFRESH_TTL_DAYS", "7"))

    admin_email: str = os.environ.get("ADMIN_EMAIL", "admin@helpdesk.io")
    admin_password: str = os.environ.get("ADMIN_PASSWORD", "Admin@12345")
    admin_username: str = os.environ.get("ADMIN_USERNAME", "admin")

    seed_tech_human_username: str = os.environ.get("SEED_TECH_HUMAN_USERNAME", "tech.human")
    seed_tech_human_password: str = os.environ.get("SEED_TECH_HUMAN_PASSWORD", "Tech@12345")
    seed_tech_virtual_username: str = os.environ.get("SEED_TECH_VIRTUAL_USERNAME", "tech.virtual")
    seed_tech_virtual_password: str = os.environ.get("SEED_TECH_VIRTUAL_PASSWORD", "VTech@12345")
    seed_employee_username: str = os.environ.get("SEED_EMPLOYEE_USERNAME", "employee.demo")
    seed_employee_password: str = os.environ.get("SEED_EMPLOYEE_PASSWORD", "Employee@12345")

    rabbitmq_url: str = os.environ.get("RABBITMQ_URL", "amqp://helpdesk:helpdesk@localhost:5672/")
    rabbitmq_exchange: str = os.environ.get("RABBITMQ_EXCHANGE", "helpdesk.events")

    redis_url: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    upload_dir: str = os.environ.get("UPLOAD_DIR", "uploads/rooms")

    lock_ttl_seconds: int = 180
    sla_check_interval_seconds: int = 30
    lock_janitor_interval_seconds: int = 30
    sla_near_breach_ratio: float = 0.8
    reassignment_check_interval_seconds: int = 20


settings = Settings()
