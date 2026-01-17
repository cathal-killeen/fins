"""
FastAPI-Admin configuration and resources.
"""

import aioredis
from fastapi_admin.app import app as admin_app
from fastapi_admin.providers.login import UsernamePasswordProvider
from fastapi_admin.resources import Model
from fastapi_admin.utils import hash_password
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from app.config import settings
from app.models import (
    Account,
    Admin,
    Budget,
    CategorizationRule,
    SyncJob,
    Transaction,
    User,
)


@admin_app.register
class UserResource(Model):
    label = "Users"
    model = User


@admin_app.register
class AccountResource(Model):
    label = "Accounts"
    model = Account


@admin_app.register
class TransactionResource(Model):
    label = "Transactions"
    model = Transaction


@admin_app.register
class BudgetResource(Model):
    label = "Budgets"
    model = Budget


@admin_app.register
class CategorizationRuleResource(Model):
    label = "Categorization Rules"
    model = CategorizationRule


@admin_app.register
class SyncJobResource(Model):
    label = "Sync Jobs"
    model = SyncJob


@admin_app.get("/")
async def admin_root(request: Request):
    root_path = request.scope.get("root_path", "")
    has_admin = await Admin.all().limit(1).exists()
    if not has_admin:
        return RedirectResponse(url=f"{root_path}/init", status_code=HTTP_303_SEE_OTHER)
    if not request.state.admin:
        return RedirectResponse(url=f"{root_path}/login", status_code=HTTP_303_SEE_OTHER)
    for resource in request.app.resources:
        if issubclass(resource, Model):
            model_name = resource.model.__name__.lower()
            return RedirectResponse(
                url=f"{root_path}/{model_name}/list",
                status_code=HTTP_303_SEE_OTHER,
            )
    return RedirectResponse(url=f"{root_path}/login", status_code=HTTP_303_SEE_OTHER)


async def _ensure_default_admin() -> None:
    if not settings.ADMIN_USERNAME or not settings.ADMIN_PASSWORD:
        return

    existing = await Admin.get_or_none(username=settings.ADMIN_USERNAME)
    if existing:
        return

    await Admin.create(
        username=settings.ADMIN_USERNAME,
        password=hash_password(settings.ADMIN_PASSWORD),
    )


async def init_admin() -> None:
    redis = await aioredis.create_redis_pool(
        settings.REDIS_URL,
        encoding="utf-8",
    )
    await admin_app.configure(
        logo_url="https://fastapi-admin.github.io/logo.png",
        providers=[
            UsernamePasswordProvider(
                admin_model=Admin,
                login_logo_url="https://fastapi-admin.github.io/logo.png",
            )
        ],
        admin_path="/admin",
        redis=redis,
    )
    await _ensure_default_admin()
