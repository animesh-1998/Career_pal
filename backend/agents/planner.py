import json
import re
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from llm.client import get_llm


llm = get_llm()

with open(r".\llm\prompts\planner_prompt.txt", "r", encoding="utf-8") as f:
    PLANNER_SYSTEM_PROMPT = f.read()

def extract_json(raw: str) -> str:
    """
    Extract JSON object from raw LLM output regardless of what surrounds it.
    Handles three cases:
    - Pure JSON response
    - JSON wrapped in ```json ... ``` fences
    - JSON preceded or followed by prose text
    """
    raw = raw.strip()

    # Case 1: strip markdown fences
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw.strip())
        return raw.strip()

    # Case 2: find the first { and last } — extract everything between them
    start = raw.find("{")
    end   = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start:end + 1]

    return raw  # fallback — let json.loads produce the error

def planner_node(state: AgentState) -> dict:
    messages = state.get("messages", [])

    # Build conversation history for planner context
    # Limit to last 10 messages to avoid bloating the context
    history = messages[-5:] if len(messages) > 10 else messages

    # Format history as a readable string
    history_text = ""
    for msg in history[:-1]:  # everything except the last message
        role = type(msg).__name__.replace("Message", "")
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        history_text += f"{role}: {content}\n"

    last_message = messages[-1]

    # If replanning after clarification
    if state.get("clarification_answer"):
        user_input = (
            f"Conversation history:\n{history_text}\n"
            f"Original query: {state['original_query']}\n"
            f"Clarification answer: {state['clarification_answer']}"
        )
    else:
        user_input = (
            f"Conversation history:\n{history_text}\n"
            f"Current user message: {last_message.content}"
        )

    response = llm.invoke([
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ])

    print("Planner raw response:\n", response.content)

    try:
        raw = extract_json(response.content)
        data = json.loads(raw)
        print("Planner parsed output:", data)

        # ── Case 1: cannot_fulfill ───────────────────────────────
        if data.get("status") == "cannot_fulfill":
            print("Planner: cannot fulfill request")
            return {
                "plan": [],
                "plan_status": "cannot_fulfill",
                "plan_reasoning": data.get("reason", ""),
                "cannot_fulfill_reason": data.get("reason", ""),
                "closest_alternative": data.get("closest_alternative", ""),
                "needs_clarification": False,
                "clarification_question": "",
                "current_step": 0,
                "execution_status": "idle",
            }

        # ── Case 2: clarification needed ────────────────────────
        if data.get("agent") == "clarification_node":
            print("Planner: clarification needed")
            return {
                "plan": [],
                "plan_status": "clarification_needed",
                "plan_reasoning": data.get("reasoning", ""),
                "needs_clarification": True,
                "clarification_question": data.get("clarification_question", ""),
                "current_step": 0,
                "execution_status": "idle",
            }

        # ── Case 3: valid plan ───────────────────────────────────
        raw_plan = data.get("plan", [])

        # Validate every step has required fields — drop malformed steps
        validated_plan = []
        for step in raw_plan:
            if not isinstance(step, dict):
                continue
            if not step.get("agent") or not step.get("description"):
                print(f"Dropping malformed plan step: {step}")
                continue
            validated_plan.append({
                "step": step.get("step", len(validated_plan) + 1),
                "agent": step["agent"],
                "description": step["description"],
                "parallel_with": step.get("parallel_with", None),
            })

        print("Validated plan:", validated_plan)

        return {
            "plan": validated_plan,
            "plan_status": "planned",
            "plan_reasoning": data.get("reasoning", ""),
            "cannot_fulfill_reason": "",
            "closest_alternative": "",
            "needs_clarification": False,
            "clarification_question": "",
            "current_step": 0,
            "step_results": {},          # ← reset here, clears stale results
            "failed_step": None,
            "execution_status": "idle",
            "original_query": user_input,
            "runtime_clarification_needed": False,
            "runtime_clarification_answer": "",
        }

    except json.JSONDecodeError as e:
        # LLM returned something unparseable — treat as cannot_fulfill
        print(f"Planner JSON parse error: {e}")
        return {
            "plan": validated_plan,
            "plan_status": "planned",
            "plan_reasoning": data.get("reasoning", ""),
            "cannot_fulfill_reason": "",
            "closest_alternative": "",
            "needs_clarification": False,
            "clarification_question": "",
            "current_step": 0,
            "step_results": {},          # ← reset here, clears stale results
            "failed_step": None,
            "execution_status": "idle",
            "original_query": user_input,
            "runtime_clarification_needed": False,
            "runtime_clarification_answer": "",
        }