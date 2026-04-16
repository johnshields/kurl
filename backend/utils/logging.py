import logging

from uvicorn.config import LOGGING_CONFIG

for _handler in LOGGING_CONFIG["handlers"].values():
    _handler["stream"] = "ext://sys.stdout"


def get_logger():
    """Return the uvicorn error logger for consistent log formatting."""
    return logging.getLogger("uvicorn.error")
