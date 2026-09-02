"""
Tests for api.middleware.rate_limit -- sliding-window limiter with a
separate bucket for analytics events so they don't compete with writes.
"""

import json
import sys
from types import ModuleType
from unittest.mock import patch

import pytest


class _StubResponse:
    """Stand-in for workers.Response -- captures body/status like the real one."""

    def __init__(self, body=None, status=200, headers=None):
        self.body = body
        self.status = status
        self.headers = headers or {}


# `workers` only exists inside the Pyodide/Workers runtime. response.py
# imports it for json_error's Response wrapper -- stub it before import.
_stub = ModuleType("workers")
_stub.Response = _StubResponse
sys.modules.setdefault("workers", _stub)

from api.middleware.rate_limit import _event_requests, _requests, check_rate_limit  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_buckets():
    """Buckets are module-level state -- reset around every test."""
    _requests.clear()
    _event_requests.clear()
    yield
    _requests.clear()
    _event_requests.clear()


def _body(response) -> dict:
    return json.loads(response.body)


class TestNonWriteMethodsSkipped:
    def test_get_never_limited(self):
        for _ in range(50):
            assert check_rate_limit("GET", "/api/kurl") is None

    def test_head_never_limited(self):
        for _ in range(50):
            assert check_rate_limit("HEAD", "/api/kurl") is None


class TestWriteBucket:
    def test_allows_up_to_max_requests(self):
        for i in range(10):
            assert check_rate_limit("POST", "/api/kurl") is None, f"request {i} should pass"

    def test_blocks_the_request_over_max(self):
        for _ in range(10):
            check_rate_limit("POST", "/api/kurl")
        blocked = check_rate_limit("POST", "/api/kurl")
        assert blocked is not None
        assert blocked.status == 429
        assert _body(blocked)["code"] == "RATE_LIMITED"

    def test_patch_and_delete_share_the_post_bucket(self):
        for _ in range(5):
            check_rate_limit("POST", "/api/kurl")
        for _ in range(5):
            check_rate_limit("PATCH", "/api/kurl")
        assert check_rate_limit("DELETE", "/api/kurl") is not None

    def test_different_write_paths_share_one_bucket(self):
        """Bucket keys on write-method only, not path -- any non-events write
        path draws from the same global counter."""
        for _ in range(10):
            check_rate_limit("POST", "/api/kurl")
        assert check_rate_limit("POST", "/api/something-else") is not None


class TestEventsBucketIsIndependent:
    def test_events_not_capped_by_full_write_bucket(self):
        for _ in range(10):
            check_rate_limit("POST", "/api/kurl")
        # Write bucket is now full -- events bucket must be untouched.
        assert check_rate_limit("POST", "/api/events") is None

    def test_events_has_its_own_higher_ceiling(self):
        for i in range(60):
            assert check_rate_limit("POST", "/api/events") is None, f"event {i} should pass"
        blocked = check_rate_limit("POST", "/api/events")
        assert blocked is not None
        assert _body(blocked)["code"] == "RATE_LIMITED"

    def test_full_events_bucket_does_not_block_writes(self):
        for _ in range(60):
            check_rate_limit("POST", "/api/events")
        assert check_rate_limit("POST", "/api/kurl") is None


class TestWindowSlides:
    def test_bucket_frees_up_after_window_elapses(self):
        with patch("time.time") as mock_time:
            mock_time.return_value = 1_000.0
            for _ in range(10):
                check_rate_limit("POST", "/api/kurl")
            assert check_rate_limit("POST", "/api/kurl") is not None

            # Jump past the 60s window -- oldest entries fall out.
            mock_time.return_value = 1_061.0
            assert check_rate_limit("POST", "/api/kurl") is None

    def test_retry_after_reflects_remaining_window(self):
        with patch("time.time") as mock_time:
            mock_time.return_value = 1_000.0
            for _ in range(10):
                check_rate_limit("POST", "/api/kurl")
            mock_time.return_value = 1_030.0  # 30s into the 60s window
            blocked = check_rate_limit("POST", "/api/kurl")
            assert "31s" in _body(blocked)["message"]
