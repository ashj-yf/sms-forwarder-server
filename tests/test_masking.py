from app.utils.masking import mask_phone, scrub


def test_mask_phone() -> None:
    assert mask_phone("13812345678") == "138****5678"


def test_scrub_sensitive_payload() -> None:
    payload = {
        "phone": "13812345678",
        "webhook_token": "wh_secret",
        "content": "hello",
        "nested": {"secret": "abc"},
    }

    assert scrub(payload) == {
        "phone": "138****5678",
        "webhook_token": "***",
        "content": {"content_length": 5},
        "nested": {"secret": "***"},
    }
