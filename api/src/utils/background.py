"""
Background Tasks
Fire-and-forget scheduling for work that should not block a response.
"""

from asyncio import ensure_future

_background_tasks = set()


def run_in_background(coro) -> None:
    """Registers the task with Workers' waitUntil. Falls back to the plain
    event loop outside Workers (e.g. under pytest)."""
    task = ensure_future(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    try:
        from pyodide.ffi import create_proxy
        from workers import wait_until

        proxy = create_proxy(task)
        task.add_done_callback(lambda _: proxy.destroy())
        wait_until(proxy)
    except ImportError:
        pass
