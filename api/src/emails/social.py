"""
Social Emails
Branded HTML/text body for the "you have a new message" notification.
"""

from emails._layout import render_html, render_text


def message_received_email(sender: str, preview: str, link: str) -> tuple[str, str, str]:
    heading = f"New message from {sender}"
    note = "You're getting this because message emails are on. Turn them off in Settings."
    return (
        f"{sender} sent you a message on kurl",
        render_html(heading, preview, "Open in kurl", link, note),
        render_text(f"{heading}\n\n{preview}", link, note),
    )
