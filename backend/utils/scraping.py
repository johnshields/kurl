import re

from app.constants import PLATFORM_NAMES

_OG_TITLE = re.compile(
    r'<meta\s+property=["\']og:title["\']\s+content="([^"]+)"', re.I
)
_OG_TITLE_SQ = re.compile(
    r"<meta\s+property=[\"']og:title[\"']\s+content='([^']+)'", re.I
)
_OG_DESC = re.compile(
    r'<meta\s+property=["\']og:description["\']\s+content="([^"]+)"', re.I
)
_OG_DESC_SQ = re.compile(
    r"<meta\s+property=[\"']og:description[\"']\s+content='([^']+)'", re.I
)
_NEXT_DATA = re.compile(
    r'<script[^>]*id="__NEXT_DATA__"[^>]*>([^<]+)</script>'
)
_BY_SPLIT = re.compile(r"^(.*?)\s+by\s+(.+)$", re.I)
_PLATFORM_SUFFIX = re.compile(
    r"\s+on\s+("
    + "|".join(re.escape(name).replace(r"\ ", r"\s+") for name in PLATFORM_NAMES.values())
    + r")\s*$",
    re.I,
)


def extract_og_title(html: str) -> str | None:
    m = _OG_TITLE.search(html) or _OG_TITLE_SQ.search(html)
    return _decode_entities(m.group(1).strip()) if m else None


def extract_og_description(html: str) -> str | None:
    m = _OG_DESC.search(html) or _OG_DESC_SQ.search(html)
    return _decode_entities(m.group(1).strip()) if m else None


def _decode_entities(text: str) -> str:
    """Decode common HTML entities (&#x27; &#39; &amp; etc.)."""
    import html
    return html.unescape(text)


def extract_next_data(html: str) -> str | None:
    m = _NEXT_DATA.search(html)
    return m.group(1) if m else None


def split_title_by_artist(text: str) -> tuple[str, str | None]:
    """Split 'Song by Artist' into (title, artist). No 'by' -> (text, None)."""
    m = _BY_SPLIT.match(text)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return text, None


def strip_platform_suffix(text: str) -> str:
    """Remove trailing 'on Apple Music', 'on Spotify' etc."""
    return _PLATFORM_SUFFIX.sub("", text).strip()
