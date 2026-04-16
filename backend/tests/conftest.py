"""
Shared fixtures and test config.
"""
import os
import sys
from pathlib import Path

# Ensure backend/ is on sys.path so tests can import modules.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

# Prevent real environment creds from leaking into tests.
os.environ.setdefault("SPOTIFY_CLIENT_ID", "")
os.environ.setdefault("SPOTIFY_CLIENT_SECRET", "")
os.environ.setdefault("TIDAL_CLIENT_ID", "")
os.environ.setdefault("TIDAL_CLIENT_SECRET", "")
os.environ.setdefault("APPLE_TEAM_ID", "")
os.environ.setdefault("APPLE_KEY_ID", "")
os.environ.setdefault("APPLE_PRIVATE_KEY", "")
