import json
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from llm.client import get_llm

llm = get_llm()

def chat_node(state: AgentState) -> AgentState:
    response = llm.invoke(state["messages"])
    return {
        "messages": [response],
        "status": "done"
    }