"""
Deploy Prefect flows to Prefect Cloud.

Usage:
    python deploy_flows.py
"""
import asyncio
from app.flows.sync_accounts import daily_account_sync_flow
from app.flows.categorize_transactions import categorization_flow
from app.flows.update_analytics import analytics_update_flow
from app.flows.recurring_detection import recurring_detection_flow
from app.flows.budget_alerts import budget_alerts_flow


async def deploy_all_flows():
    """Deploy all Prefect flows with schedules."""

    print("Deploying Prefect flows...")

    # Deploy daily account sync (runs at 2 AM daily)
    print("\n1. Deploying daily-account-sync...")
    await daily_account_sync_flow.serve(
        name="daily-account-sync",
        cron="0 2 * * *",
        tags=["sync", "production"],
        description="Sync transactions from bank APIs daily"
    )

    # Deploy AI categorization (runs every 6 hours)
    print("2. Deploying ai-categorization...")
    await categorization_flow.serve(
        name="ai-categorization",
        cron="0 */6 * * *",
        tags=["ai", "production"],
        description="Categorize transactions using AI"
    )

    # Deploy analytics update (runs every 6 hours)
    print("3. Deploying analytics-update...")
    await analytics_update_flow.serve(
        name="analytics-update",
        cron="0 */6 * * *",
        tags=["analytics", "production"],
        description="Sync data to DuckDB for analytics"
    )

    # Deploy recurring detection (runs weekly on Sundays at 3 AM)
    print("4. Deploying recurring-detection...")
    await recurring_detection_flow.serve(
        name="recurring-detection",
        cron="0 3 * * 0",
        tags=["ml", "production"],
        description="Detect recurring transaction patterns"
    )

    # Deploy budget alerts (runs daily at 8 AM)
    print("5. Deploying budget-alerts...")
    await budget_alerts_flow.serve(
        name="budget-alerts",
        cron="0 8 * * *",
        tags=["alerts", "production"],
        description="Check budgets and send alerts"
    )

    print("\n✅ All flows deployed successfully!")
    print("\nNext steps:")
    print("1. Start a Prefect worker: prefect worker start --pool default")
    print("2. View flows in Prefect Cloud UI")
    print("3. Trigger flows manually or wait for scheduled runs")


if __name__ == "__main__":
    asyncio.run(deploy_all_flows())
