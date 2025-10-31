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
from fastapi.staticfiles import StaticFiles

from config import settings
from database import connect_to_mongo, close_mongo_connection, get_database, ping
from models import (
    User, UserCreate, UserResponse, Message, ChatRequest, ChatResponse, Token
)
from auth import create_access_token, verify_password, get_password_hash
from middleware import get_current_user, get_optional_user
from rag import generate_with_rag
from file_processor import FileProcessor
from pydantic import BaseModel
import re
import requests

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

# Serve generated files (PPTs, etc.)
import os
GENERATED_DIR = os.path.join(os.path.dirname(__file__), "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=GENERATED_DIR), name="static")


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
        
        # Ensure system_prompt is always defined
        system_prompt = """You are an advanced AI assistant similar to ChatGPT and Gemini. You are highly intelligent, knowledgeable, and capable of providing comprehensive, detailed, and helpful responses to any question or request.

CRITICAL INSTRUCTION: When users ask questions, NEVER start your response with disclaimers like "I can't provide", "I don't have access", "While I can't", etc. Instead, directly answer the question with the information you know. Users want helpful answers, not warnings about limitations. Be direct and informative.

For questions about real-time or rapidly changing information (like temperature, news, financial figures, weather, etc), NEVER say any form of 'I can't provide' or 'I don't have access.' INSTEAD, provide the most probable, last-known, estimated, or typical information, clearly noting if it may be out of date. Suggest to the user how they can get truly live data (e.g., name a reputable website or app), but ALWAYS give an answer based on your available knowledge.

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

When a table is needed in your response:
- Use correct Markdown table format. Each row must start and end with a single |, the header separator should appear only once directly after the header, and every row must have the same number of columns as the header. Do not output extra pipes, repeated header lines, or malformed Markdown tables.

When a user asks for a summary that includes both anatomical structures and physiological functions (or other logically separate categories), NEVER combine unrelated items into a single table. INSTEAD, output multiple clearly-separated Markdown tables—one for each logical category (example: one table for anatomical components, another for key kidney functions). Each table must have an appropriate header, exactly matching the columns to the content type.

If the user's message is unclear, ambiguous, or could benefit from more information, immediately reply with a polite, explicit CLARIFYING QUESTION before attempting to answer. Wait for the user's reply before providing a solution or information.

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
        
        # Save user message
        user_message = {
            "user_id": current_user["_id"],
            "content": request.message,
            "role": "user",
            "created_at": datetime.utcnow(),
            "conversation_id": conversation_id
        }
        msg_result = await db.messages.insert_one(user_message)
        
        # Check for weather/temperature queries
        weather_pat = re.compile(r'(?:current \s*)?(?:temperature|weather)(?:\s*in)?\s*([a-zA-Z\s]+)', re.IGNORECASE)
        weather_match = weather_pat.search(request.message)
        weather_override = None
        if weather_match and settings.openweathermap_api_key and len(settings.openweathermap_api_key) > 5:
            loc = weather_match.group(1).strip()
            result = fetch_current_weather(loc, api_key=settings.openweathermap_api_key)
            if result:
                temp = result["temp"]
                desc = result["desc"]
                weather_override = f"[Real-time data] The current weather in {result['city']} is {desc}, temperature: {temp}°C. "
        
        # Compose prompt for LLM
        user_prompt = ((weather_override or "") + request.message).strip()
        
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
        
        ai_response = await generate_with_rag(user_prompt, system_prompt, conversation_history)
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

For questions about real-time or rapidly changing information (like temperature, news, financial figures, weather, etc), NEVER say any form of 'I can't provide' or 'I don't have access.' INSTEAD, provide the most probable, last-known, estimated, or typical information, clearly noting if it may be out of date. Suggest to the user how they can get truly live data (e.g., name a reputable website or app), but ALWAYS give an answer based on your available knowledge.

1. Academic and Educational:
    - Math problems (algebra, geometry, calculus, etc.)
    - Science (physics, chemistry, biology, etc.)
    - History, geography, literature, humanities
    - Programming and computer science
2. Technology and Computing:
    - Software/apps use
    - Troubleshooting technical issues
    - Programming/coding (all languages)
    - Gadgets, AI, technology news
3. General Knowledge:
    - Historical events
    - Science and technology explanations
    - Culture, arts, entertainment
    - Sports, news, current events
4. Language and Grammar:
    - Grammar, word meanings, syntax
    - Translation and interpretation
5. Career and Professional:
    - Resume, job search, interview questions
    - Career advice, industry insights
6. Personal and Lifestyle:
    - Health, wellness, counseling
    - Travel, productivity, time management
    - Relationships and self-improvement
7. Business and Entrepreneurship:
    - Marketing, sales, finance, management
    - Business planning and entrepreneurship
8. Love, Relationships, and More:
    - Friendship, emotional well-being, self-care
    - Growth & development, parenting
    - Communication, conflict, dating, romance, mental health

INSTRUCTIONS:
- ALWAYS answer questions in these domains directly, comprehensively, and with clear, structured explanations as needed
- Give step-by-step help for math and science, code with explanations for programming, practical and empathetic advice for personal and career issues
- DO NOT ever refuse to answer unless prohibited by law or safety
- When a question could fit several domains, break down the answer by relevant category
- Users expect answers in any of these categories; you must provide them

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

When a table is needed in your response:
- Use correct Markdown table format. Each row must start and end with a single |, the header separator should appear only once directly after the header, and every row must have the same number of columns as the header. Do not output extra pipes, repeated header lines, or malformed Markdown tables.

When a user asks for a summary that includes both anatomical structures and physiological functions (or other logically separate categories), NEVER combine unrelated items into a single table. INSTEAD, output multiple clearly-separated Markdown tables—one for each logical category (example: one table for anatomical components, another for key kidney functions). Each table must have an appropriate header, exactly matching the columns to the content type.

If the user's message is unclear, ambiguous, or could benefit from more information, immediately reply with a polite, explicit CLARIFYING QUESTION before attempting to answer. Wait for the user's reply before providing a solution or information.

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


# Image generation endpoint
class ImageGenerateRequest(BaseModel):
    prompt: str
    size: str | None = "1024x1024"


@app.post("/api/images/generate", tags=["AI"])
async def generate_image(
    request: ImageGenerateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate an image from a text prompt using OpenAI DALL·E first (fallback to Gemini). Returns base64 image data for inline rendering."""
    size = request.size or "1024x1024"
    allowed_oai_sizes = ["1024x1024", "1792x1024", "1024x1792"]
    oai_size = size if size in allowed_oai_sizes else "1024x1024"

    # Main logic: Try OpenAI first
    from config import settings
    b64 = None
    used_provider = None
    # Try OpenAI DALL·E
    try:
        if settings.openai_api_key and len(settings.openai_api_key) > 10:
            try:
                from openai import AsyncOpenAI
                import aiohttp
                oai = AsyncOpenAI(api_key=settings.openai_api_key)
                res = await oai.images.generate(
                    model="dall-e-3",
                    prompt=request.prompt,
                    n=1,
                    size=oai_size,
                    quality="standard",
                )
                url = res.data[0].url
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        img_bytes = await resp.read()
                import base64
                b64 = base64.b64encode(img_bytes).decode()
                used_provider = "openai"
            except Exception as oae:
                import traceback
                import sys
                logger.error(f"OpenAI image error: {oae}")
                logger.error(''.join(traceback.format_exception(*sys.exc_info())))
                b64 = None
                used_provider = None
    except ImportError:
        pass

    # If OpenAI fails, fallback to Gemini
    if not b64:
        if not settings.gemini_api_key or len(settings.gemini_api_key) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OPENAI_API_KEY and GEMINI_API_KEY not configured or not working. Set at least one in backend environment."
            )
        try:
            import requests
            width, height = 1024, 1024
            try:
                parts = (size or "1024x1024").lower().split("x")
                if len(parts) == 2:
                    width = int(parts[0]); height = int(parts[1])
            except Exception:
                pass
            url = "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0:generateImages"
            params = {"key": settings.gemini_api_key}
            payload = {
                "prompt": {"text": request.prompt},
                "numberOfImages": 1,
                "width": width,
                "height": height,
            }
            resp = requests.post(url, params=params, json=payload, timeout=60)
            if resp.status_code >= 400:
                logger.error(f"Gemini HTTP {resp.status_code}: {resp.text[:500]}")
                raise RuntimeError(f"Gemini HTTP {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            images = data.get("images") or []
            b64 = images and images[0].get("byteContent")
            if not b64:
                try:
                    candidates = data.get("candidates") or []
                    parts = ((candidates[0] or {}).get("content") or {}).get("parts") or []
                    inline = (parts[0] or {}).get("inline_data") or {}
                    b64 = inline.get("data")
                except Exception:
                    b64 = None
            used_provider = "gemini"
        except Exception as ge:
            logger.error(f"Gemini image generation failed: {ge}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gemini image generation failed: {str(ge)}"
            )
    if not b64:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Both OpenAI and Gemini image generation failed."
        )
    return {"image_base64": b64, "size": size, "provider": used_provider}


