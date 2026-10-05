def app_redirect(base_url: str, provider_key: str, status: str, token: str | None = None) -> str:
    url = f"{base_url}?{provider_key}={status}"
    if token:
        url += f"&token={token}"
    return url
