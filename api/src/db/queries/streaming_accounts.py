"""
Streaming Account Queries
SQL builder for the per-provider linked-OAuth-account tables. Every table
shares one shape; only the table name and provider-id column differ.
"""

from types import SimpleNamespace


def account_queries(table: str, id_column: str) -> SimpleNamespace:
    return SimpleNamespace(
        UPSERT=f"""
    INSERT INTO {table}
        (user_uid, {id_column}, display_name, access_token, refresh_token, expires_at, scope)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_uid) DO UPDATE SET
        {id_column} = excluded.{id_column},
        display_name = excluded.display_name,
        access_token = excluded.access_token,
        refresh_token = excluded.refresh_token,
        expires_at = excluded.expires_at,
        scope = excluded.scope
""",
        GET_BY_USER_UID=f"SELECT * FROM {table} WHERE user_uid = ?",
        GET_BY_PROVIDER_ID=f"SELECT * FROM {table} WHERE {id_column} = ?",
        DELETE_BY_USER_UID=f"DELETE FROM {table} WHERE user_uid = ?",
    )
