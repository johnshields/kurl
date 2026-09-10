"""
Auth Emails
Branded HTML/text bodies for the verification and password-reset links.
"""

_BG = "#0A0A0A"
_CARD = "#141414"
_BORDER = "#333333"
_TEXT = "#E5E5E5"
_MUTED = "#888888"
_FAINT = "#555555"
_FONT = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


def _html(heading: str, body: str, button_label: str, url: str, note: str) -> str:
    return (
        f'<body style="margin:0;padding:0;background:{_BG};">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{_BG};padding:40px 16px;">'
        f'<tr><td align="center">'
        f'<table role="presentation" cellpadding="0" cellspacing="0" style="width:100%;max-width:440px;background:{_CARD};border:1px solid {_BORDER};border-radius:12px;">'
        f'<tr><td style="padding:32px;font-family:{_FONT};color:{_TEXT};">'
        f'<div style="font-size:22px;font-weight:700;letter-spacing:-0.5px;">kurl</div>'
        f'<div style="height:24px;line-height:24px;">&nbsp;</div>'
        f'<div style="font-size:15px;line-height:1.5;">{heading}</div>'
        f'<div style="height:8px;line-height:8px;">&nbsp;</div>'
        f'<div style="font-size:13px;line-height:1.6;color:{_MUTED};">{body}</div>'
        f'<div style="height:24px;line-height:24px;">&nbsp;</div>'
        f'<a href="{url}" style="display:inline-block;background:{_TEXT};color:{_BG};text-decoration:none;'
        f'font-family:{_FONT};font-size:13px;font-weight:700;letter-spacing:-0.2px;padding:12px 20px;border-radius:6px;">{button_label}</a>'
        f'<div style="height:20px;line-height:20px;">&nbsp;</div>'
        f'<div style="font-size:12px;line-height:1.6;color:{_MUTED};">{note}</div>'
        f'<div style="height:16px;line-height:16px;">&nbsp;</div>'
        f'<div style="font-size:11px;color:{_FAINT};word-break:break-all;">{url}</div>'
        f'</td></tr></table></td></tr></table></body>'
    )


def _text(heading: str, url: str, note: str) -> str:
    return f"kurl -- {heading}\n\n{url}\n\n{note}"


def verification_email(link: str) -> tuple[str, str, str]:
    heading = "Verify your email"
    body = "Confirm this address to finish setting up your kurl account."
    note = "This link expires in 24 hours. If you didn't create a kurl account, ignore this email."
    return "Verify your kurl email", _html(heading, body, "Verify email", link, note), _text(heading, link, note)


def reset_email(link: str) -> tuple[str, str, str]:
    heading = "Reset your password"
    body = "Use the button below to set a new password for your kurl account."
    note = "This link expires in 30 minutes. If you didn't request this, ignore this email."
    return "Reset your kurl password", _html(heading, body, "Reset password", link, note), _text(heading, link, note)
