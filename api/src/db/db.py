"""
DB Client
Thin wrapper around D1 prepared statements.
"""


async def execute(db, sql: str, *params):
    return await db.prepare(sql).bind(*params).run()


async def fetch_all(db, sql: str, *params):
    result = await db.prepare(sql).bind(*params).all()
    if not result:
        return []
    rows = result.results
    rows = rows.to_py() if hasattr(rows, "to_py") else rows
    return rows if rows else []


async def fetch_one(db, sql: str, *params):
    result = await db.prepare(sql).bind(*params).first()
    if not result:
        return None
    return result.to_py() if hasattr(result, "to_py") else result
