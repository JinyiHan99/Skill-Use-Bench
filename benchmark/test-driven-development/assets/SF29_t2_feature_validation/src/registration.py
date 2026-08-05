"""User registration module.

Handles user account creation with basic fields.
"""
import re
import hashlib
import datetime


class UserStore:
    """In-memory user storage for the registration system."""

    def __init__(self):
        self._users = {}

    def save(self, user_data: dict) -> str:
        """Save a user record and return the user ID."""
        user_id = hashlib.md5(
            user_data["email"].encode()
        ).hexdigest()[:8]
        self._users[user_id] = {
            **user_data,
            "id": user_id,
            "created_at": datetime.datetime.utcnow().isoformat(),
        }
        return user_id

    def get(self, user_id: str) -> dict | None:
        """Retrieve a user by ID."""
        return self._users.get(user_id)

    def exists_by_email(self, email: str) -> bool:
        """Check if a user with the given email already exists."""
        return any(
            u["email"] == email for u in self._users.values()
        )


def register_user(store: UserStore, username: str, email: str, password: str) -> dict:
    """Register a new user.

    Currently accepts any input without validation. The following
    validations are needed but not yet implemented:

    - Username must be 3-20 characters, alphanumeric and underscores only
    - Email must be a valid email format
    - Password must be at least 8 characters with at least one digit
    - Email must not already be registered

    Returns a dict with 'success' and either 'user_id' or 'error'.
    """
    user_data = {
        "username": username,
        "email": email,
        "password_hash": hashlib.sha256(password.encode()).hexdigest(),
    }
    user_id = store.save(user_data)
    return {"success": True, "user_id": user_id}
