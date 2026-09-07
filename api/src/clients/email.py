"""
Email Client (Cloudflare Email Service)
Thin wrapper around the Workers send_email binding, stashed at module level like clients/cache.py's KV binding.
"""

from utils.logging import get_logger

logger = get_logger()

_binding = None


def init_email(binding) -> None:
    """Set the EMAIL binding. Called from the Workers entry point."""
    global _binding
    if binding and not _binding:
        _binding = binding
        logger.info("Email binding initialised")


def is_configured() -> bool:
    return _binding is not None


async def send(*, to: str, from_address: str, subject: str, html: str, text: str) -> bool:
    """Best-effort -- returns False on failure instead of raising."""
    if not _binding:
        logger.warning("Email binding not configured -- skipping send to %s", to)
        return False
    try:
        await _binding.send(**{"to": to, "from": from_address, "subject": subject, "html": html, "text": text})
        return True
    except Exception as e:
        logger.warning("Failed to send email to %s: %s", to, e)
        return False
