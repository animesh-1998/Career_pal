from langchain_ollama import ChatOllama
from functools import lru_cache
from enum import Enum

class ModelType(str, Enum):
    FAST = "qwen2.5:3b"    # chat, quick tasks
    SMART = "llama3.1:8b"            # planner, resume editing

@lru_cache(maxsize=4)
def get_llm(model: ModelType = ModelType.SMART, temperature: float = 0):
    return ChatOllama(
        model=model,
        temperature=temperature,
        streaming=True
    )
