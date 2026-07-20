#!/usr/bin/env python3
import hashlib
import secrets
import sys


def generate_hash(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return hashed, salt


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_password_hash.py <password>")
        sys.exit(1)

    password = sys.argv[1]
    hashed, salt = generate_hash(password)
    print(f"HASH: {hashed}")
    print(f"SALT: {salt}")
    print(f"\nAdd to your .env file:")
    print(f"HORA_AUTH_PASSWORD_HASH={hashed}")
    print(f"HORA_AUTH_SALT={salt}")
