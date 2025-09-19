import base64

from agents.email_analyzer import _extract_content_from_thread


def _encode(text: str) -> str:
    raw = text.encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def test_extract_content_prefers_decoded_plaintext():
    body = _encode("Interview scheduled for Monday")
    thread = {
        "messages": [
            {
                "payload": {
                    "parts": [
                        {
                            "mimeType": "text/plain",
                            "body": {"data": body},
                        }
                    ]
                }
            }
        ]
    }

    extracted = _extract_content_from_thread(thread)
    assert "Interview scheduled" in extracted


def test_extract_content_falls_back_to_snippet():
    thread = {
        "messages": [
            {
                "snippet": "Reminder: bring ID",
            }
        ]
    }

    extracted = _extract_content_from_thread(thread)
    assert extracted == "Reminder: bring ID"
