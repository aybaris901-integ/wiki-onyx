import pytest


class FakeRedis:
    """The few Redis commands auth uses. Records the TTL so tests can check it."""

    def __init__(self):
        self.data = {}
        self.ttls = {}

    def set(self, key, value, ex=None):
        self.data[key] = value.encode() if isinstance(value, str) else value
        self.ttls[key] = ex

    def get(self, key):
        return self.data.get(key)

    def delete(self, key):
        self.data.pop(key, None)
        self.ttls.pop(key, None)


@pytest.fixture
def redis_client():
    return FakeRedis()
