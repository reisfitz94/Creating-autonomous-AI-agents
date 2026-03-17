import os
from typing import Optional


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Return an environment variable or default."""
    return os.getenv(name, default)


def require_env(name: str) -> str:
    """Return the value of an env var or raise if missing."""
    val = os.getenv(name)
    if val is None:
        raise RuntimeError(f"environment variable {name} is required")
    return val


def get_bool_env(name: str, default: bool = False) -> bool:
    """Parse common truthy/falsy env-var values safely."""
    raw = os.getenv(name)
    if raw is None:
        return default
    val = raw.strip().lower()
    if val in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if val in {"0", "false", "f", "no", "n", "off"}:
        return False
    return default


def get_int_env(name: str, default: int) -> int:
    """Parse integer env vars with fallback on malformed values."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def get_csv_env(name: str, default: list[str]) -> list[str]:
    """Parse comma-separated values and drop empty entries."""
    raw = os.getenv(name)
    if raw is None:
        return default
    values = [item.strip() for item in raw.split(",")]
    parsed = [item for item in values if item]
    return parsed or default
