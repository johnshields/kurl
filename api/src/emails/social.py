"""
Social Emails
Branded HTML/text body for the "you have a new message" notification.
"""

from emails._layout import render_html, render_text

_MAX_PREVIEW = 140


def message_received_email(sender: str, body, kurl, link: str) -> tuple[str, str, str]:
    heading = f"New message from {sender}"
    preview = _preview(body, kurl)
    note = "You're getting this because message emails are on. Turn them off in Settings."
    return (
        f"{sender} sent you a message on kurl",
        render_html(heading, preview, "Open in kurl", link, note),
        render_text(f"{heading}\n\n{preview}", link, note),
    )


def _preview(body, kurl) -> str:
    if body:
        return body if len(body) <= _MAX_PREVIEW else body[: _MAX_PREVIEW - 1] + "…"
    if kurl:
        artist, title = kurl.get("artist"), kurl.get("title")
        if artist and title:
            return f"Sent a kurl: {artist} - {title}"
        if title:
            return f"Sent a kurl: {title}"
    return "Sent you a kurl."
