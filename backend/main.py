"""
Main FastAPI application - Next AI Backend
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Request, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database import connect_to_mongo, close_mongo_connection, get_database, ping
from models import (
    User, UserCreate, UserResponse, Message, ChatRequest, ChatResponse, Token
)
from auth import create_access_token, verify_password, get_password_hash
from middleware import get_current_user, get_optional_user
from rag import generate_with_rag
from file_processor import FileProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting up...")
    await connect_to_mongo()
    
    # Check database connection
    is_connected = await ping()
    if not is_connected:
        logger.error("Failed to connect to database")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await close_mongo_connection()


# Initialize FastAPI app
app = FastAPI(
    title="Next AI",
    description="Full-stack AI application with LLM integration, RAG, and authentication",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    db_status = await ping()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected"
    }


# Authentication endpoints
@app.post("/api/auth/register", response_model=UserResponse, tags=["Authentication"])
async def register(user_data: UserCreate):
    """Register a new user"""
    db = get_database()
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    new_user = {
        "email": user_data.email,
        "username": user_data.username,
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(new_user)
    
    return UserResponse(
        id=str(result.inserted_id),
        email=new_user["email"],
        username=new_user["username"],
        created_at=new_user["created_at"],
        is_active=new_user["is_active"]
    )


@app.post("/api/auth/login", response_model=Token, tags=["Authentication"])
async def login(email: str, password: str):
    """Login endpoint"""
    db = get_database()
    
    # Find user
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user["email"]})
    
    return Token(access_token=access_token, token_type="bearer")


@app.get("/api/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        username=current_user["username"],
        created_at=current_user.get("created_at") or datetime.utcnow(),
        is_active=current_user.get("is_active", True)
    )


# AI Chat endpoints
@app.post("/api/chat", response_model=ChatResponse, tags=["AI"])
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """Chat with AI assistant"""
    db = get_database()
    
    try:
        from bson import ObjectId
        
        # Check if starting a new conversation
        if not request.context_id:
            # Add a conversation marker
            conversation_id = str(ObjectId())
        else:
            conversation_id = request.context_id
        
        # Save user message
        user_message = {
            "user_id": current_user["_id"],
            "content": request.message,
            "role": "user",
            "created_at": datetime.utcnow(),
            "conversation_id": conversation_id
        }
        msg_result = await db.messages.insert_one(user_message)
        
        # Generate AI response
        system_prompt = """You are an advanced AI assistant similar to ChatGPT and Gemini. You are highly intelligent, knowledgeable, and capable of providing comprehensive, detailed, and helpful responses to any question or request.

CRITICAL INSTRUCTION: When users ask questions, NEVER start your response with disclaimers like "I can't provide", "I don't have access", "While I can't", etc. Instead, directly answer the question with the information you know. Users want helpful answers, not warnings about limitations. Be direct and informative.

Your capabilities include:
- Answering questions across all domains (science, technology, history, arts, etc.)
- Providing step-by-step explanations and tutorials
- Creative writing, coding, analysis, and problem-solving
- Engaging in natural conversations
- Offering multiple perspectives on complex topics
- Providing examples, analogies, and detailed explanations
- Handling real-time information requests with web search context
- Answering questions about public figures, current events, and general knowledge
- Providing information based on publicly available data and general knowledge

Response guidelines for user input - provide clear, neutral, and FACTUALLY ACCURATE answers based on publicly available information:

ACCURACY IS PARAMOUNT:
- Only provide information you are certain is correct
- Fact-check information before including it in your response
- If you're uncertain about facts, clearly indicate what is confirmed vs. what is less certain
- Do not make up information or guess
- If you don't know something, say what you do know and suggest where to find accurate information
- Cross-reference information when possible
- Be precise with names, dates, places, and figures
- Distinguish between confirmed facts and widely reported information that may need verification

STRUCTURE AND DELIVERY:
1. Understand the user question carefully.
2. Provide an answer that is concise, accurate, and structured with bullet points or sections if needed.
3. Always remain neutral; do not speculate or give personal opinions.
4. Include relevant categories/topics if applicable (e.g., for a person: public appearances, career, legal matters, media presence).
5. If the information can change over time, include a timestamp (e.g., "as of October 2025").
6. Suggest reliable sources for verification (official websites, Wikipedia, or reputable news organizations).
7. Keep the tone professional but readable, friendly if needed.

