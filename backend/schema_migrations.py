from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


USER_COLUMNS = {
    "city": "VARCHAR",
    "country": "VARCHAR",
    "latitude": "FLOAT",
    "longitude": "FLOAT",
    "notification_opt_in": "BOOLEAN NOT NULL DEFAULT 0",
}

INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS ix_food_logs_user_consumed_at ON food_logs (user_id, consumed_at)",
    "CREATE INDEX IF NOT EXISTS ix_food_logs_user_created_at ON food_logs (user_id, created_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_weekly_diet_plans_user_week_start ON weekly_diet_plans (user_id, week_start)",
    "CREATE INDEX IF NOT EXISTS ix_notification_events_user_scheduled ON notification_events (user_id, scheduled_for)",
    "CREATE INDEX IF NOT EXISTS ix_notification_events_user_read ON notification_events (user_id, is_read)",
]


def run_startup_migrations(engine: Engine) -> None:
    inspector = inspect(engine)
    if "users" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("users")}
        with engine.begin() as connection:
            for column_name, column_sql in USER_COLUMNS.items():
                if column_name not in columns:
                    connection.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_sql}"))

            for statement in INDEX_STATEMENTS:
                connection.execute(text(statement))
