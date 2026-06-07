"""API settings and shared helpers."""
from __future__ import annotations

import os


class Settings:
    cors_origins: list[str]
    max_upload_mb: int

    def __init__(self) -> None:
        origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
        self.cors_origins = [o.strip() for o in origins.split(",") if o.strip()]
        self.max_upload_mb = int(os.environ.get("MAX_UPLOAD_MB", "50"))


settings = Settings()
