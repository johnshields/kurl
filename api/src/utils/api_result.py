"""
API Result
Controller-level result dicts, wrapped into HTTP responses by the routes.
"""


def error_result(code: str, message: str) -> dict:
    return {"status": "error", "code": code, "message": message}
