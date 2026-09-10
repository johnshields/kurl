"""
Tests for emails.social.message_received_email -- subject line and the
preview text built from the message body or the attached kurl.
"""

from emails.social import message_received_email

_LINK = "https://kurl.online/messages"


def test_subject_names_the_sender():
    subject, _, _ = message_received_email("cool-cat", "hey there", None, _LINK)
    assert subject == "cool-cat sent you a message on kurl"


def test_body_passes_through():
    _, _, text = message_received_email("cool-cat", "short note", None, _LINK)
    assert "short note" in text


def test_body_is_truncated():
    _, _, text = message_received_email("cool-cat", "x" * 200, None, _LINK)
    assert ("x" * 139 + "…") in text


def test_kurl_uses_artist_and_title():
    _, _, text = message_received_email(
        "cool-cat", None, {"artist": "Fred again..", "title": "Delilah"}, _LINK
    )
    assert "Sent a kurl: Fred again.. - Delilah" in text


def test_kurl_fallback_when_no_metadata():
    _, _, text = message_received_email("cool-cat", None, {}, _LINK)
    assert "Sent you a kurl." in text
