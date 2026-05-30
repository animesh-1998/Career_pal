from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from agents.graph import build_agent_graph
from schemas.data_model import ChatRequest
import agents.graph as agent
from langgraph.types import Command
import json
from .format import format_tool_result

router = APIRouter()

# print("Workflow:", workflow)  # Debug: print the workflow object

@router.post("/")
async def chat(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}

    return StreamingResponse(
        stream_response(request.message, config),
        media_type="text/event-stream"
    )

def get_status_message(node_name: str) -> str:
    STATUS = {
        "planner_node":        "🧠 Planning your request...",
        "orchestrator_node":   "🎯 Deciding next step...",
        "job_hunt_node": "💼 Searching LinkedIn...",
        "email_node":    "📧 Accessing Gmail...",
        "chat_node":     "💬 Thinking...",
        "tools":    "⚙️  Running tool...",
    }
    return STATUS.get(node_name, "")

async def stream_response(message: str, config: dict):
    workflow = agent.graph
    if workflow is None:
        yield "data: Agent not ready yet\n\n"
        return

    final_output = ""

    async for event in workflow.astream_events(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
        version="v2"
    ):
        
        event_name = event["event"]
        node_name = event.get("name", "")
        print(f"Event: {event_name}, Node: {node_name}")# Debug: print event and node names
        # print("Event",event)
        # always stream status so user knows something is happening
        if event_name == "on_chain_start":
            status = get_status_message(node_name)
            if status:
                yield f"data: __STATUS__{status}\n\n"

        elif event_name == "on_chain_stream" and node_name == "clarification_node":
            chunk = event["data"].get("chunk", {})
            messages = chunk.get("messages", [])
            if messages:
                question = getattr(messages[-1], "content", "")
                if question:
                    print(f"Streaming clarification: {question}")
                    yield f"data: {question}\n\n"

        # collect the last tool result as final output
        elif event_name == "on_chain_stream" and node_name == "tools":
            chunk = event["data"].get("chunk", {})
            messages = chunk.get("messages", [])
            if messages:
                last = messages[-1]
                tool_name = getattr(last, "name", "")
                content = getattr(last, "content", "")
                formatted = format_tool_result(tool_name, content)
                if formatted:
                    final_output = formatted  # ← keep overwriting, last one wins

        # collect agent text responses
        elif event_name == "on_chain_stream" and node_name == "chat_node":
            chunk = event["data"].get("chunk", {})
            messages = chunk.get("messages", [])

            if messages:
                last = messages[-1]

                if isinstance(last, str):
                    content = last
                else:
                    content = getattr(last, "content", "")

                if content and content.strip():
                    encoded = content.replace("\n", "\\n")
                    yield f"data: {encoded}\n\n"

        elif event_name == "on_chain_stream" and node_name in ("job_hunt_node", "email_node"):
            chunk = event["data"].get("chunk", {})
            messages = chunk.get("messages", [])
            if messages:
                last = messages[-1]
                content = getattr(last, "content", "")
                if (
                    content
                    and isinstance(content, str)
                    and content.strip()
                    and not content.strip().startswith("[{")
                    and not content.strip().startswith('{"url')
                ):
                    final_output = content  # ← agent text overrides tool output
                    # yield f"data: {final_output}\n\n"

        # orchestrator says done → stream the final output now
        elif event_name == "on_chain_stream" and node_name == "orchestrator_node":
            chunk = event["data"].get("chunk", {})
            if chunk.get("current_agent") == "done" and final_output:
                encoded = final_output.replace("\n", "\\n")
                print(f"Streaming final output:\n{encoded}")  # Debug: print final output before streaming
                yield f"data: {encoded}\n\n"
                final_output = ""  # reset


# async def resume_response(user_response: str, config: dict):
#     workflow = agent.graph

#     async for event in workflow.astream_events(
#         {"messages": [{"role": "user", "content": user_response}]},
#         config=config,
#         version="v2"
#     ):
#         yield f"data: {json.dumps(event)}\n\n"