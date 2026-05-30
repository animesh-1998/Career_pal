from typing import TypedDict, Annotated, Any, Optional
from langgraph.graph import add_messages


class PlanStep(TypedDict):
    step: int
    agent: str
    description: str
    parallel_with: Optional[int]   


class AgentState(TypedDict):

    messages: Annotated[list, add_messages]
    original_query: str

    plan: list[PlanStep]           
    plan_reasoning: str            
    plan_status: str               
    cannot_fulfill_reason: str     
    closest_alternative: str       # suggestion when cannot_fulfill

    # ── Clarification ───────────────────────────────────────────
    needs_clarification: bool      # True when planner hits language-level ambiguity
    clarification_question: str    # single focused question to ask user
    clarification_answer: str      # user's response, fed back into replanning

    # ── Execution tracking ──────────────────────────────────────
    current_step: int              # index of step currently executing
    current_agent: str             # agent currently executing
    current_instruction: str       # description field of the current PlanStep
    step_results: dict[int, Any]   # keyed by step number, not agent name
    failed_step: Optional[int]     # which step failed, if any
    execution_status: str          # "idle" | "running" | "paused" | "completed" | "failed"

    # ── Runtime ambiguity (agent-level) ─────────────────────────
    runtime_clarification_needed: bool    # agent hit ambiguity during tool execution
    runtime_clarification_question: str   # agent's question to user
    runtime_clarification_answer: str     # user's answer, fed back to the same agent

    # ── Human in the loop ───────────────────────────────────────
    human_approval_required: bool  # True before any destructive action (send, apply)
    human_approval_granted: bool   # user confirmed or rejected
    pending_action: dict           # action waiting for approval {agent, action, payload}

    # ── Tool registry ───────────────────────────────────────────
    tool_map: dict[str, Any]       # agent_name → tools, populated at graph init