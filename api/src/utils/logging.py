"""
Logging setup
"""

import logging
import sys

_logger = None


def get_logger():
    global _logger
    if _logger:
        return _logger
    _logger = logging.getLogger("kurl")
    if not _logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        _logger.addHandler(handler)
        _logger.setLevel(logging.INFO)
    return _logger
