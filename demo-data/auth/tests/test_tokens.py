import pytest

from app.tokens import ACCESS_TOKEN_TTL_SECONDS, InvalidToken, issue_access_token, verify_access_token

SECRET = "test-secret-long-enough-for-hs256-signing"


def test_round_trip():
    token = issue_access_token(SECRET, "u_1", "s_1", now=1000)
    claims = verify_access_token(SECRET, token, now=1001)
    assert claims["sub"] == "u_1" and claims["sid"] == "s_1"


def test_expires():
    token = issue_access_token(SECRET, "u_1", "s_1", now=1000)
    with pytest.raises(InvalidToken):
        verify_access_token(SECRET, token, now=1000 + ACCESS_TOKEN_TTL_SECONDS)


def test_rejects_wrong_signature():
    token = issue_access_token(SECRET, "u_1", "s_1", now=1000)
    with pytest.raises(InvalidToken):
        verify_access_token("another-secret-long-enough-for-hs256", token, now=1001)
