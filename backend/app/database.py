"""
Database configuration and connections.
"""

import duckdb
from app.config import settings


def _normalize_db_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgres://" + url[len("postgresql://") :]
    return url

TORTOISE_ORM = {
    "connections": {"default": _normalize_db_url(settings.DATABASE_URL)},
    "apps": {
        "models": {
            "models": ["app.models", "fastapi_admin.models"],
            "default_connection": "default",
        }
    },
}


def get_duckdb_connection():
    """Get DuckDB connection for analytics queries."""
    return duckdb.connect(settings.DUCKDB_PATH)
