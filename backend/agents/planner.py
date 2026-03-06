import json
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from llm.client import get_llm


llm = get_llm()

with open(".\llm\prompts\planner_prompt.txt", "r", encoding="utf-8") as f:
    PLANNER_SYSTEM_PROMPT = f.read()


def planner_node(state: AgentState) -> AgentState:
    # get last user message
    last_message = state["messages"][-1]
    
    response = llm.invoke([
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=last_message.content)
    ])
    
    try:
        plan_data = json.loads(response.content)
    except json.JSONDecodeError:
        # fallback to chat if model doesn't return valid JSON
        plan_data = {
            "intent": "CHAT",
            "plan": ["chat_response"],
            "reasoning": "Failed to parse plan, defaulting to chat"
        }
    
    return {
        "intent": plan_data["intent"],
        "plan": plan_data["plan"],
        "status": "executing"
    }