"""
Dates
Timestamp helpers for D1 (SQLite) comparisons.
"""

from datetime import datetime, timedelta


def iso_days_ago(days: int) -> str:
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
