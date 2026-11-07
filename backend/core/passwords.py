# -*- coding: utf-8 -*-
import hashlib
import hmac
import secrets

PBKDF2_ROUNDS = 180_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ROUNDS,
    )
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    if not stored:
        return False
    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, rounds_s, salt, expected = stored.split("$", 3)
            rounds = int(rounds_s)
        except (ValueError, TypeError):
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            rounds,
        )
        return hmac.compare_digest(digest.hex(), expected)
    # Legacy plaintext leftover from older configs
    return hmac.compare_digest(password, stored)
