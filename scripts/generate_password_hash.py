#!/usr/bin/env python3
import sys

import bcrypt


def generate_hash(password: str, rounds: int = 12) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt(rounds)
    ).decode("utf-8")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_password_hash.py <password> [rounds]")
        sys.exit(1)

    password = sys.argv[1]
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    hashed = generate_hash(password, rounds)
    print(f"HASH: {hashed}")
    print(f"\nAdd to your .env file:")
    print(f"HORA_AUTH_PASSWORD_HASH={hashed}")
