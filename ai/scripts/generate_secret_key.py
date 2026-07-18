#!/usr/bin/env python3
"""Generate a secure SECRET_KEY for production."""

import secrets


def generate_secret_key(length: int = 32) -> str:
    """Generate a secure random secret key.

    Args:
        length: Length of the secret key in bytes (default: 32)

    Returns:
        Hex-encoded random secret key
    """
    return secrets.token_hex(length)


def main():
    """Generate and display a secret key."""
    key = generate_secret_key()
    print(f"Generated SECRET_KEY:\n{key}\n")
    print("Add to .env:")
    print(f"SECRET_KEY={key}")


if __name__ == "__main__":
    main()
