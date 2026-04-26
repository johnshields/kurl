"""
DB Client
Thin wrapper around D1 prepared statements.
"""


async def execute(db, sql: str, *params):
    return await db.prepare(sql).bind(*params).run()


async def fetch_one(db, sql: str, *params):
    row = await db.prepare(sql).bind(*params).first()
    if not row:
        return None
    return row.to_py() if hasattr(row, "to_py") else row


async def fetch_all(db, sql: str, *params):
    result = await db.prepare(sql).bind(*params).all()
    if not result:
        return []
    rows = result.results.to_py()
    return rows if rows else []
