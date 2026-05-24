"""
Re-export shared HTTP client factory. Kept for back-compat with platform
clients that import from this path.
"""

from clients._http import get_client  # noqa: F401
