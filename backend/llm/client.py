import os
from dotenv import load_dotenv

# Must call this BEFORE accessing env vars
load_dotenv(override=True)
from langchain_ollama import ChatOllama
from functools import lru_cache
from enum import Enum
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

class ModelType(str, Enum):
    FAST = "qwen2.5:3b"    # chat, quick tasks
    SMART = "llama3.1:8b"            # planner, resume editing

@lru_cache(maxsize=4)
def get_llm(temperature=0):
    return ChatOpenAI(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
        temperature=temperature,
        streaming=True
    )
# def get_llm(model: ModelType = ModelType.SMART, temperature: float = 0):
#     return ChatOllama(
#         model=model,
#         temperature=temperature,
#         streaming=True
#     )
    # return ChatGoogleGenerativeAI(
    #     model="gemini-2.0-flash",
    #     google_api_key=os.getenv("GOOGLE_API_KEY"),
    #     temperature=0,
    # )
