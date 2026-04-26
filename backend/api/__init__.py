"""
Template rendering
Simple string-based templates — no Jinja2 dependency needed on Workers.
"""

from pathlib import Path

from fastapi.responses import HTMLResponse

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "public"
_cache: dict[str, str] = {}


def _read(name: str) -> str:
    if name not in _cache:
        _cache[name] = (_TEMPLATES_DIR / name).read_text()
    return _cache[name]


def render(name: str, context: dict | None = None) -> HTMLResponse:
    html = _read(name)
    if context:
        for key, value in context.items():
            html = html.replace("{{ " + key + " }}", str(value))
    return HTMLResponse(html)
