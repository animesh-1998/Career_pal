# agents/email.py

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from .state import AgentState
from llm.client import get_llm

llm = get_llm()

with open(r".\llm\prompts\email_prompt.txt", "r", encoding="utf-8") as f:
    EMAIL_SYSTEM_PROMPT = f.read()



def is_stuck(messages: list, tool_name: str, threshold: int = 3) -> bool:
    """
    Detect if the agent is looping on the same tool call without progress.
    Looks at last 8 messages only — avoids false positives from earlier steps.
    """
    recent = messages[-3:]
    count = sum(
        1 for m in recent
        if isinstance(m, AIMessage)
        and hasattr(m, "tool_calls")
        and any(c["name"] == tool_name for c in (m.tool_calls or []))
    )
    return count >= threshold



async def email_node(state: AgentState, tools: list) -> dict:

    # ── Guard: no tools available ────────────────────────────────
    if not tools:
        return {
            "messages": [AIMessage(content="Gmail tools are not available right now.")],
            "execution_status": "failed",
        }

    instruction = state.get("current_instruction", "")
    original_query = state.get("original_query", "")
    existing_messages = state.get("messages", [])


    agent_messages = [
        SystemMessage(content=EMAIL_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"User's original request: {original_query}\n\n"
            f"Your current task: {instruction}\n\n"
            "Complete this task fully using your tools. "
            "Think step by step — you may call multiple tools if needed. "
            "Only stop when the task is done or you need input from the user."
        )),
    ]

    llm_with_tools = llm.bind_tools(tools)
    tool_map = {t.name: t for t in tools}

    new_messages = []
    MAX_ITERATIONS = 6

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"Email ReAct iteration {iteration}")

        all_seen = existing_messages + new_messages
        if is_stuck(all_seen, tool_name="search_emails", threshold=3):
            print("Email node: stuck on search_emails, aborting")
            stuck_msg = AIMessage(
                content="I tried searching your emails multiple times but couldn't find what's needed. "
                        "Could you provide more details about what you're looking for?"
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

        print(f"Email ReAct: tool_calls={[c['name'] for c in (response.tool_calls or [])]}")

        if not response.tool_calls:
            print(f"Email ReAct: completed in {iteration} iteration(s)")
            break

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id   = tool_call["id"]

            print(f"Email ReAct: calling '{tool_name}' args={tool_args}")

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
                    print(f"Email ReAct: tool error — {e}")

            tool_msg = ToolMessage(
                content=str(result),
                tool_call_id=tool_id,
                name=tool_name,
            )
            new_messages.append(tool_msg)
            agent_messages.append(tool_msg)

            print(f"Email ReAct: '{tool_name}' result preview: {str(result)[:200]}")

   
    last_ai = next(
        (m for m in reversed(new_messages) if isinstance(m, AIMessage)), None
    )
    if last_ai and "needs_clarification:" in last_ai.content.lower():
        question = last_ai.content.split("needs_clarification:")[-1].strip()
        print(f"Email ReAct: runtime clarification needed — {question}")
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