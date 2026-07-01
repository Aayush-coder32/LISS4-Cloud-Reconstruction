from app.core.security import create_access_token, decode_token, get_password_hash, verify_password


def test_password_hash_roundtrip() -> None:
    password = "CloudFree@2026"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed)


def test_access_token_contains_subject() -> None:
    token = create_access_token("user-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
