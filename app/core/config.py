from __future__ import annotations

import os


class Settings:
    """Application configuration loaded from environment variables with sensible defaults."""

    # ESP32 / relay
    esp32_host: str = os.getenv("ESP32_HOST", "192.168.1.100")
    esp32_port: int = int(os.getenv("ESP32_PORT", "80"))
    esp32_timeout: float = float(os.getenv("ESP32_TIMEOUT", "3.0"))
    demo_mode: bool = os.getenv("DEMO_MODE", "false").lower() in ("1", "true", "yes")

    # Tables
    num_tables: int = int(os.getenv("NUM_TABLES", "8"))
    default_rate_per_hour: float = float(os.getenv("RATE_PER_HOUR", "20.0"))

    # Database paths
    db_path: str = os.getenv("DB_PATH", "pool.db")
    auth_db_path: str = os.getenv("AUTH_DB_PATH", "auth.db")

    # CORS / frontend URL (comma-separated)
    cors_origins: list[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
        if o.strip()
    ]

    # Default owner credentials (only used when no users exist)
    # IMPORTANT: Set DEFAULT_OWNER_PASSWORD via environment variable before first run.
    # The built-in default is intentionally weak — change it immediately after setup.
    default_owner_name: str = os.getenv("DEFAULT_OWNER_NAME", "Owner")
    default_owner_password: str = os.getenv("DEFAULT_OWNER_PASSWORD", "changeme1")


settings = Settings()
