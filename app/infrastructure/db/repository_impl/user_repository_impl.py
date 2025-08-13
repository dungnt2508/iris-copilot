from __future__ import annotations

from typing import Optional, List, Dict
from datetime import datetime

from app.domain.user.repository import UserRepository
from app.domain.user.entities.user import User, UserRole, UserStatus
from app.domain.user.value_objects.email import Email


class InMemoryUserRepository(UserRepository):
    """
    Simple in-memory UserRepository for development/testing.
    Replace with DB-backed implementation in production.
    """

    def __init__(self) -> None:
        self._users_by_id: Dict[str, User] = {}
        self._users_by_email: Dict[str, str] = {}
        self._users_by_username: Dict[str, str] = {}

        # Seed an admin for testing
        admin = User.create(
            email="admin@example.com",
            username="admin",
            full_name="Administrator",
            hashed_password="$2b$12$abcdefghijklmnopqrstuv",  # not a real hash
            role=UserRole.ADMIN,
        )
        admin.status = UserStatus.ACTIVE
        self._insert(admin)

    def _insert(self, user: User) -> None:
        self._users_by_id[user.id] = user
        self._users_by_email[user.email] = user.id
        self._users_by_username[user.username] = user.id

    async def find_by_id(self, user_id: str) -> Optional[User]:
        return self._users_by_id.get(user_id)

    async def find_by_email(self, email: Email) -> Optional[User]:
        user_id = self._users_by_email.get(email.value.lower())
        return self._users_by_id.get(user_id) if user_id else None

    async def find_by_username(self, username: str) -> Optional[User]:
        user_id = self._users_by_username.get(username.lower())
        return self._users_by_id.get(user_id) if user_id else None

    async def save(self, user: User) -> User:
        # Upsert
        user.updated_at = datetime.utcnow()
        self._insert(user)
        return user

    async def delete(self, user_id: str) -> bool:
        user = self._users_by_id.pop(user_id, None)
        if not user:
            return False
        self._users_by_email.pop(user.email, None)
        self._users_by_username.pop(user.username, None)
        return True

    async def list_all(
        self, limit: int = 100, offset: int = 0, filters: Optional[dict] = None
    ) -> List[User]:
        users = list(self._users_by_id.values())
        # Simple filtering by role/status if provided
        if filters:
            role = filters.get("role")
            status = filters.get("status")
            if role:
                users = [u for u in users if u.role.value == role]
            if status:
                users = [u for u in users if u.status.value == status]
        return users[offset : offset + limit]

    async def count(self, filters: Optional[dict] = None) -> int:
        return len(await self.list_all(filters=filters))

    async def exists_by_email(self, email: Email) -> bool:
        return email.value.lower() in self._users_by_email

    async def exists_by_username(self, username: str) -> bool:
        return username.lower() in self._users_by_username

    async def find_by_role(self, role: str) -> List[User]:
        return [u for u in self._users_by_id.values() if u.role.value == role]

    async def search(self, query: str, limit: int = 50) -> List[User]:
        q = query.lower()
        results = [
            u
            for u in self._users_by_id.values()
            if q in u.email or q in u.username or q in u.full_name.lower()
        ]
        return results[:limit]


