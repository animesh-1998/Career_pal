from fastapi import APIRouter, HTTPException
import agents.graph as agent
import uuid
from datetime import datetime
from schemas.data_model import CreateSessionRequest

router = APIRouter()


@router.post("/")
def create_session(req: CreateSessionRequest):
    thread_id = f"{req.user_id}-{uuid.uuid4().hex[:8]}"
    return {
        "thread_id": thread_id,
        "created_at": datetime.utcnow().isoformat()
    }


@router.get("/{user_id}")
async def get_sessions(user_id: str):        # ← async
    store = agent.session_store
    if not store:
        raise HTTPException(status_code=503, detail="Session store not ready")
    sessions = await store.get_sessions(user_id)   # ← await
    return {"sessions": sessions}


@router.get("/{thread_id}/messages")
async def get_session_messages(thread_id: str):    # ← async
    store = agent.session_store
    if not store:
        raise HTTPException(status_code=503, detail="Session store not ready")
    messages = await store.get_session_messages(thread_id)  # ← await
    return {"messages": messages}


@router.delete("/{thread_id}")
async def delete_session(thread_id: str):          # ← async
    store = agent.session_store
    if not store:
        raise HTTPException(status_code=503, detail="Session store not ready")
    success = await store.delete_session(thread_id)         # ← await
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete session")
    return {"deleted": thread_id}