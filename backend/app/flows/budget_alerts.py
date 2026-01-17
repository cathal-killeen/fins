"""
Budget monitoring and alert workflow.
"""

from prefect import flow, task
from typing import List, Dict, Any


@task
async def check_budget_status(user_id: str) -> List[Dict[str, Any]]:
    """Check all active budgets for a user"""
    from app.services.analytics_service import get_active_budgets, get_period_spending

    budgets = await get_active_budgets(user_id)
    alerts = []

    for budget in budgets:
        spent = await get_period_spending(
            user_id=user_id, category=budget["category"], period=budget["period"]
        )

        percentage = spent / budget["amount"] if budget["amount"] > 0 else 0

        if percentage >= budget.get("alert_threshold", 0.8):
            alerts.append(
                {
                    "budget_id": budget["id"],
                    "category": budget["category"],
                    "spent": spent,
                    "budget": budget["amount"],
                    "percentage": percentage,
                }
            )

    return alerts


@task
async def send_alert_notifications(user_id: str, alerts: List[Dict[str, Any]]):
    """Send budget alert notifications to user"""
    if not alerts:
        return

    # TODO: Implement notification service (email, push, in-app)
    print(f"Sending {len(alerts)} budget alerts to user {user_id}")
    for alert in alerts:
        print(
            f"  - {alert['category']}: ${alert['spent']:.2f} / ${alert['budget']:.2f} ({alert['percentage'] * 100:.1f}%)"
        )

    return len(alerts)


async def get_all_users() -> List[Dict[str, Any]]:
    """Get all users in the system"""
    # TODO: Implement database query
    return []


@flow(name="budget-alerts", log_prints=True)
async def budget_alerts_flow():
    """
    Check budgets and send alerts.
    Runs daily.
    """
    users = await get_all_users()

    if not users:
        print("No users to check")
        return {"total_users": 0, "alerts_sent": 0}

    total_alerts = 0

    for user in users:
        alerts = await check_budget_status(user["id"])
        if alerts:
            sent = await send_alert_notifications(user["id"], alerts)
            total_alerts += sent
            print(f"Sent {sent} alerts to user {user['id']}")

    print(f"✅ Sent {total_alerts} total budget alerts")

    return {"total_users": len(users), "alerts_sent": total_alerts}
