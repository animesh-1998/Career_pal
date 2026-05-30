import re
from langchain_core.messages import ToolMessage, AIMessage
from .state import AgentState
from langgraph.graph import END


# ── Helpers ─────────────────────────────────────────────────────────────────

def extract_tool_text(msg) -> str:
    content = msg.content
    if isinstance(content, list):
        return " ".join(i.get("text", "") for i in content if isinstance(i, dict))
    return str(content)


def store_step_results(state: AgentState) -> dict:
    """
    Store the agent's final response for the current step.
    Only stores a result if the current agent has actually run —
    detected by checking if current_agent matches the expected
    agent for this step.
    """
    step_results = dict(state.get("step_results", {}))
    current_step = state.get("current_step", 0)
    plan = state.get("plan", [])
    messages = state.get("messages", [])
    current_agent = state.get("current_agent", "")

    if current_step >= len(plan):
        return step_results

    step_number = plan[current_step].get("step")
    key = str(step_number)

    # Already stored — skip
    if key in step_results:
        return step_results

    # Only store if an agent was actually dispatched for this step
    # current_agent is set by the orchestrator when dispatching
    # If current_agent is empty or "done", no agent has run yet
    expected_agent = get_agent_node(plan[current_step])
    if current_agent != expected_agent:
        print(f"Orchestrator: skipping store — agent '{current_agent}' "
              f"has not run for step {step_number} yet (expected '{expected_agent}')")
        return step_results

    # Walk backwards — find last AIMessage with no tool calls (final response)
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and not msg.tool_calls:
            content = extract_tool_text(msg) or msg.content
            if content:
                step_results[key] = content
                print(f"Orchestrator: stored result for step {step_number}: {content[:100]}")
                break

    return step_results

def build_dependency_context(plan: list, step_index: int, step_results: dict) -> str:
    """
    Build context from results of steps this step depends on.
    Dependency is inferred from parallel_with — if step B has parallel_with=None
    and step A came before it, step A's result is passed as context.
    Steps marked parallel_with another step do NOT get that step's result
    as context (they run simultaneously).
    """
    if step_index == 0 or step_index >= len(plan):
        return ""

    step_obj = plan[step_index]
    parallel_with = step_obj.get("parallel_with")

    parts = []
    for prev in plan[:step_index]:
        prev_step_num = prev.get("step")

        # skip the step this one runs in parallel with — no dependency
        if parallel_with is not None and prev_step_num == parallel_with:
            continue

        result = step_results.get(str(prev_step_num), "")
        if result:
            parts.append(f"Result from step {prev_step_num}:\n{result}")

    return "\n\n".join(parts)


AGENT_MAP = {
    "email_agent":     "email_node",
    "job_hunt_agent":  "job_hunt_node",
    "resume_agent":    "resume_node",
    "chat_agent":      "chat_node",
}

def get_agent_node(step_obj: dict) -> str:
    """Map agent name from plan step to graph node name."""
    agent = step_obj.get("agent", "")
    node = AGENT_MAP.get(agent)
    if not node:
        print(f"Orchestrator warning: unknown agent '{agent}' in plan step — skipping")
    return node


def build_instruction(step_obj: dict, dependency_context: str) -> str:
    """
    Build full instruction for the agent from plan step.
    No tool names — just step number, description, and prior context.
    """
    step_num = step_obj.get("step", "")
    description = step_obj.get("description", "")

    instruction = f"Step {step_num}: {description}"

    if dependency_context:
        instruction += f"\n\nContext from previous steps:\n{dependency_context}"

    return instruction


def last_message_is_tool(state: AgentState) -> bool:
    messages = state.get("messages", [])
    return bool(messages) and isinstance(messages[-1], ToolMessage)


# ── Orchestrator node ────────────────────────────────────────────────────────

