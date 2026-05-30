# Career Pal - AI-Powered Career Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Career Pal is an intelligent AI-powered career assistant that automates job hunting, email management, and resume optimization. It acts as your personal career coach, understanding complex requests and delegating tasks to specialized AI agents that seamlessly interact with LinkedIn, Gmail, and resume management tools.

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the Application](#running-the-application)
- [Project Structure](#-project-structure)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 🤖 Intelligent Request Processing
- **Natural Language Understanding**: Converts complex user requests into step-by-step execution plans
- **Smart Clarification System**: Asks for missing information when requests are ambiguous
- **Dynamic Task Routing**: Automatically routes tasks to the appropriate specialized agent
- **Parallel Execution**: Runs multiple tasks simultaneously when dependencies allow
- **Context Awareness**: Maintains conversation history and passes context between execution steps

### 💼 Job Hunt Agent
- Search for jobs on LinkedIn with custom criteria
- Retrieve detailed job descriptions and company information
- Search for professional profiles
- Get company analytics and insights
- Smart loop detection to prevent redundant searches

### 📧 Email Agent
- Search and retrieve emails from Gmail
- Draft and send professional emails with human approval
- Manage email labels and organize inbox
- Read email content and attachments
- Built-in approval workflow for sensitive actions

### 📄 Resume Agent
- Fetch and analyze your resume
- Update specific resume sections
- Export resume in multiple formats (PDF, Word)
- Automatic formatting and validation
- Prevents destructive changes without human approval

### 💬 General Chat
- Provide career advice and guidance
- Answer career-related questions
- Supplement specialized agent responses with context

### 🔄 Session Persistence
- Multi-turn conversations with persistent state
- Resume conversations across sessions
- PostgreSQL-backed state checkpointing
- Session history and management

---

## 🏗️ Architecture

### High-Level Overview

```
┌──────────────────────────────────┐
│  Frontend (React)                 │
│  - Chat Interface                 │
│  - Auth (Login/Signup)            │
│  - Session Management             │
└────────────┬─────────────────────┘
             │ HTTP/SSE
             ▼
┌──────────────────────────────────┐
│  Backend (FastAPI)               │
│  - /api/chat (streaming)         │
│  - /api/auth (login/signup)      │
│  - /api/sessions (management)    │
│                                  │
│  LangGraph Agent Orchestration   │
│  ┌────────────────────────────┐  │
│  │ Planner (create plan)      │  │
│  │ Orchestrator (route tasks) │  │
│  │ Job Hunt Agent             │  │
│  │ Email Agent                │  │
│  │ Resume Agent               │  │
│  │ Chat Agent                 │  │
│  │ Clarification Handler      │  │
│  └────────────────────────────┘  │
│                                  │
│  MCP Client (Tool Provider)      │
│  - LinkedIn Tools                │
│  - Gmail Tools                   │
│  - Resume Tools                  │
└────────────┬─────────────────────┘
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
 LinkedIn  Gmail   Resume
   API      API    Storage
```

### Execution Flow

1. **User Message** → Frontend sends to `/api/chat`
2. **Planner** → Creates execution plan with steps and assigned agents
3. **Clarification** → If needed, asks user for missing information (optional)
4. **Orchestrator** → Routes each step to appropriate agent
5. **Agent ReAct Loop** → Thinks, calls tools, processes results iteratively
6. **Response Streaming** → Real-time updates via Server-Sent Events (SSE)
7. **State Checkpoint** → Session state persisted to PostgreSQL

### Key Components

#### Frontend (`frontend/`)
- **App.js**: Root component with routing and authentication
- **Chat.js**: Main chat interface with real-time streaming
- **Auth.js**: Login/signup pages
- **context/**: Global state management (AuthContext)
- **services/**: API communication layer

#### Backend Core (`backend/`)

**Agents** (`backend/agents/`)
- `state.py`: Shared state definition for the execution graph
- `graph.py`: LangGraph configuration and orchestration logic
- `planner.py`: Generates execution plans from user requests
- `orchestrator.py`: Routes tasks and manages step execution
- `job_hunt.py`: LinkedIn job search and research
- `email.py`: Gmail operations with human approval
- `resume.py`: Resume management and updates
- `chat.py`: General conversation capability
- `clarification.py`: Clarification request handler

**LLM Integration** (`backend/llm/`)
- `client.py`: LLM provider (Groq - llama-3.1-8b)
- `prompts/`: System prompts for each agent

**MCP Servers** (`backend/mcp_client/`)
- `client.py`: Tool fetching from external MCP servers
- `config.py`: MCP server configuration

**API Routes** (`backend/api/routes/`)
- `chat.py`: Chat streaming endpoint with real-time updates
- `auth.py`: User authentication and JWT tokens
- `format.py`: Response formatting utilities
- `sessions.py`: Session management and history

**Memory & Storage** (`backend/memory/`)
- `checkpointer.py`: PostgreSQL-backed state persistence
- `session.py`: Session lifecycle management

**External MCP Servers** (`backend/mcp-server/`)
- **linkedin-mcp-server/**: LinkedIn job search, profiles, company data
- **gmail-mcp-server/**: Gmail operations, email management
- **resume-mcp-server/**: Resume read/write operations

---

## 💻 Tech Stack

### Backend
- **Framework**: FastAPI 0.115.11+
- **LLM Integration**: LangChain Core & OpenAI
- **LLM Provider**: Groq API, OpenAI
- **Database**: PostgreSQL, SQLAlchemy 2.0.39+
- **Server**: Uvicorn 0.34.0+, Gunicorn 23.0.0
- **Authentication**: PyJWT
- **Async Support**: aiohttp, asyncio
- **Task Queue**: Celery 5.4.0+
- **Data Processing**: Pandas, NumPy, scikit-learn
- **Web Framework**: Flask 3.1.0+
- **HTTP Client**: Requests, httpx
- **Serialization**: Pydantic 2.10.6+, Orjson 3.10.15

For the complete list of dependencies, see [requirements.txt](requirements.txt) (216 packages)

### Frontend
- **Framework**: React 19.2.4
- **Routing**: React Router DOM 7.13.1
- **HTTP Client**: Axios 1.13.6
- **Markdown**: React Markdown 10.1.0
- **Build**: React Scripts 5.0.1

### DevOps & Tools
- **Languages**: Python 3.10+, JavaScript/Node.js 18+
- **Package Managers**: pip, uv (Python), npm (Node.js)
- **Containers**: Docker & Docker Compose
- **Testing**: Pytest
- **Git Tools**: GitPython, Dulwich
- **Monitoring & Logging**: OpenTelemetry, MLflow
- **Version Control & DVC**: DVC 3.59.1+, GitPython 3.1.44

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:
- Python 3.10+
- Node.js 18+ and npm
- PostgreSQL 12+
- Docker & Docker Compose (for MCP servers)
- Git

### Required Accounts & Credentials

1. **Groq API Key** - Sign up at [groq.com](https://groq.com) for fast LLM access
2. **Gmail OAuth2** - Set up OAuth credentials in Google Cloud Console
3. **LinkedIn Account** - For LinkedIn scraping (automated profile)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/career-pal.git
cd career-pal
```

#### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# or using uv:
uv pip install -r requirements.txt
```

#### 3. Frontend Setup

```bash
# Navigate to frontend
cd ../frontend

# Install Node dependencies
npm install
```

#### 4. Database Setup

```bash
# Create PostgreSQL database
createdb career_pal

# The backend will auto-create tables on first run
```

### Configuration

#### Backend Environment Variables

Create `backend/.env`:

```env
# LLM Configuration
GROQ_API_KEY=your_groq_api_key_here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/career_pal

# Authentication
SECRET_KEY=your_secret_key_for_jwt
ALGORITHM=HS256

# Gmail OAuth (from Google Cloud Console)
GMAIL_CREDENTIALS_PATH=/path/to/credentials.json

# LinkedIn Profile (for scraping)
LINKEDIN_PROFILE_PATH=/home/user/.linkedin-mcp/profile/

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

#### MCP Server Configuration

The MCP servers are configured in `backend/mcp_client/config.py`. Ensure:

1. **LinkedIn MCP Server**: Requires browser profile
2. **Gmail MCP Server**: Requires OAuth credentials
3. **Resume MCP Server**: Works with local file storage

### Running the Application

#### Development Mode

**Terminal 1 - Backend API:**

```bash
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
python main.py
# Server runs on http://localhost:8000
```

**Terminal 2 - Frontend:**

```bash
cd frontend
npm start
# App runs on http://localhost:3000
```

**Terminal 3 - MCP Servers (optional, auto-started by backend):**

```bash
cd backend/mcp-server
docker-compose up
```

#### Production Mode

```bash
# Build frontend
cd frontend
npm run build

# Run backend with Uvicorn
cd ../backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 📂 Project Structure

```
career-pal/
├── backend/                          # FastAPI backend
│   ├── main.py                       # Application entry point
│   ├── pyproject.toml                # Python dependencies
│   ├── agents/                       # LangGraph agent definitions
│   │   ├── state.py                  # Shared execution state
│   │   ├── graph.py                  # Agent orchestration graph
│   │   ├── planner.py                # Request planning
│   │   ├── orchestrator.py           # Task routing
│   │   ├── job_hunt.py               # LinkedIn integration
│   │   ├── email.py                  # Gmail integration
│   │   ├── resume.py                 # Resume management
│   │   ├── chat.py                   # General conversation
│   │   └── clarification.py          # Clarification requests
│   ├── api/                          # FastAPI routes
│   │   └── routes/
│   │       ├── chat.py               # Chat streaming endpoint
│   │       ├── auth.py               # Authentication
│   │       └── sessions.py           # Session management
│   ├── llm/                          # LLM configuration
│   │   ├── client.py                 # LLM provider setup
│   │   └── prompts/                  # System prompts
│   ├── mcp_client/                   # MCP tool integration
│   │   ├── client.py                 # Tool fetching
│   │   └── config.py                 # MCP server config
│   ├── memory/                       # State persistence
│   │   ├── checkpointer.py           # PostgreSQL checkpointer
│   │   └── session.py                # Session management
│   ├── schemas/                      # Data models
│   │   └── data_model.py
│   ├── tools/                        # Custom tools
│   │   └── resume_tool.py
│   └── mcp-server/                   # MCP server implementations
│       ├── linkedin-mcp-server/      # LinkedIn tools
│       ├── gmail-mcp-server/         # Gmail tools
│       └── resume-mcp-server/        # Resume tools
│
├── frontend/                         # React frontend
│   ├── public/                       # Static assets
│   │   └── index.html
│   ├── src/
│   │   ├── App.js                    # Root component
│   │   ├── index.js                  # Entry point
│   │   ├── App.css                   # Global styles
│   │   ├── pages/                    # Page components
│   │   │   ├── Chat.js               # Chat interface
│   │   │   ├── Login.js              # Login page
│   │   │   └── Signup.js             # Signup page
│   │   ├── variables/
│   │   │   ├── context/              # Context providers
│   │   │   └── services/             # API services
│   │   └── components/               # Reusable components
│   ├── package.json                  # Node dependencies
│   └── README.md                     # Frontend docs
│
├── README.md                         # Project overview (this file)
├── LICENSE                           # MIT License
└── .gitignore                        # Git ignore rules
```

---

## 💬 Usage

### Starting a Chat Session

1. **Navigate to Login**: Open `http://localhost:3000`
2. **Sign Up/Login**: Create an account or log in
3. **Start Chatting**: Type your request in the chat box

### Example Requests

```
"Find me senior software engineer jobs in San Francisco"

"Search my emails for job offers from the last week"

"Update my resume's experience section with my new project work"

"Draft a thank you email to John at TechCorp"

"Help me prepare for interviews at Microsoft"
```

### How It Works

1. **Plan Creation**: Career Pal analyzes your request and creates a multi-step execution plan
2. **Clarification**: If needed, it asks for missing information (location, role type, etc.)
3. **Execution**: Specialized agents handle each step:
   - Job Hunt Agent searches LinkedIn
   - Email Agent manages Gmail
   - Resume Agent handles document updates
4. **Real-Time Updates**: Watch progress with live status messages
5. **Approval Workflow**: Sensitive actions (sending emails) require your confirmation

### Key Features in Action

**Loop Detection**: If an agent gets stuck repeating the same action, it asks for help

**Context Preservation**: Results from previous steps are used in subsequent steps

**Human Approval**: Before sending emails or modifying resumes, you confirm the action

**Streaming Responses**: Responses appear in real-time rather than waiting for completion

---

## 📡 API Documentation

### Chat Endpoint

**POST** `/api/chat`

Stream-based chat with real-time updates.

**Request:**
```json
{
  "message": "Find me jobs in San Francisco",
  "thread_id": "user-123-session-abc"
}
```

**Response:** Server-Sent Events (SSE) stream
```
data: {"type": "status", "content": "🧠 Planning your request..."}
data: {"type": "status", "content": "💼 Searching LinkedIn..."}
data: {"type": "content", "content": "Found 5 senior engineer roles..."}
```

### Authentication Endpoints

**POST** `/api/auth/signup`
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**POST** `/api/auth/login`
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

### Sessions Endpoint

**GET** `/api/sessions`
- List all user sessions

**POST** `/api/sessions`
- Create a new session

**GET** `/api/sessions/{session_id}`
- Get session details and history

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use meaningful variable/function names
- Add docstrings to functions
- Test your changes before submitting
- Update documentation as needed

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙋 Support

If you encounter issues or have questions:

1. Check existing GitHub Issues
2. Review the documentation in each module
3. Create a new GitHub Issue with detailed description
4. Include error logs and reproduction steps

---

## 🛣️ Roadmap

- [ ] Voice input support
- [ ] Calendar integration
- [ ] More LLM provider options
- [ ] Advanced job matching with ML
- [ ] Interview preparation module
- [ ] Salary negotiation assistant
- [ ] Company research dashboard

---

## 📝 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration
- Powered by [Groq](https://groq.com) for fast LLM inference
- LinkedIn integration via custom MCP server
- Gmail integration via Google APIs

---

**Happy Career Building! 🚀**