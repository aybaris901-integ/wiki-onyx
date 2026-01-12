"""Short signed access tokens. The `sid` claim ties a token to a server-side session."""
import jwt

ACCESS_TOKEN_TTL_SECONDS = 60 * 60
ALGORITHM = "HS256"


class InvalidToken(Exception):
    pass


def issue_access_token(secret: str, user_id: str, session_id: str, now: int) -> str:
    claims = {"sub": user_id, "sid": session_id, "iat": now, "exp": now + ACCESS_TOKEN_TTL_SECONDS}
    return jwt.encode(claims, secret, algorithm=ALGORITHM)


def verify_access_token(secret: str, token: str, now: int) -> dict:
    try:
        claims = jwt.decode(token, secret, algorithms=[ALGORITHM], options={"verify_exp": False, "verify_iat": False})
    except jwt.InvalidTokenError as exc:
        raise InvalidToken(str(exc)) from exc
    if claims["exp"] <= now:
        raise InvalidToken("expired")
    return claims
