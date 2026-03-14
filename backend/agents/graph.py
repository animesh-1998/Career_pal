from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from .state import AgentState
from .chat import chat_node
from .planner import planner_node
from .job_hunt import job_hunt_node
from .email import email_node
from mcp_client import get_tools


# global graph instance — set by main.py after MCP is ready
graph = None

from langchain_core.tools import StructuredTool

def clean_tools(tools: list) -> list:
    """Remove ctx mentions from tool descriptions and schemas"""
    cleaned = []
    for tool in tools:
        # remove ctx from args_schema
        if hasattr(tool, "args_schema") and tool.args_schema:
            schema = tool.args_schema.schema() if hasattr(tool.args_schema, "schema") else {}
            properties = schema.get("properties", {})
            properties.pop("ctx", None)  # remove ctx from schema

        # clean description — remove ctx lines
        clean_description = "\n".join(
            line for line in tool.description.splitlines()
            if "ctx" not in line.lower()
        )

        # rebuild tool with clean description
        clean_tool = StructuredTool(
            name=tool.name,
            description=clean_description,
            args_schema=tool.args_schema,
            coroutine=tool.coroutine,
            response_format=tool.response_format,
            metadata=tool.metadata
        )
        cleaned.append(clean_tool)
    return cleaned

def route_after_planner(state: AgentState) -> str:
    intent = state.get("intent")

    if intent == "JOB_HUNT":
        return "job_hunt_node"
    elif intent == "EMAIL":
        return "email_node"       # add later
    else:
        return "chat_node"        # default for CHAT and anything else
    
def route_after_tools(state: AgentState) -> str:
    intent = state.get("intent", "CHAT")
    if intent == "EMAIL":
        return "email_node"
    elif intent == "JOB_HUNT":
        return "job_hunt_node"
    return END

async def build_agent_graph():
    linkedin_raw_tools = await get_tools("linkedin")
    email_tools = await get_tools("email")
    linkedin_tools = clean_tools(linkedin_raw_tools)
    print("Tools found:", linkedin_tools)
    print("Tool names:", [t.name for t in linkedin_tools])
    print("Tools found:", email_tools)
    print("Tool names:", [t.name for t in email_tools])
    all_tools = await get_tools()
    async def job_hunt_node_with_tools(state: AgentState):
        return await job_hunt_node(state, linkedin_tools)
    
    async def email_node_with_tools(state: AgentState):
        return await email_node(state, email_tools)

    graph = StateGraph(AgentState)

    graph.add_node("planner_node", planner_node)
    graph.add_node("chat_node", chat_node)
    graph.add_node("job_hunt_node", job_hunt_node_with_tools)
    graph.add_node("email_node", email_node_with_tools)
    graph.add_node("tools", ToolNode(all_tools))          # ← ToolNode(tools) not just tools

    graph.add_edge(START, "planner_node")             # ← was "planner", should be "planner_node"

    graph.add_conditional_edges(
        "planner_node",                               # ← was "planner", should be "planner_node"
        route_after_planner,
        {
            "chat_node": "chat_node",
            "job_hunt_node": "job_hunt_node",
            "email_node": "email_node"
        }
    )

    graph.add_conditional_edges("job_hunt_node", tools_condition, {
        "tools": "tools",
        END: END            # ← correct
    })
    graph.add_conditional_edges("email_node", tools_condition, {
        "tools": "tools",
        END: END            # ← correct
    })

    graph.add_conditional_edges("tools", route_after_tools, {
        "email_node": "email_node",
        "job_hunt_node": "job_hunt_node",
        END: END
    })

    graph.add_edge("chat_node", END)

    return graph.compile()