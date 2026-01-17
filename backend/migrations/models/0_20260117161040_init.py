from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" UUID NOT NULL PRIMARY KEY,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "password_hash" VARCHAR(255) NOT NULL,
    "full_name" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_users_email_133a6f" ON "users" ("email");
COMMENT ON TABLE "users" IS 'User account model.';
CREATE TABLE IF NOT EXISTS "accounts" (
    "id" UUID NOT NULL PRIMARY KEY,
    "account_type" VARCHAR(50) NOT NULL,
    "institution" VARCHAR(255),
    "account_name" VARCHAR(255) NOT NULL,
    "account_number_last4" VARCHAR(4),
    "currency" VARCHAR(3) NOT NULL DEFAULT 'USD',
    "current_balance" DECIMAL(15,2),
    "available_balance" DECIMAL(15,2),
    "credit_limit" DECIMAL(15,2),
    "is_active" BOOL NOT NULL DEFAULT True,
    "last_synced_at" TIMESTAMPTZ,
    "sync_error" TEXT,
    "meta" JSONB NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "accounts" IS 'Bank account model.';
CREATE TABLE IF NOT EXISTS "budgets" (
    "id" UUID NOT NULL PRIMARY KEY,
    "category" VARCHAR(100) NOT NULL,
    "subcategory" VARCHAR(100),
    "amount" DECIMAL(15,2) NOT NULL,
    "period" VARCHAR(20) NOT NULL,
    "start_date" DATE NOT NULL,
    "end_date" DATE,
    "rollover_enabled" BOOL NOT NULL DEFAULT False,
    "alert_threshold" DOUBLE PRECISION NOT NULL DEFAULT 0.8,
    "is_active" BOOL NOT NULL DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_budgets_user_id_70b9b5" UNIQUE ("user_id", "category", "subcategory", "period", "start_date")
);
COMMENT ON TABLE "budgets" IS 'Budget model.';
CREATE TABLE IF NOT EXISTS "categorization_rules" (
    "id" UUID NOT NULL PRIMARY KEY,
    "pattern_type" VARCHAR(50) NOT NULL,
    "pattern_value" TEXT NOT NULL,
    "category" VARCHAR(100) NOT NULL,
    "subcategory" VARCHAR(100),
    "confidence_score" DOUBLE PRECISION NOT NULL DEFAULT 1,
    "usage_count" INT NOT NULL DEFAULT 0,
    "last_used_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_categorizat_user_id_66d0fd" UNIQUE ("user_id", "pattern_type", "pattern_value")
);
COMMENT ON TABLE "categorization_rules" IS 'AI categorization rules model.';
CREATE TABLE IF NOT EXISTS "sync_jobs" (
    "id" UUID NOT NULL PRIMARY KEY,
    "job_type" VARCHAR(50) NOT NULL,
    "prefect_flow_run_id" VARCHAR(255),
    "status" VARCHAR(50) NOT NULL,
    "stage" VARCHAR(50),
    "progress" JSONB,
    "started_at" TIMESTAMPTZ,
    "completed_at" TIMESTAMPTZ,
    "error_message" TEXT,
    "meta" JSONB NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "sync_jobs" IS 'Processing job tracking model.';
CREATE TABLE IF NOT EXISTS "transactions" (
    "id" UUID NOT NULL PRIMARY KEY,
    "transaction_date" DATE NOT NULL,
    "post_date" DATE,
    "amount" DECIMAL(15,2) NOT NULL,
    "currency" VARCHAR(3) NOT NULL DEFAULT 'USD',
    "description" TEXT NOT NULL,
    "merchant_name" VARCHAR(255),
    "category" VARCHAR(100),
    "subcategory" VARCHAR(100),
    "tags" JSONB NOT NULL,
    "is_recurring" BOOL NOT NULL DEFAULT False,
    "recurring_group_id" UUID,
    "confidence_score" DOUBLE PRECISION,
    "ai_categorized" BOOL NOT NULL DEFAULT False,
    "user_verified" BOOL NOT NULL DEFAULT False,
    "notes" TEXT,
    "meta" JSONB NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "account_id" UUID NOT NULL REFERENCES "accounts" ("id") ON DELETE CASCADE,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_transaction_transac_8db3ee" ON "transactions" ("transaction_date");
CREATE INDEX IF NOT EXISTS "idx_transaction_account_c046e9" ON "transactions" ("account_id", "transaction_date");
CREATE INDEX IF NOT EXISTS "idx_transaction_user_id_b701d8" ON "transactions" ("user_id", "transaction_date");
COMMENT ON TABLE "transactions" IS 'Financial transaction model.';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)
