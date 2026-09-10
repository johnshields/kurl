"""
Auth Validation
Shared input checks for the auth controller (email, password).
"""

from utils.api_result import error_result

MIN_PASSWORD_LENGTH = 8


def normalise_email(value: str | None) -> str:
    return (value or "").strip().lower()


def weak_password_error(password: str) -> dict | None:
    if len(password) < MIN_PASSWORD_LENGTH:
        return error_result("WEAK_PASSWORD", "Password must be at least 8 characters.")
    return None
