from app.sessions import KEY_PREFIX, SESSION_TTL_SECONDS, RedisSessionStore


def test_create_get_delete(redis_client):
    sessions = RedisSessionStore(redis_client)
    session_id = sessions.create("u_1")
    assert sessions.get_user_id(session_id) == "u_1"
    sessions.delete(session_id)
    assert sessions.get_user_id(session_id) is None


def test_session_gets_a_ttl_so_redis_cleans_it_up(redis_client):
    session_id = RedisSessionStore(redis_client).create("u_1")
    assert redis_client.ttls[KEY_PREFIX + session_id] == SESSION_TTL_SECONDS
