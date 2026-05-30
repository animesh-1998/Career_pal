from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from .state import AgentState
from llm.client import get_llm

llm = get_llm()

with open(r".\llm\prompts\resume_prompt.txt", "r", encoding="utf-8") as f:
    RESUME_SYSTEM_PROMPT = f.read()


# ── Stuck detection ──────────────────────────────────────────────────────────

def is_stuck(messages: list, tool_name: str, threshold: int = 3) -> bool:
    """
    Detect if the agent is looping on the same tool without progress.
    Checks last 8 messages to avoid false positives from earlier steps.
    """
    recent = messages[-8:]
    count = sum(
        1 for m in recent
        if isinstance(m, AIMessage)
        and hasattr(m, "tool_calls")
        and any(c["name"] == tool_name for c in (m.tool_calls or []))
    )
    return count >= threshold


# ── Resume node ──────────────────────────────────────────────────────────────

async def resume_node(state: AgentState, tools: list) -> dict:

    # ── Guard: no tools available ────────────────────────────────
    if not tools:
        return {
            "messages": [AIMessage(content="Resume tools are not available right now.")],
            "execution_status": "failed",
        }

    instruction = state.get("current_instruction", "")
    original_query = state.get("original_query", "")
    existing_messages = state.get("messages", [])

    # ── Build starting message list for this step ────────────────
    # Resume agent always fetches before writing, so we remind it explicitly
    agent_messages = [
        SystemMessage(content=RESUME_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"User's original request: {original_query}\n\n"
            f"Your current task: {instruction}\n\n"
            "Complete this task fully using your tools. "
            "If the task requires reading the current resume before making changes, "
            "fetch it first — do not assume its contents. "
            "Think step by step and use as many tool calls as needed. "
            "Only stop when the task is fully complete or you need input from the user."
        )),
    ]

    llm_with_tools = llm.bind_tools(tools)
    tool_map = {t.name: t for t in tools}

    new_messages = []
    MAX_ITERATIONS = 8  # resume tasks can need more steps: fetch → parse → update → export

    # ── ReAct loop ───────────────────────────────────────────────
    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"Resume ReAct iteration {iteration}")

        # Stuck detection — check across existing + new messages
        all_seen = existing_messages + new_messages
        if is_stuck(all_seen, tool_name="get_resume", threshold=3):
            print("Resume node: stuck on get_resume, aborting")
            stuck_msg = AIMessage(
                content="I tried fetching the resume multiple times but encountered "
                        "repeated issues. Could you confirm the resume is accessible "
                        "or try uploading it again?"
            )
            return {
                "messages": new_messages + [stuck_msg],
                "runtime_clarification_needed": True,
                "runtime_clarification_question": stuck_msg.content,
                "execution_status": "paused",
            }

        if is_stuck(all_seen, tool_name="update_resume", threshold=3):
            print("Resume node: stuck on update_resume, aborting")
            stuck_msg = AIMessage(
                content="I attempted to update the resume multiple times but keep "
                        "running into the same issue. Could you clarify what specific "
                        "changes you'd like made?"
            )
            return {
                "messages": new_messages + [stuck_msg],
                "runtime_clarification_needed": True,
                "runtime_clarification_question": stuck_msg.content,
                "execution_status": "paused",
            }

        response = await llm_with_tools.ainvoke(agent_messages)
        new_messages.append(response)
        agent_messages.append(response)

        print(f"Resume ReAct: tool_calls={[c['name'] for c in (response.tool_calls or [])]}")

        # No tool calls → LLM is done reasoning
        if not response.tool_calls:
            print(f"Resume ReAct: completed in {iteration} iteration(s)")
            break

        # ── Execute tool calls ───────────────────────────────────
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id   = tool_call["id"]

            print(f"Resume ReAct: calling '{tool_name}' args={tool_args}")

            tool = tool_map.get(tool_name)
            if not tool:
                result = f"Error: tool '{tool_name}' not found."
            else:
                try:
                    if hasattr(tool, "ainvoke"):
                        result = await tool.ainvoke(tool_args)
                    else:
                        result = tool.invoke(tool_args)
                except Exception as e:
                    result = f"Error executing '{tool_name}': {e}"
                    print(f"Resume ReAct: tool error — {e}")

            tool_msg = ToolMessage(
                content=str(result),
                tool_call_id=tool_id,
                name=tool_name,
            )
            new_messages.append(tool_msg)
            agent_messages.append(tool_msg)

            print(f"Resume ReAct: '{tool_name}' result preview: {str(result)[:200]}")

    # ── Runtime clarification check ──────────────────────────────
    last_ai = next(
        (m for m in reversed(new_messages) if isinstance(m, AIMessage)), None
    )
    if last_ai and "needs_clarification:" in last_ai.content.lower():
        question = last_ai.content.split("needs_clarification:")[-1].strip()
        print(f"Resume ReAct: runtime clarification needed — {question}")
        return {
            "messages": new_messages,
            "runtime_clarification_needed": True,
            "runtime_clarification_question": question,
            "execution_status": "paused",
        }

    return {
        "messages": new_messages,
        "runtime_clarification_needed": False,
        "execution_status": "running",
    }