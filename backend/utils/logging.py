"""
Logging setup
Uses uvicorn's logger when available (local dev), falls back to stdlib.
"""

import logging
import sys


def get_logger():
    try:
        from uvicorn.config import LOGGING_CONFIG

        for _handler in LOGGING_CONFIG["handlers"].values():
            _handler["stream"] = "ext://sys.stdout"
        return logging.getLogger("uvicorn.error")
    except ImportError:
        # Workers runtime — no uvicorn
        logger = logging.getLogger("kurl")
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
