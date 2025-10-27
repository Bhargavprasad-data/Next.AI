"""
Database models for MongoDB
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from bson import ObjectId


# User Models
class User(BaseModel):
    """User model (database document)"""
    email: EmailStr
    username: str
    hashed_password: str
    created_at: datetime = datetime.utcnow()
    is_active: bool = True


class UserCreate(BaseModel):
    """User creation schema"""
    email: EmailStr
    username: str
    password: str


class UserResponse(BaseModel):
    """User response schema"""
    id: str
    email: EmailStr
    username: str
    created_at: datetime
    is_active: bool


# Chat Models
class Message(BaseModel):
    """Chat message model (database document)"""
    user_id: str
    content: str
    role: str  # 'user' or 'assistant'
    created_at: datetime = datetime.utcnow()
    conversation_id: Optional[str] = None
    metadata: Optional[dict] = {}


class MessageCreate(BaseModel):
    """Message creation schema"""
    content: str
    role: str = "user"


class MessageResponse(BaseModel):
    """Message response schema"""
    id: str
    user_id: str
    content: str
    role: str
    created_at: datetime


# Chat Request/Response
class ChatRequest(BaseModel):
    """Chat request schema"""
    message: str
    context_id: Optional[str] = None  # For conversation continuity


class ChatResponse(BaseModel):
    """Chat response schema"""
    response: str
    context_id: str
    tokens_used: Optional[int] = None
    ai_model: Optional[str] = None  # Renamed from model_used to avoid Pydantic conflict


# Token Models
class Token(BaseModel):
    """JWT Token model"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data model"""
    email: Optional[str] = None

