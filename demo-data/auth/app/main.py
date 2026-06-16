import time

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from .passwords import verify_password
from .sessions import RefreshRejected
from .tokens import InvalidToken, issue_access_token, verify_access_token


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


def create_app(users: dict[str, dict], sessions, jwt_secret: str) -> FastAPI:
    """`users` maps email to {"id", "password_hash"}."""
    app = FastAPI(title="auth")

    def current_session(authorization: str) -> dict:
        try:
            claims = verify_access_token(jwt_secret, authorization.removeprefix("Bearer "), int(time.time()))
        except InvalidToken:
            raise HTTPException(401, "invalid token")
        if sessions.get_user_id(claims["sid"]) is None:
            raise HTTPException(401, "session ended")
        return claims

    @app.post("/login")
    def login(request: LoginRequest):
        user = users.get(request.email)
        if user is None or not verify_password(request.password, user["password_hash"]):
            raise HTTPException(401, "wrong email or password")
        session_id, refresh_token = sessions.create(user["id"])
        return {
            "access_token": issue_access_token(jwt_secret, user["id"], session_id, int(time.time())),
            "refresh_token": refresh_token,
        }

    @app.post("/refresh")
    def refresh(request: RefreshRequest):
        try:
            session_id, user_id, refresh_token = sessions.rotate_refresh_token(request.refresh_token)
        except RefreshRejected:
            raise HTTPException(401, "log in again")
        return {
            "access_token": issue_access_token(jwt_secret, user_id, session_id, int(time.time())),
            "refresh_token": refresh_token,
        }

    @app.get("/me")
    def me(authorization: str = Header(default="")):
        return {"user_id": current_session(authorization)["sub"]}

    @app.post("/logout", status_code=204)
    def logout(authorization: str = Header(default="")):
        sessions.delete(current_session(authorization)["sid"])

    return app
