"""
REPOSITORY PATTERN
==================
Category : Backend / Structural (Data Access)
Interview tag: "Mediates between the domain/business logic and the data
                mapping layers, acting like an in-memory collection of
                domain objects."

Real-world backend use case in this file
-----------------------------------------
A `User` domain entity with a `UserRepository` interface (abstract base
class). We provide TWO implementations — one in-memory (great for unit
tests), one simulating a SQL database — and business logic (`UserService`)
that depends only on the abstract interface, never on the concrete
storage. This is the core of "swap Postgres for a fake in tests without
touching business logic."
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import itertools


# ---------------------------------------------------------------------------
# Domain entity — plain data, no persistence knowledge whatsoever.
# ---------------------------------------------------------------------------
@dataclass
class User:
    id: Optional[int]
    email: str
    is_active: bool = True


# ---------------------------------------------------------------------------
# Repository interface (the contract). Business logic depends on THIS,
# never on a concrete database client.
# ---------------------------------------------------------------------------
class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        ...

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        ...

    @abstractmethod
    def add(self, user: User) -> User:
        ...

    @abstractmethod
    def delete(self, user_id: int) -> None:
        ...

    @abstractmethod
    def list_active(self) -> list[User]:
        ...


# ---------------------------------------------------------------------------
# Implementation 1: In-memory repository.
# Perfect for unit tests — fast, no real DB needed, same interface.
# ---------------------------------------------------------------------------
class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self._users: dict[int, User] = {}
        self._id_counter = itertools.count(1)

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        return next((u for u in self._users.values() if u.email == email), None)

    def add(self, user: User) -> User:
        user.id = next(self._id_counter)
        self._users[user.id] = user
        print(f"[InMemoryRepo] added {user}")
        return user

    def delete(self, user_id: int) -> None:
        self._users.pop(user_id, None)
        print(f"[InMemoryRepo] deleted user_id={user_id}")

    def list_active(self) -> list[User]:
        return [u for u in self._users.values() if u.is_active]


# ---------------------------------------------------------------------------
# Implementation 2: "SQL-backed" repository (simulated — no real DB
# connection here, but this is where SQLAlchemy/psycopg2 calls would go).
# Notice the business logic never needs to change to use this instead.
# ---------------------------------------------------------------------------
class SqlUserRepository(UserRepository):
    def __init__(self, connection_string: str):
        print(f"[SqlUserRepo] connecting to {connection_string}")
        self._connection_string = connection_string
        # In real life: self._engine = create_engine(connection_string)
        self._fake_table: dict[int, User] = {}
        self._id_counter = itertools.count(1)

    def get_by_id(self, user_id: int) -> Optional[User]:
        print(f"[SqlUserRepo] SELECT * FROM users WHERE id = {user_id}")
        return self._fake_table.get(user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        print(f"[SqlUserRepo] SELECT * FROM users WHERE email = '{email}'")
        return next((u for u in self._fake_table.values() if u.email == email), None)

    def add(self, user: User) -> User:
        user.id = next(self._id_counter)
        self._fake_table[user.id] = user
        print(f"[SqlUserRepo] INSERT INTO users VALUES ({user.id}, '{user.email}')")
        return user

    def delete(self, user_id: int) -> None:
        self._fake_table.pop(user_id, None)
        print(f"[SqlUserRepo] DELETE FROM users WHERE id = {user_id}")

    def list_active(self) -> list[User]:
        print("[SqlUserRepo] SELECT * FROM users WHERE is_active = true")
        return [u for u in self._fake_table.values() if u.is_active]


# ---------------------------------------------------------------------------
# Business logic layer — depends ONLY on the abstract UserRepository.
# This is the payoff: swap InMemory <-> Sql freely, UserService never knows.
# ---------------------------------------------------------------------------
class UserService:
    def __init__(self, repository: UserRepository):
        self._repository = repository

    def register(self, email: str) -> User:
        existing = self._repository.get_by_email(email)
        if existing:
            raise ValueError(f"User with email {email} already exists")
        return self._repository.add(User(id=None, email=email))

    def deactivate(self, user_id: int) -> None:
        user = self._repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"No user with id {user_id}")
        user.is_active = False
        print(f"[UserService] deactivated user_id={user_id}")

    def active_users(self) -> list[User]:
        return self._repository.list_active()


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
def _run_service_demo(repository: UserRepository, label: str):
    print(f"\n=== UserService backed by {label} ===")
    service = UserService(repository)
    service.register("ben@example.com")
    service.register("alice@example.com")
    print("Active users:", service.active_users())

    service.deactivate(1)
    print("Active users after deactivation:", service.active_users())

    try:
        service.register("alice@example.com")  # duplicate -> raises
    except ValueError as e:
        print("Expected error:", e)


def _demo():
    # Same business logic, two totally different storage backends.
    _run_service_demo(InMemoryUserRepository(), "InMemoryUserRepository (e.g. for unit tests)")
    _run_service_demo(SqlUserRepository("postgres://localhost/appdb"), "SqlUserRepository (e.g. for production)")


if __name__ == "__main__":
    _demo()
