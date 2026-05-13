from urllib.parse import quote

from app.constants import URL_TEMPLATES


def build_search_url(platform: str, title: str | None, artist: str | None) -> str | None:
    """Build a target-platform search URL as a fallback when direct link isn't available."""
    template = URL_TEMPLATES.get(platform, {}).get("search")
    if not template:
        return None
    query = " ".join(p for p in (title, artist) if p)
    if not query:
        return None
    return template.format(query=quote(query))
