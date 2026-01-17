"""
Database configuration and connections.
"""

import duckdb
from app.config import settings

TORTOISE_ORM = {
    "connections": {"default": settings.DATABASE_URL},
    "apps": {
        "models": {
            "models": ["app.models"],
            "default_connection": "default",
        }
    },
}


def get_duckdb_connection():
    """Get DuckDB connection for analytics queries."""
    return duckdb.connect(settings.DUCKDB_PATH)
