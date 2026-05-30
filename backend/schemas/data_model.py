from pydantic import BaseModel



class ChatRequest(BaseModel):
    message: str
    thread_id: str
    is_clarification: bool = False

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class CreateSessionRequest(BaseModel):
    user_id: str
