import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg://acme@localhost/acme")
JWT_SECRET = os.environ.get("JWT_SECRET", "")
