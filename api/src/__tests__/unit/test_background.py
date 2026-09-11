"""
Tests for utils.background -- the plain-event-loop fallback. Workers'
waitUntil only runs under Pyodide.
"""

import asyncio

from utils.background import run_in_background


async def test_schedules_the_coroutine_without_raising():
    ran = []

    async def _work():
        ran.append(True)

    run_in_background(_work())
    await asyncio.sleep(0)  # let the scheduled task run
    assert ran == [True]


async def test_a_failing_task_does_not_propagate_to_the_caller():
    async def _boom():
        raise RuntimeError("background failure")

    run_in_background(_boom())
    await asyncio.sleep(0)
