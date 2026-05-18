from __future__ import annotations

import hashlib
import logging
import secrets
import time
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, delete, insert, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from app.config import AUTH_DB_URL, AUTH_DB_TYPE

logger = logging.getLogger(__name__)


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


@dataclass
class UserRecord:
    username: str
    role: str


class AuthDB:
    def __init__(self, db_url: str = AUTH_DB_URL):
        self.db_url = self._normalize_db_url(db_url)
        engine_kwargs = {
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "future": True,
        }
        if self.db_url.lower().startswith("sqlite"):
            engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
        self.engine: Engine = create_engine(self.db_url, **engine_kwargs)
        self.metadata = MetaData()
        self.users = Table(
            "users",
            self.metadata,
            Column("username", String(255), primary_key=True),
            Column("password_hash", String(128), nullable=False),
            Column("salt", String(64), nullable=False),
            Column("role", String(32), nullable=False, default="user"),
        )
        self.sessions = Table(
            "sessions",
            self.metadata,
            Column("token", String(255), primary_key=True),
            Column("username", String(255), nullable=False),
            Column("created_at", Integer, nullable=False),
        )
        self._init_db()

    @staticmethod
    def _normalize_db_url(db_url: str) -> str:
        normalized = db_url.strip()
        lower_url = normalized.lower()
        if lower_url.startswith("mysql") and "charset=" not in lower_url:
            joiner = "&" if "?" in normalized else "?"
            normalized = f"{normalized}{joiner}charset=utf8mb4"
        return normalized

    def _init_db(self) -> None:
        logger.info("[auth-db] Initializing auth database (%s): %s", AUTH_DB_TYPE, self.db_url)
        self.metadata.create_all(self.engine)
        logger.info("[auth-db] Auth tables are ready")

    def seed_user(self, username: str, password: str, role: str) -> None:
        if self.get_user(username) is not None:
            return
        salt = secrets.token_hex(16)
        password_hash = _hash_password(password, salt)
        with self.engine.begin() as conn:
            conn.execute(
                insert(self.users).values(
                    username=username,
                    password_hash=password_hash,
                    salt=salt,
                    role=role,
                )
            )

    def create_user(self, username: str, password: str, role: str = "user") -> None:
        if self.get_user(username) is not None:
            raise ValueError("User already exists")
        try:
            self.seed_user(username, password, role)
        except IntegrityError as exc:
            raise ValueError("User already exists") from exc

    def get_user(self, username: str) -> Optional[UserRecord]:
        with self.engine.connect() as conn:
            row = conn.execute(
                select(self.users.c.username, self.users.c.role).where(self.users.c.username == username)
            ).mappings().first()
            if not row:
                return None
            return UserRecord(username=row["username"], role=row["role"])

    def verify_user(self, username: str, password: str) -> bool:
        with self.engine.connect() as conn:
            row = conn.execute(
                select(self.users.c.password_hash, self.users.c.salt).where(self.users.c.username == username)
            ).mappings().first()
            if not row:
                return False
            return row["password_hash"] == _hash_password(password, row["salt"])

    def user_exists(self, username: str) -> bool:
        return self.get_user(username) is not None

    def create_session(self, username: str) -> str:
        token = secrets.token_urlsafe(32)
        with self.engine.begin() as conn:
            conn.execute(
                insert(self.sessions).values(
                    token=token,
                    username=username,
                    created_at=int(time.time()),
                )
            )
        return token

    def get_username_by_token(self, token: str) -> Optional[str]:
        with self.engine.connect() as conn:
            row = conn.execute(
                select(self.sessions.c.username).where(self.sessions.c.token == token)
            ).mappings().first()
            return row["username"] if row else None

    def delete_session(self, token: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(delete(self.sessions).where(self.sessions.c.token == token))


auth_db = AuthDB()
auth_db.seed_user("root", "root", "root")
auth_db.seed_user("gxy", "gxy123456", "user")