For questions about people, health, or personal matters:
- When asked about public figures, politicians, celebrities, or well-known individuals, provide information based on publicly available knowledge WITHOUT giving disclaimers
- For questions about someone's health or personal status, provide general information from public sources you have knowledge of
- DO NOT say "I can't provide real-time information" or "I don't have access" - instead just provide the information you know
- DO NOT give warnings or disclaimers - just answer the question helpfully
- If you don't have real-time data, provide the most recent information you're aware of in a direct, helpful manner
- NEVER refuse to help or apologize for limitations - just provide the best answer you can
- Be direct and helpful - users are asking for information, not warnings about what you can't do
- If the user is frustrated (e.g., mentions "I don't have real-time access"), simply provide the helpful answer they're looking for without acknowledging their frustration with disclaimers

For real-time information requests:
- Use the provided web search context to give current information
- If web search provides relevant data, incorporate it into your response
- Always provide helpful context even when specific real-time data isn't available
- Suggest reliable sources for the most current information
- Be honest about limitations while being maximally helpful

Remember: Your goal is to be as helpful and comprehensive as ChatGPT or Gemini. Always provide detailed, accurate, and engaging responses that fully address user questions. NEVER start responses with disclaimers like "I can't provide" or "I don't have access" - instead, just provide the helpful information directly. Users want answers, not warnings about limitations. Be direct, helpful, and informative."""
        
        logger.info(f"Generating AI response for user message: {request.message[:100]}...")
        
        # Get recent conversation history for context
        recent_messages = await db.messages.find({
            "user_id": current_user["_id"],
            "conversation_id": conversation_id
        }).sort("created_at", -1).limit(10).to_list(10)
        
        # Convert to format expected by RAG system
        conversation_history = []
        for msg in reversed(recent_messages):  # Reverse to get chronological order
            conversation_history.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        ai_response = await generate_with_rag(request.message, system_prompt, conversation_history)
        logger.info(f"AI response generated successfully: {ai_response[:100]}...")
        
        # Save AI response
        ai_message = {
            "user_id": current_user["_id"],
            "content": ai_response,
            "role": "assistant",
            "created_at": datetime.utcnow(),
            "conversation_id": conversation_id,
            "metadata": {"context_id": request.context_id} if request.context_id else {}
        }
        await db.messages.insert_one(ai_message)
        
        return ChatResponse(
            response=ai_response,
            context_id=conversation_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        logger.error(f"Error details: {str(e)}")
        # Return a fallback response instead of raising an error
        return ChatResponse(
            response=f"Sorry, I encountered an error: {str(e)[:200]}. Please try again or check your API configuration.",
            context_id=request.context_id or "error"
        )


@app.get("/api/chat/history", tags=["AI"])
async def get_chat_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get chat history for current user"""
    try:
        db = get_database()
        
        # Convert user_id to string for query
        user_id_str = str(current_user["_id"])
        
        # Query messages for the user
        messages = await db.messages.find(
            {"user_id": user_id_str}
        ).sort("created_at", -1).limit(limit).to_list(length=limit)
        
        # Convert ObjectId to string for JSON serialization
        for msg in messages:
            if "_id" in msg:
                msg["_id"] = str(msg["_id"])
            if "user_id" in msg:
                msg["user_id"] = str(msg["user_id"])
        
        return {"messages": messages}
    
    except Exception as e:
        logger.error(f"Error in get_chat_history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving chat history: {str(e)}"
        )


