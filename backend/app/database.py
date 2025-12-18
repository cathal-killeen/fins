"""
Database connection and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.config import settings
import duckdb

# PostgreSQL for transactional data
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependency to get DB session
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# DuckDB for analytics
def get_duckdb_connection():
    """Get DuckDB connection for analytics queries."""
    return duckdb.connect(settings.DUCKDB_PATH)


def get_postgres_connection():
    """Get raw PostgreSQL connection."""
    import psycopg2
    # Parse DATABASE_URL to get connection params
    # This is a simple implementation - consider using urllib.parse for production
    return psycopg2.connect(settings.DATABASE_URL)
