from langchain_core.messages import SystemMessage
from .state import AgentState
from mcp_client import get_tools
from llm.client import get_llm



llm = get_llm()

with open(".\llm\prompts\email_prompt.txt", "r", encoding="utf-8") as f:
    EMAIL_SYSTEM_PROMPT = f.read()


async def email_node(state: AgentState,tools: list) -> AgentState:
    # get linkedin tools from mcp server
    # tools = await get_tools(["linkedin-mcp-server"])

    if not tools:
        # fallback if MCP server not available
        return {
            **state,
            "messages": [
                {
                    "role": "assistant",
                    "content": "Gmail tools are not available right now. Please try again later."
                }
            ],
            "status": "done"
        }

    # bind linkedin tools to llm
    llm_with_tools = llm.bind_tools(tools)

    response = await llm_with_tools.ainvoke([
        SystemMessage(content=EMAIL_SYSTEM_PROMPT),
        *state["messages"]
    ])

    return {
        "messages": [response],
        "status": "done"
    }