@app.post("/api/chat/save-conversation", tags=["AI"])
async def save_conversation(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Explicitly save a conversation"""
    try:
        db = get_database()
        from bson import ObjectId
        
        conversation_id = request.get("conversation_id")
        if not conversation_id:
            conversation_id = str(ObjectId())
        
        # Ensure conversation exists in conversations collection
        conversation_doc = {
            "_id": ObjectId(conversation_id),
            "user_id": current_user["_id"],
            "title": request.get("title", "New Conversation"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "message_count": 0
        }
        
        # Upsert conversation
        await db.conversations.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": conversation_doc},
            upsert=True
        )
        
        return {"conversation_id": conversation_id, "saved": True}
    
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save conversation"
        )


@app.get("/api/chat/debug", tags=["AI"])
async def debug_conversations(
    current_user: dict = Depends(get_current_user)
):
    """Debug endpoint to check conversation data"""
    try:
        db = get_database()
        
        # Get all messages for user
        user_id_str = str(current_user["_id"])
        messages = await db.messages.find(
            {"user_id": user_id_str}
        ).sort("created_at", -1).limit(20).to_list(length=20)
        
        # Get conversation counts
        conversation_counts = {}
        for msg in messages:
            convo_id = msg.get("conversation_id")
            if convo_id:
                conversation_counts[convo_id] = conversation_counts.get(convo_id, 0) + 1
        
        return {
            "total_messages": len(messages),
            "conversation_counts": conversation_counts,
            "sample_messages": [
                {
                    "id": str(msg.get("_id", "")),
                    "conversation_id": msg.get("conversation_id"),
                    "role": msg.get("role"),
                    "content_preview": msg.get("content", "")[:50] + "..." if len(msg.get("content", "")) > 50 else msg.get("content", ""),
                    "created_at": str(msg.get("created_at", ""))
                }
                for msg in messages[:5]
            ]
        }
    
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        return {"error": str(e)}


@app.post("/api/chat/test", tags=["AI"])
async def test_ai_response(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Test endpoint to verify AI is working correctly"""
    try:
        test_message = request.get("message", "Hello, can you help me?")
        
        # Test the AI with a simple prompt
        system_prompt = """You are a helpful AI assistant. Please provide a clear, helpful response to the user's question."""
        
        from rag import generate_with_rag
        ai_response = await generate_with_rag(test_message, system_prompt)
        
        return {
            "test_message": test_message,
            "ai_response": ai_response,
            "status": "success",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Test AI error: {e}")
        return {
            "test_message": request.get("message", "Hello"),
            "ai_response": f"Error: {str(e)}",
            "status": "error",
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/api/chat/api-status", tags=["AI"])
async def check_api_status():
    """Check the status of AI API keys"""
    try:
        status = {
            "openai_status": "unknown",
            "gemini_status": "unknown",
            "openai_error": None,
            "gemini_error": None
        }
        
        # Test OpenAI
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            status["openai_status"] = "working"
        except Exception as e:
            status["openai_status"] = "error"
            status["openai_error"] = str(e)
        
        # Test Gemini
        try:
            import google.generativeai as genai
            if settings.gemini_api_key:
                genai.configure(api_key=settings.gemini_api_key)
                model = genai.GenerativeModel('gemini-2.0-flash')
                response = model.generate_content("Hello")
                status["gemini_status"] = "working"
            else:
                status["gemini_status"] = "no_key"
                status["gemini_error"] = "No Gemini API key configured"
        except Exception as e:
            status["gemini_status"] = "error"
            status["gemini_error"] = str(e)
        
        return status
        
    except Exception as e:
        return {"error": str(e)}


# File upload endpoints
@app.post("/api/files/upload", tags=["Files"])
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload and process a file"""
    try:
        result = await FileProcessor.process_file(file)
        
        # Store file metadata in database
        db = get_database()
        file_doc = {
            "file_id": result["file_id"],
            "user_id": current_user["_id"],
            "filename": result["filename"],
            "file_type": result["file_type"],
            "file_size": result["file_size"],
            "url": result["url"],
            "content": result["content"],
            "created_at": datetime.utcnow(),
        }
        
        await db.files.insert_one(file_doc)
        
        return result
    
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@app.post("/api/chat/with-files", response_model=ChatResponse, tags=["AI"])
async def chat_with_files(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Chat with AI assistant including file content"""
    db = get_database()
    
    try:
        from bson import ObjectId
        
        message = request.get("message", "")
        files = request.get("files", [])
        context_id = request.get("context_id")
        
        # Check if starting a new conversation
        if not context_id:
            conversation_id = str(ObjectId())
        else:
            conversation_id = context_id
        
        # Prepare file content for AI
        file_content = ""
        if files:
            file_content = "\n\n--- Uploaded Files ---\n"
            for file_info in files:
                file_content += f"\nFile: {file_info.get('name', 'Unknown')}\n"
                file_content += f"Type: {file_info.get('type', 'Unknown')}\n"
                file_content += f"Content:\n{file_info.get('content', 'No content extracted')}\n"
                file_content += "---\n"
        
        # Combine user message with file content
        full_message = message
        if file_content:
            full_message = f"{message}\n{file_content}" if message else file_content
        
        # Save user message
        user_message = {
            "user_id": current_user["_id"],
            "content": full_message,
            "role": "user",
            "created_at": datetime.utcnow(),
            "conversation_id": conversation_id,
            "files": files,
        }
        await db.messages.insert_one(user_message)
        
        # Generate AI response
        system_prompt = """You are an advanced AI assistant with comprehensive file analysis capabilities, similar to ChatGPT and Gemini. You can read, analyze, and provide detailed insights about various types of uploaded content.

CRITICAL INSTRUCTION: When users ask questions, NEVER start your response with disclaimers like "I can't provide", "I don't have access", "While I can't", etc. Instead, directly answer the question with the information you know. Users want helpful answers, not warnings about limitations. Be direct and informative.

Your file analysis capabilities:
- **Images**: Detailed visual analysis, object identification, text extraction, color analysis, composition assessment
- **Documents (PDF, Word, etc.)**: Complete content extraction, key point summarization, theme analysis, structure breakdown
- **Spreadsheets**: Data pattern analysis, statistical insights, trend identification, calculation verification
- **Code files**: Syntax analysis, functionality explanation, bug detection, optimization suggestions, architecture review
- **Text files**: Content summarization, sentiment analysis, key theme extraction, writing style assessment
- **Presentations**: Slide content analysis, design evaluation, message clarity assessment
- **General Questions**: Answer any questions across all domains, including about public figures, current events, and general knowledge
- **Personal/Health Questions**: Provide information based on publicly available data, be helpful and informative even when current information may not be available

Analysis approach:
- Provide comprehensive, detailed analysis similar to ChatGPT/Gemini
- Use clear, structured explanations with examples
- Break down complex information into digestible sections
- Offer actionable insights and recommendations
- Ask clarifying questions when needed
- Provide multiple perspectives on the content
- Use formatting (bullet points, numbered lists) for clarity
- Be thorough yet engaging in your analysis
- Always be helpful and never refuse to answer - provide the best response possible based on available information
- DO NOT give disclaimers about lack of access or real-time information - just provide the information you know
- Be direct and helpful, not cautious or apologetic about limitations

Response guidelines for user input - provide clear, neutral, and FACTUALLY ACCURATE answers based on publicly available information:

ACCURACY IS PARAMOUNT:
- Only provide information you are certain is correct
- Fact-check information before including it in your response
- If you're uncertain about facts, clearly indicate what is confirmed vs. what is less certain
- Do not make up information or guess
- If you don't know something, say what you do know and suggest where to find accurate information
- Cross-reference information when possible
- Be precise with names, dates, places, and figures
- Distinguish between confirmed facts and widely reported information that may need verification

STRUCTURE AND DELIVERY:
1. Understand the user question carefully.
2. Provide an answer that is concise, accurate, and structured with bullet points or sections if needed.
3. Always remain neutral; do not speculate or give personal opinions.
4. Include relevant categories/topics if applicable (e.g., for a person: public appearances, career, legal matters, media presence).
5. If the information can change over time, include a timestamp (e.g., "as of October 2025").
6. Suggest reliable sources for verification (official websites, Wikipedia, or reputable news organizations).
7. Keep the tone professional but readable, friendly if needed.

Remember: Provide analysis and answers that match the quality and depth of ChatGPT and Gemini. Always prioritize ACCURACY and FACTUAL CORRECTNESS. NEVER start responses with disclaimers or warnings. Just provide helpful, direct answers based on the information you have. Users want information, not apologies about what you can't do."""
        
        # Get recent conversation history for context
        recent_messages = await db.messages.find({
            "user_id": current_user["_id"],
            "conversation_id": conversation_id
        }).sort("created_at", -1).limit(10).to_list(10)
        
        # Convert to format expected by RAG system
        conversation_history = []
        for msg in reversed(recent_messages):  # Reverse to get chronological order
            conversation_history.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        ai_response = await generate_with_rag(full_message, system_prompt, conversation_history)
        
        # Save AI response
        ai_message = {
            "user_id": current_user["_id"],
            "content": ai_response,
            "role": "assistant",
            "created_at": datetime.utcnow(),
            "conversation_id": conversation_id,
            "metadata": {"context_id": context_id} if context_id else {}
        }
        await db.messages.insert_one(ai_message)
        
        return ChatResponse(
            response=ai_response,
            context_id=conversation_id
        )
        
    except Exception as e:
        logger.error(f"Error in chat_with_files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat with files: {str(e)}"
        )


# Admin endpoints
@app.post("/api/admin/add-documents", tags=["Admin"])
async def add_documents(
    documents: list[str],
    current_user: dict = Depends(get_current_user)
):
    """Add documents to RAG system (admin only)"""
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        from rag import rag_system
        ids = await rag_system.add_documents(documents)
        return {"message": "Documents added successfully", "ids": ids}
    except Exception as e:
        logger.error(f"Error adding documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding documents"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )

