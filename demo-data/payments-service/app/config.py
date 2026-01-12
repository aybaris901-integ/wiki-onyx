import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg://acme@localhost/payments")
PAYRAIL_BASE_URL = os.environ.get("PAYRAIL_BASE_URL", "https://api.payrail.example/v2")
PAYRAIL_API_KEY = os.environ.get("PAYRAIL_API_KEY", "")
