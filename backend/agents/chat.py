import json
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from llm.client import get_llm

llm = get_llm()

def chat_node(state: AgentState) -> AgentState:
    response = llm.invoke(state["messages"])
    print("Chat node response:", response.content)
    return {
        "messages": [response.content],
        "current_step": state.get("current_step", 0) + 1,  # ← advance step
        "status": "done"
    }