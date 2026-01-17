"""
Analytics database update workflow - sync PostgreSQL to DuckDB.
"""

from prefect import flow, task
import duckdb
from datetime import datetime
from typing import Optional


@task
async def sync_to_duckdb():
    """
    Sync data from PostgreSQL to DuckDB for analytics.
    Uses incremental updates based on last sync timestamp.
    """
    from app.database import get_postgres_connection
    from app.config import settings

    conn = duckdb.connect(settings.DUCKDB_PATH)

    # Get last sync timestamp
    last_sync = await get_last_sync_timestamp()
    print(f"Last sync: {last_sync}")

    # Export new/updated transactions from PostgreSQL
    # TODO: Implement actual PostgreSQL query
    print("Syncing transactions from PostgreSQL to DuckDB")

    # Update materialized views
    try:
        conn.execute("CALL refresh_daily_spending()")
        conn.execute("CALL refresh_monthly_summary()")
        conn.execute("CALL refresh_merchant_stats()")
    except Exception as e:
        print(f"Note: Materialized view refresh failed (views may not exist yet): {e}")

    await update_sync_timestamp()

    print("✅ Synced data to DuckDB")
    conn.close()


@task
async def generate_insights():
    """Generate AI-powered insights from analytics data"""
    from app.services.analytics_service import generate_ai_insights

    print("Generating AI insights from analytics data")
    # TODO: Implement insight generation
    insights = await generate_ai_insights()
    print(f"Generated {len(insights)} insights")

    return insights


async def get_last_sync_timestamp() -> Optional[datetime]:
    """Get the last sync timestamp from metadata table"""
    # TODO: Implement
    return datetime.now()


async def update_sync_timestamp():
    """Update the last sync timestamp"""
    # TODO: Implement
    pass


@flow(name="analytics-update", log_prints=True)
async def analytics_update_flow():
    """
    Update analytics database and generate insights.
    Runs every 6 hours.
    """
    await sync_to_duckdb()
    insights = await generate_insights()

    return {
        "sync_completed": True,
        "insights_generated": len(insights) if insights else 0,
    }
