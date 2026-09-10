"""
Bot Detection
Flags crawler and headless-client user agents so analytics can skip them.
"""

BOT_PATTERNS = [
    "bot", "crawler", "spider", "headlesschrome", "ahrefsbot",
    "googlebot", "bingbot", "slurp", "duckduckbot",
    "facebookexternalhit", "semrushbot",
]


def is_bot(user_agent: str | None) -> bool:
    ua = (user_agent or "").lower()
    # Real browsers always send a User-Agent; scripted/headless clients often skip it.
    if not ua:
        return True
    return any(p in ua for p in BOT_PATTERNS)
