import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    petkit_username: str = field(default_factory=lambda: os.environ["PETKIT_USERNAME"])
    petkit_password: str = field(default_factory=lambda: os.environ["PETKIT_PASSWORD"])
    petkit_region: str = field(default_factory=lambda: os.getenv("PETKIT_REGION", "US"))
    petkit_timezone: str = field(
        default_factory=lambda: os.getenv("PETKIT_TIMEZONE", "America/New_York")
    )
    poll_interval_seconds: int = field(
        default_factory=lambda: int(os.getenv("POLL_INTERVAL_SECONDS", "120"))
    )
    db_path: Path = field(
        default_factory=lambda: Path(os.getenv("DB_PATH", "simbakit.db"))
    )
    web_host: str = field(default_factory=lambda: os.getenv("WEB_HOST", "127.0.0.1"))
    web_port: int = field(default_factory=lambda: int(os.getenv("WEB_PORT", "8585")))
