import os

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
JWT_SECRET = os.environ.get("JWT_SECRET", "")
