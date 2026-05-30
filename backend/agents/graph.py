from langgraph.graph import StateGraph, START, END
from langchain_core.tools import StructuredTool
from .state import AgentState
from .chat import chat_node
from .planner import planner_node
from .orchestrator import orchestrator_node
from .clarification import clarification_node
from .email import email_node
from .job_hunt import job_hunt_node
from .resume import resume_node
from mcp_client import get_tools


# ── Global graph instance — set by main.py after MCP is ready ───────────────
graph = None
checkpointer = None
session_store = None


# ── Tool cleaning ────────────────────────────────────────────────────────────

def clean_tools(tools: list) -> list:
    """Remove ctx parameter from tool descriptions and schemas."""
    cleaned = []
    for tool in tools:
        # Remove ctx from args_schema properties
        if hasattr(tool, "args_schema") and tool.args_schema:
            schema = (
                tool.args_schema.schema()
                if hasattr(tool.args_schema, "schema")
                else {}
            )
            schema.get("properties", {}).pop("ctx", None)

        # Remove ctx lines from description
        clean_description = "\n".join(
            line for line in tool.description.splitlines()
            if "ctx" not in line.lower()
        )

        clean_tool = StructuredTool(
            name=tool.name,
            description=clean_description,
            args_schema=tool.args_schema,
            coroutine=tool.coroutine,
            response_format=tool.response_format,
            metadata=tool.metadata,
        )
        cleaned.append(clean_tool)
    return cleaned



def route_after_planner(state: AgentState) -> str:
    """
    Three exits from the planner:
    - clarification_needed  → ask user
    - cannot_fulfill        → go to orchestrator which will route to END
    - planned               → go to orchestrator to begin execution
    """
    plan_status = state.get("plan_status", "")

    if plan_status == "clarification_needed" or state.get("needs_clarification"):
        return "clarification_node"

    return "orchestrator_node"


def route_after_clarification(state: AgentState) -> str:
    """After user answers clarification, always replan with full context."""
    return "planner_node"


def route_from_orchestrator(state: AgentState) -> str:
    """
    Orchestrator sets current_agent to signal where to go next.
    All valid targets must be listed in the conditional edges map.
    """
    agent = state.get("current_agent", "")
    print(f"Orchestrator routing to: {agent}")

    if agent == "done":
        return END

    valid_agents = {
        "email_node",
        "job_hunt_node",
        "resume_node",
        "chat_node",
        "clarification_node",
    }

    if agent not in valid_agents:
        print(f"Warning: unknown agent '{agent}' — routing to END")
        return END

    return agent



async def build_agent_graph(checkpointer=None) -> StateGraph:

    linkedin_raw_tools = await get_tools("linkedin")
    email_raw_tools    = await get_tools("email")
    resume_raw_tools   = await get_tools("resume")

    linkedin_tools = clean_tools(linkedin_raw_tools)
    email_tools    = clean_tools(email_raw_tools)
    resume_tools   = clean_tools(resume_raw_tools)

    print(f"LinkedIn tools: {[t.name for t in linkedin_tools]}")
    print(f"Email tools:    {[t.name for t in email_tools]}")
    print(f"Resume tools:   {[t.name for t in resume_tools]}")

    async def email_node_with_tools(state: AgentState):
        return await email_node(state, email_tools)

    async def job_hunt_node_with_tools(state: AgentState):
        return await job_hunt_node(state, linkedin_tools)

    async def resume_node_with_tools(state: AgentState):
        return await resume_node(state, resume_tools)

    builder = StateGraph(AgentState)

    builder.add_node("planner_node",      planner_node)
    builder.add_node("orchestrator_node", orchestrator_node)
    builder.add_node("clarification_node",clarification_node)
    builder.add_node("email_node",        email_node_with_tools)
    builder.add_node("job_hunt_node",     job_hunt_node_with_tools)
    builder.add_node("resume_node",       resume_node_with_tools)
    builder.add_node("chat_node",         chat_node)


    builder.add_edge(START, "planner_node")

    builder.add_conditional_edges(
        "planner_node",
        route_after_planner,
        {
            "clarification_node": "clarification_node",
            "orchestrator_node":  "orchestrator_node",
        }
    )

    builder.add_conditional_edges(
        "clarification_node",
        route_after_clarification,
        {
            "planner_node": "planner_node",
        }
    )

    builder.add_conditional_edges(
        "orchestrator_node",
        route_from_orchestrator,
        {
            "email_node":          "email_node",
            "job_hunt_node":       "job_hunt_node",
            "resume_node":         "resume_node",
            "chat_node":           "chat_node",
            "clarification_node":  "clarification_node",
            END:                    END,
        }
    )

    builder.add_edge("email_node",    "orchestrator_node")
    builder.add_edge("job_hunt_node", "orchestrator_node")
    builder.add_edge("resume_node",   "orchestrator_node")
    # builder.add_edge("clarification_node",     END)

    builder.add_edge("chat_node", END)

    return builder.compile(checkpointer=checkpointer)