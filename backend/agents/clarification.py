from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt
from .state import AgentState

from langchain_core.messages import AIMessage
from .state import AgentState

async def clarification_node(state: AgentState) -> AgentState:
    question = state.get("clarification_question", "Could you clarify your request?")
    print(f"Clarification node: asking '{question}'")
    return {
        **state,
        "messages": [AIMessage(content=question)],
        "needs_clarification": False,
        "clarification_question": question,
    }
