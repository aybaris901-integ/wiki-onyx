from fastapi.testclient import TestClient

from app.main import create_app
from app.passwords import hash_password
from app.sessions import RedisSessionStore

SECRET = "test-secret-long-enough-for-hs256-signing"
USERS = {"ap@customer.example": {"id": "u_1", "password_hash": hash_password("correct horse")}}


def client(redis_client):
    return TestClient(create_app(USERS, RedisSessionStore(redis_client), SECRET))


def login(http):
    return http.post("/login", json={"email": "ap@customer.example", "password": "correct horse"}).json()


def bearer(tokens):
    return {"authorization": f"Bearer {tokens['access_token']}"}


def test_refresh_returns_working_tokens(redis_client):
    http = client(redis_client)
    refreshed = http.post("/refresh", json={"refresh_token": login(http)["refresh_token"]}).json()
    assert http.get("/me", headers=bearer(refreshed)).json() == {"user_id": "u_1"}


def test_reused_refresh_token_logs_the_user_out(redis_client):
    http = client(redis_client)
    tokens = login(http)
    assert http.post("/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 200
    assert http.post("/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
    assert http.get("/me", headers=bearer(tokens)).status_code == 401
