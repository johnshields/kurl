from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

TRACKING_PARAMS = {
    "si",
    "fbclid",
    "gclid",
    "msclkid",
    "yclid",
    "dclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "_branch_match_id",
}

TRACKING_PREFIXES = ("utm_",)


def _is_tracking(key: str) -> bool:
    return key in TRACKING_PARAMS or any(key.startswith(p) for p in TRACKING_PREFIXES)


def normalise_url(url: str) -> str:
    """Strip known tracking params from a URL, preserving functional ones."""
    parts = urlparse(url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not _is_tracking(k)]
    return urlunparse(parts._replace(query=urlencode(query)))
