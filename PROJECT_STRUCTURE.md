# Project Structure

```
AI/
├── backend/                      # FastAPI Backend
│   ├── __init__.py
│   ├── main.py                  # Main FastAPI application
│   ├── config.py                # Configuration settings
│   ├── database.py              # MongoDB connection
│   ├── models.py                # Pydantic models
│   ├── auth.py                  # Authentication utilities
│   ├── middleware.py            # Authentication middleware
│   ├── rag.py                   # RAG implementation
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile               # Backend Dockerfile
│   └── .env                     # Environment variables
│
├── frontend/                    # React.js Frontend
│   ├── src/
│   │   ├── main.jsx             # Entry point
│   │   ├── App.jsx              # Main app component
│   │   ├── index.css            # Global styles
│   │   ├── components/
│   │   │   ├── Login.jsx        # Login/Register UI
│   │   │   ├── ChatInterface.jsx # Chat interface
│   │   │   └── MessageBubble.jsx # Message component
│   │   └── services/
│   │       └── api.js           # API service
│   ├── package.json             # Node dependencies
│   ├── vite.config.js           # Vite configuration
│   ├── index.html               # HTML template
│   ├── Dockerfile               # Frontend Dockerfile
│   └── nginx.conf               # Nginx configuration
│
├── docker-compose.yml           # Docker orchestration
├── README.md                    # Main documentation
├── QUICKSTART.md                # Quick start guide
├── setup.py                     # Setup script
├── example_usage.py             # API usage examples
└── .gitignore                   # Git ignore rules

```

## Backend Structure

### Core Modules

- **main.py**: FastAPI application with routes and endpoints
- **config.py**: Environment-based configuration
- **database.py**: MongoDB connection and utilities
- **models.py**: Pydantic models for data validation
- **auth.py**: JWT authentication and password hashing
- **middleware.py**: Authentication middleware
- **rag.py**: RAG system with OpenAI integration

### API Endpoints

- `/health` - Health check
- `/api/auth/register` - User registration
- `/api/auth/login` - User login
- `/api/auth/me` - Get current user
- `/api/chat` - Send chat message
- `/api/chat/history` - Get chat history
- `/api/admin/add-documents` - Add RAG documents

## Frontend Structure

### Components

- **App.jsx**: Main application with routing
- **Login.jsx**: Authentication UI
- **ChatInterface.jsx**: Main chat interface
- **MessageBubble.jsx**: Individual message display

### Services

- **api.js**: HTTP client with authentication

## Technology Stack

### Backend
- FastAPI (Web Framework)
- MongoDB (Database)
- Motor (Async MongoDB Driver)
- OpenAI (LLM API)
- LangChain (RAG)
- ChromaDB (Vector Store)
- JWT (Authentication)
- Pydantic (Validation)

### Frontend
- React.js (UI Framework)
- Material-UI (Components)
- Axios (HTTP Client)
- Vite (Build Tool)
- React Markdown (Markdown Rendering)

### DevOps
- Docker (Containerization)
- Docker Compose (Orchestration)
- Nginx (Web Server)


