"""
Tests for api.middleware.rate_limit -- per-IP sliding-window limiter with a
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

from api.middleware.rate_limit import _buckets, _event_buckets, check_rate_limit  # noqa: E402


def _req(ip: str | None = "1.1.1.1"):
    """Fake Workers request exposing just the header lookup rate_limit needs."""

    class _Request:
        headers = {"CF-Connecting-IP": ip} if ip else {}

    return _Request()


@pytest.fixture(autouse=True)
def _clear_buckets():
    """Buckets are module-level state -- reset around every test."""
    _buckets.clear()
    _event_buckets.clear()
    yield
    _buckets.clear()
    _event_buckets.clear()


def _body(response) -> dict:
    return json.loads(response.body)


class TestNonWriteMethodsSkipped:
    def test_get_never_limited(self):
        for _ in range(50):
            assert check_rate_limit(_req(), "GET", "/api/kurl") is None

    def test_head_never_limited(self):
        for _ in range(50):
            assert check_rate_limit(_req(), "HEAD", "/api/kurl") is None


class TestWriteBucket:
    def test_allows_up_to_max_requests(self):
        for i in range(10):
            assert check_rate_limit(_req(), "POST", "/api/kurl") is None, f"request {i} should pass"

    def test_blocks_the_request_over_max(self):
        for _ in range(10):
            check_rate_limit(_req(), "POST", "/api/kurl")
        blocked = check_rate_limit(_req(), "POST", "/api/kurl")
        assert blocked is not None
        assert blocked.status == 429
        assert _body(blocked)["code"] == "RATE_LIMITED"

    def test_patch_and_delete_share_the_post_bucket(self):
        for _ in range(5):
            check_rate_limit(_req(), "POST", "/api/kurl")
        for _ in range(5):
            check_rate_limit(_req(), "PATCH", "/api/kurl")
        assert check_rate_limit(_req(), "DELETE", "/api/kurl") is not None

    def test_different_write_paths_share_one_bucket_per_ip(self):
        """Bucket keys on IP + write-method only, not path -- any non-events
        write path draws from the same per-IP counter."""
        for _ in range(10):
            check_rate_limit(_req(), "POST", "/api/kurl")
        assert check_rate_limit(_req(), "POST", "/api/something-else") is not None


class TestPerIpIsolation:
    def test_different_ips_get_independent_buckets(self):
        for _ in range(10):
            check_rate_limit(_req("1.1.1.1"), "POST", "/api/kurl")
        # 1.1.1.1's bucket is now full -- a different IP must be unaffected.
        assert check_rate_limit(_req("2.2.2.2"), "POST", "/api/kurl") is None

    def test_blocked_ip_stays_blocked_independently(self):
        for _ in range(10):
            check_rate_limit(_req("1.1.1.1"), "POST", "/api/kurl")
        for _ in range(10):
            check_rate_limit(_req("2.2.2.2"), "POST", "/api/kurl")
        assert check_rate_limit(_req("1.1.1.1"), "POST", "/api/kurl") is not None
        assert check_rate_limit(_req("2.2.2.2"), "POST", "/api/kurl") is not None

    def test_missing_ip_header_falls_back_to_shared_unknown_bucket(self):
        for _ in range(10):
            check_rate_limit(_req(None), "POST", "/api/kurl")
        assert check_rate_limit(_req(None), "POST", "/api/kurl") is not None
        # A real IP is a different bucket, unaffected by the unknown fallback.
        assert check_rate_limit(_req("3.3.3.3"), "POST", "/api/kurl") is None


class TestEventsBucketIsIndependent:
    def test_events_not_capped_by_full_write_bucket(self):
        for _ in range(10):
            check_rate_limit(_req(), "POST", "/api/kurl")
        # Write bucket is now full -- events bucket must be untouched.
        assert check_rate_limit(_req(), "POST", "/api/events") is None

    def test_events_has_its_own_higher_ceiling(self):
        for i in range(60):
            assert check_rate_limit(_req(), "POST", "/api/events") is None, f"event {i} should pass"
        blocked = check_rate_limit(_req(), "POST", "/api/events")
        assert blocked is not None
        assert _body(blocked)["code"] == "RATE_LIMITED"

    def test_full_events_bucket_does_not_block_writes(self):
        for _ in range(60):
            check_rate_limit(_req(), "POST", "/api/events")
        assert check_rate_limit(_req(), "POST", "/api/kurl") is None

    def test_events_buckets_are_also_per_ip(self):
        for _ in range(60):
            check_rate_limit(_req("1.1.1.1"), "POST", "/api/events")
        assert check_rate_limit(_req("2.2.2.2"), "POST", "/api/events") is None


class TestWindowSlides:
    def test_bucket_frees_up_after_window_elapses(self):
        with patch("time.time") as mock_time:
            mock_time.return_value = 1_000.0
            for _ in range(10):
                check_rate_limit(_req(), "POST", "/api/kurl")
            assert check_rate_limit(_req(), "POST", "/api/kurl") is not None

            # Jump past the 60s window -- oldest entries fall out.
            mock_time.return_value = 1_061.0
            assert check_rate_limit(_req(), "POST", "/api/kurl") is None

    def test_retry_after_reflects_remaining_window(self):
        with patch("time.time") as mock_time:
            mock_time.return_value = 1_000.0
            for _ in range(10):
                check_rate_limit(_req(), "POST", "/api/kurl")
            mock_time.return_value = 1_030.0  # 30s into the 60s window
            blocked = check_rate_limit(_req(), "POST", "/api/kurl")
            assert "31s" in _body(blocked)["message"]


class TestTrackedIpSweep:
    def test_stale_ip_entries_are_pruned_once_threshold_crossed(self):
        with patch("api.middleware.rate_limit.RATE_LIMIT_MAX_TRACKED_IPS", 1), patch("time.time") as mock_time:
            mock_time.return_value = 1_000.0
            check_rate_limit(_req("1.1.1.1"), "POST", "/api/kurl")
            check_rate_limit(_req("2.2.2.2"), "POST", "/api/kurl")
            assert len(_buckets) == 2

            # Past the 60s window for both -- next call should sweep them out.
            mock_time.return_value = 1_100.0
            check_rate_limit(_req("3.3.3.3"), "POST", "/api/kurl")

            assert set(_buckets.keys()) == {"3.3.3.3"}
