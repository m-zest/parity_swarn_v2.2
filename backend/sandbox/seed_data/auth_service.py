"""
Authentication Service v1.8.0
Internal use only - FinTech Corp

Handles user authentication, session management, and access control.
"""

import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta


SESSION_DURATION = timedelta(hours=8)
MAX_LOGIN_ATTEMPTS = 5


def authenticate_user(username, password):
    """Authenticate a user and create a session token."""
    conn = sqlite3.connect("/var/data/customers/customers.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, password_hash, role FROM users WHERE username = ?",
        (username,)
    )
    row = cursor.fetchone()
    if row is None:
        return {"error": "user_not_found"}

    user_id, stored_hash, role = row
    input_hash = hashlib.sha256(password.encode()).hexdigest()

    if input_hash != stored_hash:
        return {"error": "invalid_password"}

    token = secrets.token_hex(32)
    expires = (datetime.utcnow() + SESSION_DURATION).isoformat()
    cursor.execute(
        "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires)
    )
    conn.commit()
    conn.close()
    return {"token": token, "role": role, "expires": expires}


def validate_session(token):
    """Check if a session token is valid."""
    conn = sqlite3.connect("/var/data/customers/customers.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, expires_at FROM sessions WHERE token = ?",
        (token,)
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return {"user_id": row[0], "expires_at": row[1]}


def check_permission(user_id, resource):
    """Check if user has access to a resource."""
    conn = sqlite3.connect("/var/data/customers/customers.db")
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return False
    role = row[0]
    # Admin has access to everything
    if role == "admin":
        return True
    # Engineers can access code and configs
    if role == "engineer" and resource in ["code", "config", "logs"]:
        return True
    # Read-only for other roles
    if resource in ["docs", "dashboard"]:
        return True
    return False
