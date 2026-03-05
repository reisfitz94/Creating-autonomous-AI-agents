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
