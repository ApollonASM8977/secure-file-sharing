"""Shared utilities: crypto helpers, user management, logging."""

import os
import re
import json
import hashlib
import datetime

import bcrypt
from Crypto.PublicKey import RSA

from config import (
    USER_DB, LOG_FILE, KEYS_DIR,
    PBKDF2_ITERATIONS, RSA_KEY_SIZE
)


# ── Key Derivation ────────────────────────────────────────────────────────────

def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 32-byte AES key from a password using PBKDF2-HMAC-SHA256.

    Uses 260,000 iterations (OWASP 2024 recommendation).
    The salt must be stored alongside the ciphertext.
    """
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=32,
    )


# ── User Management ───────────────────────────────────────────────────────────

def load_users() -> dict:
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            return json.load(f)
    return {}


def save_users(users: dict) -> None:
    with open(USER_DB, "w") as f:
        json.dump(users, f, indent=2)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def is_strong_password(password: str) -> bool:
    """Enforce: ≥8 chars, uppercase, lowercase, digit, special character."""
    return bool(
        len(password) >= 8
        and re.search(r"[A-Z]", password)
        and re.search(r"[a-z]", password)
        and re.search(r"\d", password)
        and re.search(r"[!@#$%^&*()\-_=+\[\]{};:',.<>?/\\|`~]", password)
    )


# ── RSA Key Management ────────────────────────────────────────────────────────

def generate_rsa_keys(username: str) -> None:
    """Generate a 2048-bit RSA key pair and save to the keys/ directory."""
    os.makedirs(KEYS_DIR, exist_ok=True)
    private_key = RSA.generate(RSA_KEY_SIZE)
    public_key = private_key.publickey()

    with open(os.path.join(KEYS_DIR, f"{username}_private.pem"), "wb") as f:
        f.write(private_key.export_key())

    with open(os.path.join(KEYS_DIR, f"{username}_public.pem"), "wb") as f:
        f.write(public_key.export_key())


def load_rsa_key(username: str, key_type: str = "private"):
    """Load an RSA key from the keys/ directory. Returns None if not found."""
    path = os.path.join(KEYS_DIR, f"{username}_{key_type}.pem")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return RSA.import_key(f.read())


# ── Activity Logging ──────────────────────────────────────────────────────────

def log_activity(action: str, filename: str, user: str) -> None:
    """Append a timestamped entry to the activity log."""
    entry = {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "action": action,
        "file": filename,
        "user": user,
    }
    logs: list = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                logs = json.load(f)
        except (json.JSONDecodeError, IOError):
            logs = []
    logs.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)
