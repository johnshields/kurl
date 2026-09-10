"""
Auth Emails
Branded HTML/text bodies for the verification and password-reset links.
"""

from emails._layout import render_html, render_text


def verification_email(link: str) -> tuple[str, str, str]:
    heading = "Verify your email"
    body = "Confirm this address to finish setting up your kurl account."
    note = "This link expires in 24 hours. If you didn't create a kurl account, ignore this email."
    return "Verify your kurl email", render_html(heading, body, "Verify email", link, note), render_text(heading, link, note)


def reset_email(link: str) -> tuple[str, str, str]:
    heading = "Reset your password"
    body = "Use the button below to set a new password for your kurl account."
    note = "This link expires in 30 minutes. If you didn't request this, ignore this email."
    return "Reset your kurl password", render_html(heading, body, "Reset password", link, note), render_text(heading, link, note)