class PptGenerateRequest(BaseModel):
    prompt: str
    slide_count: int | None = 14
    outline_markdown: str | None = None  # Optional: user-provided outline/content to use directly


@app.post("/api/ppt/generate", tags=["AI"])
async def generate_ppt(
    request: PptGenerateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate a PPTX file based on user input and return a download URL."""
    try:
        # Create content outline using OpenAI for higher quality structure
        from openai import AsyncOpenAI
        import json
        from datetime import datetime
        from pptx import Presentation
        from pptx.util import Inches, Pt

        slide_count = max(3, min(int(request.slide_count or 14), 20))

        outline_schema = (
            "Return ONLY JSON with keys: title (string), subtitle (string, optional), slides (array of objects). "
            "Each slide object must have: 'title' (string), 'bullets' (array of 3-8 strings), and optional 'notes' (string). "
            f"Create about {slide_count} slides. Bullets should be specific, informative, 1 sentence each, with factual details when known. "
            "Use strong structure: Title, Introduction, Background/History, Key Features/Points, Generations/Timeline (if applicable), Special Editions/Variants, Technology & Performance/Data, Cultural Impact/Market, Future/Next Steps, Summary/Conclusion, Q&A. "
            "Avoid generic filler. Include references slide bullets if relevant."
        )

        outline_prompt = (
            f"You are preparing a professional, detailed presentation.\n"
            f"Topic: {request.prompt}\n"
            f"All slides and bullets must focus ONLY on the topic: {request.prompt}. Slides MUST be deeply factual, detailed, and specifically about this topic — no generic templates or filler allowed. Do not include empty or unrelated bullets. Include authentic facts, numbers, history, news, descriptions, analysis, and examples. Never use placeholder content.\n"
            f"{outline_schema}\n"
            "Example minimal JSON format: {\"title\":\"...\",\"subtitle\":\"...\",\"slides\":[{\"title\":\"...\",\"bullets\":[\"...\",\"...\"],\"notes\":\"...\"}]}"
        )

        outline = {
            "title": "Presentation",
            "slides": []
        }

        def parse_outline_markdown(md_text: str) -> dict:
            """Parse a simple outline-like text into our outline dict.
            Supports blocks that look like 'Slide N: Title' and bullet lists under 'Content:'
            or generic headings and '-' bullets. Best-effort; falls back if parsing yields no slides.
            """
            title = request.prompt[:80] if request.prompt else "Presentation"
            subtitle: str | None = None
            slides: list[dict] = []
            if not md_text:
                return {"title": title, "subtitle": subtitle, "slides": slides}
            lines = [l.rstrip() for l in md_text.splitlines()]
            current: dict | None = None
            in_content = False
            for raw in lines:
                line = raw.strip()
                if not line:
                    in_content = False
                    continue
                # Global title/subtitle at document top
                if not slides and not current and line.lower().startswith("title:"):
                    maybe_title = line.split(":",1)[1].strip()
                    if maybe_title:
                        title = maybe_title
                    continue
                if not slides and not current and line.lower().startswith("subtitle:"):
                    maybe_sub = line.split(":",1)[1].strip()
                    if maybe_sub:
                        subtitle = maybe_sub
                    continue
                # Detect a new slide header
                if line.lower().startswith("slide "):
                    # Commit previous slide
                    if current:
                        if current.get("bullets"):
                            slides.append(current)
                    # Extract title after ':' if present
                    slide_title = line.split(":", 1)[1].strip() if ":" in line else line
                    current = {"title": slide_title or "Slide", "bullets": []}
                    in_content = False
                    continue
                # Detect Title: ... within a slide
                if line.lower().startswith("title:"):
                    if not current:
                        current = {"title": line.split(":",1)[1].strip() or "Slide", "bullets": []}
                    else:
                        current["title"] = line.split(":",1)[1].strip() or current.get("title") or "Slide"
                    in_content = False
                    continue
                # Detect Image: ... add as a bullet annotation
                if line.lower().startswith("image:"):
                    if not current:
                        current = {"title": "Slide", "bullets": []}
                    desc = line.split(":",1)[1].strip()
                    if desc:
                        current.setdefault("bullets", []).append(f"Image: {desc}")
                    continue
                # Detect Content: section
                if line.lower().startswith("content:"):
                    in_content = True
                    continue
                # Bullet via dash or asterisk
                if line.startswith("-") or line.startswith("*"):
                    if not current:
                        current = {"title": "Slide", "bullets": []}
                    bullet = line.lstrip("-* ").strip()
                    if bullet:
                        current.setdefault("bullets", []).append(bullet)
                    continue
                # Within a Content: section, treat plain lines as bullets
                if in_content:
                    if not current:
                        current = {"title": "Slide", "bullets": []}
                    current.setdefault("bullets", []).append(line)
                    continue
                # Heading: ... map as title if no current
                if line.lower().startswith("heading:"):
                    if current and current.get("bullets"):
                        slides.append(current)
                    current = {"title": line.split(":",1)[1].strip() or "Slide", "bullets": []}
                    continue
            # Commit last
            if current and current.get("bullets"):
                slides.append(current)
            return {"title": title, "subtitle": subtitle, "slides": slides}

        if request.outline_markdown:
            parsed = parse_outline_markdown(request.outline_markdown)
            if parsed.get("slides"):
                outline = parsed
        elif settings.openai_api_key:
            try:
                client = AsyncOpenAI(api_key=settings.openai_api_key)
                completion = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You create structured presentation outlines as strict JSON only."},
                        {"role": "user", "content": outline_prompt},
                    ],
                    temperature=0.4,
                )
                text = completion.choices[0].message.content
                # Extract JSON if wrapped in code fences
                if "{" in text:
                    json_str = text[text.find("{") : text.rfind("}") + 1]
                    outline = json.loads(json_str)
            except Exception as e:
                logger.warning(f"Outline generation failed, falling back: {e}")

        # Fallback detailed outline if needed or too short
        slides = outline.get("slides") or []
        if len(slides) < max(8, slide_count - 2):
            topic = request.prompt
            base_title = (outline.get("title") or topic or "Presentation")[:80]
            detailed_titles = [
                "Introduction",
                "Origins and Vision",
                "First Generation (1964–1973)",
                "Second Generation (1974–1978)",
                "Third Generation (1979–1993)",
                "Fourth Generation (1994–2004)",
                "Fifth Generation (2005–2014)",
                "Sixth Generation (2015–2023)",
                "Seventh Generation (2024–Present)",
                "Special Editions & Racing Heritage",
                "Technology & Performance",
                "Cultural Impact",
                "Future Outlook",
                "Conclusion & Q&A",
            ]
            fallback_slides = []
            for t in detailed_titles[:slide_count]:
                if t == "Introduction":
                    bullets = [
                        f"Overview of {topic} and why it matters.",
                        "Key characteristics and enduring appeal.",
                        "Context for the discussion and desired outcomes.",
                    ]
                elif t == "Origins and Vision":
                    bullets = [
                        "Foundational goals, design philosophy, and target audience.",
                        "Market conditions and influences at inception.",
                        "Early milestones and launch context.",
                    ]
                elif "First Generation" in t:
                    bullets = [
                        "Design language: long hood, short deck; multiple body styles.",
                        "Powertrains across trims; growing performance variants.",
                        "Market impact and cultural footprint in the late 1960s.",
                    ]
                elif "Second Generation" in t:
                    bullets = [
                        "Downsizing response to fuel crisis and regulations.",
                        "Platform shift and engineering trade-offs.",
                        "Reception, sales performance, and lessons learned.",
                    ]
                elif "Third Generation" in t:
                    bullets = [
                        "Platform change enabling lighter, more aerodynamic designs.",
                        "Return of performance variants and aftermarket ecosystem.",
                        "Longest-running generation and enthusiast following.",
                    ]
                elif "Fourth Generation" in t:
                    bullets = [
                        "Modernization with retro cues and improved refinement.",
                        "Powertrain evolution and chassis handling gains.",
                        "Notable special editions and design refresh.",
                    ]
                elif "Fifth Generation" in t:
                    bullets = [
                        "Retro-futurist styling revisiting classic proportions.",
                        "Technology and safety upgrades; interior improvements.",
                        "High-performance models and motorsport relevance.",
                    ]
                elif "Sixth Generation" in t:
                    bullets = [
                        "Independent rear suspension and global platform strategy.",
                        "Powertrain mix (including efficient turbo options).",
                        "Advanced infotainment and driver-assist tech.",
                    ]
                elif "Seventh Generation" in t:
                    bullets = [
                        "Design evolution with digital cockpit and modern electronics.",
                        "Performance focus with continued V8 availability (where applicable).",
                        "Track-oriented variants and new features.",
                    ]
                elif "Special Editions" in t:
                    bullets = [
                        "Overview of halo models and heritage editions.",
                        "Motorsport variants and competition successes.",
                        "Community, clubs, and enthusiast culture.",
                    ]
                elif "Technology & Performance" in t:
                    bullets = [
                        "Chassis, suspension, and braking advancements.",
                        "Powertrain innovations and performance metrics (where known).",
                        "Weight, aerodynamics, and materials evolution.",
                    ]
                elif "Cultural Impact" in t:
                    bullets = [
                        "Appearances in media and popular culture.",
                        "Design influence on competitors and the segment.",
                        "Sales performance and brand perception over time.",
                    ]
                elif "Future Outlook" in t:
                    bullets = [
                        "Electrification and regulatory landscape.",
                        "Technology roadmap and potential variants.",
                        "Balancing heritage with innovation.",
                    ]
                else:
                    bullets = [
                        "Recap of key takeaways and highlights.",
                        "Strategic implications and next steps.",
                        "Q&A / Discussion.",
                    ]
                fallback_slides.append({"title": t, "bullets": bullets, "notes": ""})

            outline = {"title": base_title, "subtitle": outline.get("subtitle") or "Generated by Next.AI", "slides": fallback_slides}

        prs = Presentation()

        # Title slide
        title_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(title_layout)
        slide.shapes.title.text = outline.get("title") or "Presentation"
        subtitle_text = outline.get("subtitle") or "Generated by Next.AI"
        if slide.placeholders and len(slide.placeholders) > 1:
            slide.placeholders[1].text = subtitle_text

        # Content slides
        bullet_layout = prs.slide_layouts[1]
        for s in outline.get("slides", [])[:slide_count]:
            cs = prs.slides.add_slide(bullet_layout)
            cs.shapes.title.text = s.get("title") or "Slide"
            body = cs.shapes.placeholders[1].text_frame
            body.clear()
            bullets = s.get("bullets") or []
            for i, b in enumerate(bullets[:12]):
                if i == 0:
                    body.text = b
                else:
                    p = body.add_paragraph()
                    p.text = b
                    p.level = 0
            # Add speaker notes if provided
            notes_text = s.get("notes")
            if notes_text:
                notes_slide = cs.notes_slide
                notes_frame = notes_slide.notes_text_frame
                notes_frame.text = notes_text

        # Save file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_base = "presentation"
        filename = f"{safe_base}_{timestamp}.pptx"
        filepath = os.path.join(GENERATED_DIR, filename)
        prs.save(filepath)

        return {"filename": filename, "url": f"/static/{filename}"}
    except Exception as e:
        logger.error(f"Error generating PPT: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PPT: {str(e)}"
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


def fetch_current_weather(city, country_code=None, api_key=None):
    if not api_key:
        return None
    endpoint = "http://api.openweathermap.org/data/2.5/weather"
    q = f"{city},{country_code}" if country_code else city
    params = {"q": q, "appid": api_key, "units": "metric"}
    try:
        resp = requests.get(endpoint, params=params, timeout=6)
        if resp.status_code != 200:
            return None
        data = resp.json()
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        return {"temp": temp, "desc": desc, "city": city.title()}
    except Exception:
        return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )

