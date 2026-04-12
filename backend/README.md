# kurl_api

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
fastapi dev main.py
```

## .env

```
REDIS_URL=redis://localhost:6379
ODESLI_BASE_URL=https://api.song.link/v1-alpha.1/links
ODESLI_API_KEY=
CACHE_TTL_SECONDS=86400
```
