from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import os

_checkpointer: AsyncPostgresSaver | None = None

DB_URL = os.getenv("DATABASE_URL")  
_ctx_manager = None


async def setup_checkpointer():
    global _checkpointer, _ctx_manager

    if _checkpointer is None:
        # get context manager
        _ctx_manager = AsyncPostgresSaver.from_conn_string(DB_URL)

        # enter it manually (IMPORTANT)
        _checkpointer = await _ctx_manager.__aenter__()

        # now setup works
        await _checkpointer.setup()

        print("AsyncPostgresSaver initialized")

    return _checkpointer


def get_checkpointer():
    if _checkpointer is None:
        raise RuntimeError("Checkpointer not initialized")
    return _checkpointer


async def close_checkpointer():
    global _ctx_manager

    if _ctx_manager:
        await _ctx_manager.__aexit__(None, None, None)