import hashlib
import hmac
import os


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    return f"{salt.hex()}:{_derive(password, salt).hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt, digest = stored.split(":")
    return hmac.compare_digest(_derive(password, bytes.fromhex(salt)).hex(), digest)


def _derive(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
