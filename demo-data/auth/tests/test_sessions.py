import pytest

from app.sessions import KEY_PREFIX, SESSION_TTL_SECONDS, RedisSessionStore, RefreshRejected


def test_create_get_delete(redis_client):
    sessions = RedisSessionStore(redis_client)
    session_id, _ = sessions.create("u_1")
    assert sessions.get_user_id(session_id) == "u_1"
    sessions.delete(session_id)
    assert sessions.get_user_id(session_id) is None


def test_session_gets_a_ttl_so_redis_cleans_it_up(redis_client):
    session_id, _ = RedisSessionStore(redis_client).create("u_1")
    assert redis_client.ttls[KEY_PREFIX + session_id] == SESSION_TTL_SECONDS


def test_refresh_token_rotates(redis_client):
    sessions = RedisSessionStore(redis_client)
    session_id, first = sessions.create("u_1")
    returned_id, user_id, second = sessions.rotate_refresh_token(first)
    assert (returned_id, user_id) == (session_id, "u_1")
    assert second != first


def test_reusing_an_old_refresh_token_ends_the_session(redis_client):
    sessions = RedisSessionStore(redis_client)
    session_id, first = sessions.create("u_1")
    _, _, second = sessions.rotate_refresh_token(first)

    with pytest.raises(RefreshRejected):
        sessions.rotate_refresh_token(first)

    assert sessions.get_user_id(session_id) is None
    with pytest.raises(RefreshRejected):
        sessions.rotate_refresh_token(second)
