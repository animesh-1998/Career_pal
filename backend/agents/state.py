from typing import TypedDict, Annotated, List
from langgraph.graph import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]  # chat history
    plan: List[str]
    intent: str                          # planner output
    current_task: str                        # what's executing now
    job_details: dict                        # scraped job info
    resume_path: str                         # path to resume
    modified_resume: str                     # tailored resume content
    human_approval: bool                     # wait for user confirmation
    status: str