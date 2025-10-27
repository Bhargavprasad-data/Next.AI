# Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Option 1: Using Docker (Recommended)

```bash
# 1. Clone and navigate to the project
cd AI

# 2. Create environment file
cd backend
cp .env.example .env

# 3. Edit .env and add your OpenAI API key
# OPENAI_API_KEY=your_key_here

# 4. Start all services with Docker
cd ..
docker-compose up -d

# 5. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Manual Setup

**Backend Setup:**

```bash
# 1. Install Python dependencies
cd backend
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key

# 3. Start MongoDB (if not using Docker)
# On Windows:
# Download MongoDB from mongodb.com
# Start MongoDB service

# On Linux/Mac:
# brew install mongodb-community  # Mac
# sudo systemctl start mongod     # Linux

# 4. Run backend
python main.py
```

**Frontend Setup:**

```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Run frontend
npm run dev
```

## 🎯 Testing the Application

1. **Open the frontend**: http://localhost:3000
2. **Register a new account**:
   - Click "Register" tab
   - Enter email, username, and password
   - Submit
3. **Login**:
   - Click "Login" tab
   - Enter credentials
   - Access the chat interface
4. **Start chatting**:
   - Type a message in the input field
   - Press Enter or click Send
   - AI will respond!

## 📡 API Testing

### Using cURL

```bash
# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpass123"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login?email=test@example.com&password=testpass123

# Send message (replace TOKEN with actual token)
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, AI!"}'
```

### Using Python

```bash
python example_usage.py
```

## 🔧 Troubleshooting

### MongoDB Connection Error

```bash
# Start MongoDB service
# Windows:
net start MongoDB

# Linux:
sudo systemctl start mongod

# Mac:
brew services start mongodb-community
```

### OpenAI API Error

1. Check your API key in `backend/.env`
2. Verify you have credits in your OpenAI account
3. Check API rate limits

### Port Already in Use

```bash
# Change port in docker-compose.yml or .env files
# Backend: PORT=8001
# Frontend: npm run dev -- --port 3001
```

## 📝 Next Steps

1. **Add your OpenAI API key** to `backend/.env`
2. **Customize the AI prompt** in `backend/rag.py`
3. **Add RAG documents** via the admin endpoint
4. **Deploy to cloud** (Render, Railway, Vercel)

## 🎉 You're Ready!

Your AI application is now running. Start building amazing AI-powered features!


