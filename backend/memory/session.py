from datetime import datetime
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import asyncpg
import os

class SessionStore:
    def __init__(self, checkpointer: AsyncPostgresSaver):
        self.checkpointer = checkpointer
        self._pool = None

    async def _get_pool(self):
        """Lazy-init a direct asyncpg pool using the same DB URL"""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
        return self._pool

    async def get_sessions(self, user_id: str) -> list[dict]:
        try:
            pool = await self._get_pool()
            # Get the latest checkpoint per thread using checkpoint_id ordering
            query = """
                SELECT DISTINCT ON (thread_id)
                    thread_id,
                    checkpoint_id,
                    metadata
                FROM checkpoints
                WHERE thread_id LIKE $1
                ORDER BY thread_id, checkpoint_id DESC
            """
            async with pool.acquire() as conn:
                rows = await conn.fetch(query, f"{user_id}-%")

            sessions = []
            for row in rows:
                thread_id = row["thread_id"]
                checkpoint_id = row["checkpoint_id"]
                last_message = await self.get_last_human_message(thread_id)
                title = (
                    last_message[:40] + "..."
                    if len(last_message) > 40
                    else last_message or "New Chat"
                )
                sessions.append({
                    "thread_id": thread_id,
                    "title": title,
                    "last_message": last_message,
                    "checkpoint_id": checkpoint_id,  # use as sort key
                })

            # checkpoint_id is UUIDv7 — lexicographic sort = chronological
            sessions.sort(key=lambda x: x["checkpoint_id"], reverse=True)
            return sessions

        except Exception as e:
            print(f"Error fetching sessions: {e}")
            return []

    async def get_last_human_message(self, thread_id: str) -> str:
        try:
            config = {"configurable": {"thread_id": thread_id}}
            checkpoint = await self.checkpointer.aget(config)
            if not checkpoint:
                return ""
            messages = checkpoint.get("channel_values", {}).get("messages", [])

            # Use FIRST human message as session title — more descriptive
            for msg in messages:
                if hasattr(msg, "type") and msg.type == "human":
                    return msg.content

            return ""
        except Exception:
            return ""

    async def get_session_messages(self, thread_id: str) -> list[dict]:
        try:
            config = {"configurable": {"thread_id": thread_id}}
            checkpoint = await self.checkpointer.aget(config)
            if not checkpoint:
                return []
            messages = checkpoint.get("channel_values", {}).get("messages", [])
            result = []
            for msg in messages:
                if hasattr(msg, "type"):
                    if msg.type == "human":
                        result.append({"role": "user", "content": msg.content})
                    elif msg.type == "ai" and msg.content:
                        result.append({"role": "assistant", "content": msg.content})
            return result
        except Exception as e:
            print(f"Error fetching messages: {e}")
            return []

    async def delete_session(self, thread_id: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        "DELETE FROM checkpoints WHERE thread_id = $1", thread_id
                    )
                    await conn.execute(
                        "DELETE FROM checkpoint_writes WHERE thread_id = $1", thread_id
                    )
                    await conn.execute(
                        "DELETE FROM checkpoint_blobs WHERE thread_id = $1", thread_id
                    )  # ← also clean blobs
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False

    async def session_exists(self, thread_id: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT 1 FROM checkpoints WHERE thread_id = $1 LIMIT 1",
                    thread_id
                )
            return result is not None
        except Exception:
            return False

    async def close(self):
        if self._pool:
            await self._pool.close()