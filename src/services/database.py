import asyncpg
from asyncpg import Pool
from typing import Optional, List, Dict, Any
import os
import json
from datetime import datetime


class DatabaseService:
    """Async PostgreSQL database service using asyncpg."""

    def __init__(self):
        self.pool: Optional[Pool] = None
        self.dsn = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/agentdb")

    async def connect(self) -> None:
        """Initialize the connection pool."""
        self.pool = await asyncpg.create_pool(dsn=self.dsn, min_size=2, max_size=10)

    async def disconnect(self) -> None:
        """Close the connection pool."""
        if self.pool:
            await self.pool.close()

    async def create_tables(self) -> None:
        """Create necessary tables if they don't exist."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    session_id VARCHAR(100) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(100) REFERENCES chat_sessions(session_id),
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Fetch a user by username."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
            return dict(row) if row else None

    async def create_user(self, username: str, email: str, hashed_password: str) -> Dict[str, Any]:
        """Insert a new user into the database."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO users (username, email, hashed_password) VALUES ($1, $2, $3) RETURNING *",
                username, email, hashed_password
            )
            return dict(row)

    async def save_message(self, session_id: str, role: str, content: str) -> None:
        """Save a chat message to the database."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO messages (session_id, role, content) VALUES ($1, $2, $3)",
                session_id, role, content
            )

    async def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all messages for a given session."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT role, content, created_at FROM messages WHERE session_id = $1 ORDER BY created_at ASC",
                session_id
            )
            return [dict(row) for row in rows]

    async def create_session(self, user_id: int, session_id: str) -> Dict[str, Any]:
        """Create a new chat session."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO chat_sessions (user_id, session_id) VALUES ($1, $2) RETURNING *",
                user_id, session_id
            )
            return dict(row)


_db_service: Optional[DatabaseService] = None


def get_db() -> DatabaseService:
    """Return the global DatabaseService instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
