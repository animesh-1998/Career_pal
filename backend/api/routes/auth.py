from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import hashlib
import jwt
import datetime
from schemas.data_model import SignupRequest, LoginRequest
import os

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY")

# Simple in-memory store 
users_db = {}

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

@router.post("/signup")
def signup(req: SignupRequest):
    if req.email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(len(users_db) + 1)
    users_db[req.email] = {
        "id": user_id,
        "name": req.name,
        "email": req.email,
        "password": hash_password(req.password)
    }
    
    token = create_token(user_id, req.email)
    return {
        "user": {"id": user_id, "name": req.name, "email": req.email},
        "token": token
    }

@router.post("/login")
def login(req: LoginRequest):
    user = users_db.get(req.email)
    if not user or user["password"] != hash_password(req.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_token(user["id"], user["email"])
    return {
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
        "token": token
    }