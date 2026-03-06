from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from agents.graph import build_agent_graph
from schemas.data_model import ChatRequest
import agents.graph as agent

router = APIRouter()

# print("Workflow:", workflow)  # Debug: print the workflow object

@router.post("/")
async def chat(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    
    return StreamingResponse(
        stream_response(request.message, config),
        media_type="text/event-stream"
    )

async def stream_response(message: str, config: dict):
    workflow = agent.graph
    async for event in workflow.astream_events(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
        version="v2"
    ):
        print("Event:", event)  # Debug: print the entire event
        if event["event"] == "on_chain_stream" and event["name"] in ("job_hunt_node", "chat_node"):
            chunk = event["data"].get("chunk", {})
            messages = chunk.get("messages", [])
            if messages:
                last = messages[-1]
                # could be AIMessage object or dict
                if isinstance(last, dict):
                    content = last.get("content", "")
                else:
                    content = last.content
                if content:
                    yield f"data: {content}\n\n"