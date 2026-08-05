"""Existing tests for the registration module.

These tests cover the basic happy path but none of the
validation logic (which doesn't exist yet).
"""
import pytest
from src.registration import UserStore, register_user


@pytest.fixture
def store():
    return UserStore()


def test_register_user_returns_success(store):
    result = register_user(store, "alice", "alice@example.com", "password123")
    assert result["success"] is True
    assert "user_id" in result


def test_registered_user_can_be_retrieved(store):
    result = register_user(store, "bob", "bob@example.com", "securepass1")
    user = store.get(result["user_id"])
    assert user is not None
    assert user["username"] == "bob"
    assert user["email"] == "bob@example.com"


def test_exists_by_email_after_registration(store):
    register_user(store, "carol", "carol@example.com", "mypass123")
    assert store.exists_by_email("carol@example.com") is True
    assert store.exists_by_email("unknown@example.com") is False
