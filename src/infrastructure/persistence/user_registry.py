"""User registry for CPF tracking (in-memory implementation)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from threading import Lock


@dataclass
class UserRecord:
    """User record with CPF."""
    user_id: str
    username: str
    cpf: Optional[str] = None
    disabled: bool = False


class InMemoryUserRegistry:
    """Thread-safe in-memory user registry with CPF tracking."""

    def __init__(self) -> None:
        self._users: dict[str, UserRecord] = {}  # user_id -> UserRecord
        self._cpf_to_user_id: dict[str, str] = {}  # cpf -> user_id
        self._lock = Lock()

        # Seed with mock users
        self._seed_mock_users()

    def _seed_mock_users(self) -> None:
        """Seed with initial mock users (valid CPFs)."""
        # Valid CPFs for testing:
        # 529.982.247-25 -> 52998224725
        # 111.444.777-35 is INVALID
        # 390.533.447-05 -> 39053344705
        mock_users = [
            UserRecord(user_id="user-123", username="john_doe", cpf="52998224725"),
            UserRecord(user_id="user-456", username="jane_doe", cpf="39053344705"),
        ]
        for user in mock_users:
            self._users[user.user_id] = user
            if user.cpf:
                self._cpf_to_user_id[user.cpf] = user.user_id

    def get_by_user_id(self, user_id: str) -> Optional[UserRecord]:
        """Get user by user_id."""
        with self._lock:
            return self._users.get(user_id)

    def get_by_cpf(self, cpf: str) -> Optional[UserRecord]:
        """Get user by CPF."""
        with self._lock:
            user_id = self._cpf_to_user_id.get(cpf)
            if user_id:
                return self._users.get(user_id)
            return None

    def cpf_exists(self, cpf: str) -> bool:
        """Check if CPF is already registered."""
        with self._lock:
            return cpf in self._cpf_to_user_id

    def register_user(self, user_id: str, username: str, cpf: Optional[str] = None) -> UserRecord:
        """Register a new user with optional CPF."""
        with self._lock:
            if user_id in self._users:
                raise ValueError(f"User {user_id} already exists")

            if cpf and cpf in self._cpf_to_user_id:
                raise ValueError(f"CPF {cpf} already registered")

            user = UserRecord(user_id=user_id, username=username, cpf=cpf)
            self._users[user_id] = user
            if cpf:
                self._cpf_to_user_id[cpf] = user_id
            return user

    def update_cpf(self, user_id: str, cpf: str) -> UserRecord:
        """Update CPF for existing user."""
        with self._lock:
            user = self._users.get(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")

            if cpf in self._cpf_to_user_id and self._cpf_to_user_id[cpf] != user_id:
                raise ValueError(f"CPF {cpf} already registered to another user")

            # Remove old CPF mapping if exists
            if user.cpf and user.cpf in self._cpf_to_user_id:
                del self._cpf_to_user_id[user.cpf]

            user.cpf = cpf
            self._cpf_to_user_id[cpf] = user_id
            return user


# Singleton instance
_user_registry: Optional[InMemoryUserRegistry] = None


def get_user_registry() -> InMemoryUserRegistry:
    """Get the singleton user registry instance."""
    global _user_registry
    if _user_registry is None:
        _user_registry = InMemoryUserRegistry()
    return _user_registry