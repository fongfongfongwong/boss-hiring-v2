"""FastAPI dependency injection helpers."""

from database.db import get_db

__all__ = ["get_db"]