def step_is_complete(current_step: int, plan: list, step_results: dict) -> bool:
    """
    Check if the current step has a stored result.
    Takes step_results as a parameter — uses the freshly computed
    version, not the stale one from state.
    """
    if current_step >= len(plan):
        return True

    step_number = plan[current_step].get("step")
    is_complete = str(step_number) in step_results

    print(f"Orchestrator: step_is_complete check — step={step_number}, "
          f"result_exists={is_complete}, keys={list(step_results.keys())}")

    return is_complete

def orchestrator_node(state: AgentState) -> dict:
    plan_status = state.get("plan_status", "")

    # ── Cannot fulfill ───────────────────────────────────────────
    if plan_status == "cannot_fulfill":
        print("Orchestrator: plan cannot be fulfilled")
        return {
            "current_agent": "done",
            "execution_status": "failed",
        }

    # ── Planner-level clarification ──────────────────────────────
    if plan_status == "clarification_needed" or state.get("needs_clarification"):
        print("Orchestrator: routing to clarification node")
        return {
            "current_agent": "clarification_node",
            "execution_status": "paused",
        }

    # ── Runtime clarification from agent ────────────────────────
    if state.get("runtime_clarification_needed"):
        print("Orchestrator: runtime clarification needed, pausing")
        return {
            "current_agent": "clarification_node",
            "execution_status": "paused",
        }

    plan = state.get("plan", [])

    if not plan:
        return {"current_agent": "done", "execution_status": "failed"}

    current_step = state.get("current_step", 0)

    # ── Store step result from freshly merged messages ───────────
    # This runs AFTER LangGraph merges the agent's returned messages
    # into state — so we can capture the agent's final response here
    step_results = store_step_results(state)

    print(f"Orchestrator: current_step={current_step}, plan_length={len(plan)}, "
          f"step_results_keys={list(step_results.keys())}")

    # ── All steps done ───────────────────────────────────────────
    if current_step >= len(plan):
        print("Orchestrator: all steps completed")
        return {
            "current_agent": "done",
            "execution_status": "completed",
            "step_results": step_results,
        }

    # ── Current step complete → advance to next ──────────────────
    # Pass freshly computed step_results, not stale state version
    if step_is_complete(current_step, plan, step_results):
        next_index = current_step + 1
        print(f"Orchestrator: step {current_step} complete, advancing to {next_index}")

        if next_index >= len(plan):
            print("Orchestrator: all steps completed after advancing")
            return {
                "current_agent": "done",
                "execution_status": "completed",
                "current_step": next_index,
                "step_results": step_results,
            }

        next_obj = plan[next_index]
        next_agent = get_agent_node(next_obj)

        if not next_agent:
            return {
                "current_agent": "done",
                "execution_status": "failed",
                "failed_step": next_obj.get("step"),
                "step_results": step_results,
            }

        dependency_context = build_dependency_context(plan, next_index, step_results)
        next_instruction = build_instruction(next_obj, dependency_context)

        print(f"Orchestrator → next step {next_obj.get('step')}: {next_obj.get('description')}")

        return {
            "current_agent": next_agent,
            "current_instruction": next_instruction,
            "current_step": next_index,        # ← step index incremented here
            "step_results": step_results,
            "execution_status": f"executing_step_{next_obj.get('step')}",
        }

    # ── Human approval gate ──────────────────────────────────────
    if state.get("human_approval_required") and not state.get("human_approval_granted"):
        return {
            "current_agent": "human_approval_node",
            "execution_status": "paused",
        }

    # ── Execute current step (first time) ───────────────────────
    step_obj = plan[current_step]
    agent_node = get_agent_node(step_obj)

    if not agent_node:
        return {
            "current_agent": "done",
            "execution_status": "failed",
            "failed_step": step_obj.get("step"),
            "step_results": step_results,
        }

    dependency_context = build_dependency_context(plan, current_step, step_results)
    instruction = build_instruction(step_obj, dependency_context)

    print(f"Orchestrator → dispatching step {step_obj.get('step')}: {step_obj.get('description')}")

    return {
        "current_agent": agent_node,
        "current_instruction": instruction,
        "step_results": step_results,
        "execution_status": f"executing_step_{step_obj.get('step')}",
    }