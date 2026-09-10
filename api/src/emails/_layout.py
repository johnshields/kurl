"""
Email Layout (shared)
Branded HTML/text bodies for a kurl link email -- heading, blurb, CTA button.
"""

_BG = "#0A0A0A"
_CARD = "#141414"
_BORDER = "#333333"
_TEXT = "#E5E5E5"
_MUTED = "#888888"
_FAINT = "#555555"
_FONT = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


def render_html(heading: str, body: str, button_label: str, url: str, note: str) -> str:
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


def render_text(heading: str, url: str, note: str) -> str:
    return f"kurl -- {heading}\n\n{url}\n\n{note}"
