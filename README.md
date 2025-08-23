# 🤖 OpenAPI Conversational Agent Platform

**Transform any OpenAPI specification into an intelligent conversational agent using Google ADK**

## 🌐 Live Demo

**Try it now:** [https://paradise-newman-shareholders-earning.trycloudflare.com](https://paradise-newman-shareholders-earning.trycloudflare.com)

Access the interactive API documentation at: `/docs`

## ✨ Features

### 🚀 **NEW: Enhanced Features (v1.0)**

- 🔐 **Smart Authentication System**: Automatically detects API auth types (GitHub: `token`, Slack: `Bearer`, others: `API-key`)
- 💰 **User-Provided API Keys**: Users can bring their own Gemini API keys for cost control  
- 🗄️ **PostgreSQL Database**: Production-ready data persistence with Alembic migrations
- 🎯 **Agent Marketplace**: Pre-built templates for GitHub, Slack, HTTPBin, JSONPlaceholder
- 👤 **User Management**: JWT authentication, registration, profiles, password management
- 🛡️ **Enterprise Security**: Token revocation, AES-encrypted API keys, audit logging
- 💬 **Natural Conversations**: Chat with APIs like "create GitHub issue" or "list my repos"

### 🎯 **Core Features**

- 🔗 **OpenAPI Integration**: Convert any OpenAPI spec into functional tools
- 🧠 **Google ADK Agents**: Powered by real Google ADK with Gemini models
- 📞 **Tool Execution Monitoring**: Before/after callbacks for all API interactions
- 🎯 **Custom Instructions**: Combine system prompts with user-specific context
- 🐳 **Docker Ready**: Modern containerized deployment with Docker Compose + PostgreSQL
- 🚀 **CI/CD Pipeline**: Automated deployment with GitHub Actions
- 📊 **Conversation History**: Persistent storage of all interactions and tool executions
- 🛠️ **RESTful API**: Full API for programmatic access

## ⚙️ Environment Configuration

This project uses environment variables for all configuration. Create a `.env` file from the template:

```bash
cp .env.example .env
```

**Required Configuration:**
- `GOOGLE_API_KEY`: Your Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- `SECRET_KEY`: Secure JWT secret (generate with: `openssl rand -base64 32`)
- `POSTGRES_PASSWORD`: Secure database password
- `PGADMIN_DEFAULT_PASSWORD`: PgAdmin interface password

**Security Note:** Never commit the `.env` file to version control. It contains sensitive credentials.

## 🚀 Quick Start

### Option 1: Use the Live Demo
Visit [https://paradise-newman-shareholders-earning.trycloudflare.com/docs](https://paradise-newman-shareholders-earning.trycloudflare.com/docs) and interact with the API directly.

### Option 2: Run Locally with Docker (Recommended)

**Prerequisites:**
- Docker and Docker Compose
- Google Gemini API key

**Setup:**
```bash
git clone https://github.com/Greyisheep/openapi-chat-agent.git
cd openapi-chat-agent

# Create environment file from template
cp .env.example .env

# Edit .env and configure your settings:
# - Set your GOOGLE_API_KEY (get from https://makersuite.google.com/app/apikey)
# - Update database passwords
# - Generate a secure SECRET_KEY: openssl rand -base64 32
nano .env

# Start all services (PostgreSQL + PgAdmin + API)
docker compose up -d
```

**Services:**
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs  
- **PgAdmin**: http://localhost:8080 (see .env for credentials)
- **PostgreSQL**: localhost:5432

### Option 3: Development Setup

```bash
pip install -e .
# Set up PostgreSQL database
# Run alembic upgrade head
uvicorn app.main:app --reload
```

## 🎯 What You Can Do

### 🐙 **GitHub Integration** 
Create a GitHub agent and chat naturally:
```bash
"Get my GitHub user information"
"List my repositories" 
"Create an issue in my openapi-chat-agent repo"
"Show recent commits"
"Get repository information for owner/repo-name"
```

### 💬 **Slack Integration**
Manage Slack workspaces conversationally:
```bash
"Send message to #general channel"
"List all channels"
"Get channel information"
"Create a new channel"
```

### 🧪 **Testing & Development**
Use HTTPBin and JSONPlaceholder for testing:
```bash
"Get my IP address"
"Test HTTP headers"
"Fetch all posts"
"Create a new post"
"Get user information"
```

### 🔗 **Any OpenAPI Service**
The platform works with **any** OpenAPI-compliant API:
- REST APIs with Bearer/Token/API-key authentication
- Automatic tool generation from OpenAPI specs
- Smart authentication detection
- Natural language to API call conversion

## 👤 Authentication & User Management

This platform now requires user authentication. Here's how to get started:

**1. Register a User:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "SecurePass123!",
    "full_name": "Test User"
  }'
```

**2. Login to Get Access Token:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "email_or_username": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**3. Set Your Gemini API Key (Optional but Recommended):**
```bash
curl -X POST http://localhost:8000/auth/api-keys/gemini \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -d '{
    "gemini_api_key": "YOUR_ACTUAL_GEMINI_API_KEY"
  }'
```

## 🎯 Agent Marketplace

Choose from pre-built templates with smart authentication:

### 📋 **Available Templates**

| Template | Authentication | Use Cases |
|----------|---------------|-----------|
| **🐙 GitHub** | `Authorization: token <token>` | Manage repos, issues, PRs, commits |
| **💬 Slack** | `Authorization: Bearer <token>` | Send messages, manage channels |
| **🧪 HTTPBin** | No auth required | HTTP testing, debugging, learning |
| **📄 JSONPlaceholder** | No auth required | Demo posts, comments, users |

### 🚀 **Quick Template Usage**

**Browse Templates:**
```bash
curl http://localhost:8000/marketplace/templates
```

**Create GitHub Agent:**
```bash
curl -X POST http://localhost:8000/marketplace/templates/github/create-agent \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -d '{
    "agent_name": "My GitHub Assistant",
    "api_key": "YOUR_GITHUB_PERSONAL_ACCESS_TOKEN",
    "custom_instructions": "Focus on helping with open source projects."
  }'
```

**Then Chat:**
```bash
curl -X POST http://localhost:8000/api/v1/agents/{agent_id}/chat \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -d '{"message": "Create an issue titled \"Bug Report\" in my main repository"}'
```

## 🔧 Manual Agent Creation

**Create a Custom Agent:**
```bash
curl -X POST http://localhost:8000/api/v1/agents/ \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -d '{
    "name": "Custom API Agent",
    "openapi_spec": { /* your OpenAPI spec */ },
    "user_api_key": "your-api-key",
    "user_instructions": "Custom instructions for your agent"
  }'
```

**Chat with Your Agent:**
```bash
curl -X POST http://localhost:8000/api/v1/agents/{agent_id}/chat \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -d '{"message": "What can you help me with?"}'
```

## 💬 Example Conversations

### 🐙 **GitHub Agent in Action**

```bash
User: "Get my GitHub user information"
Agent: "Here is your GitHub user information:
• Name: Claret Ibeawuchi
• Username: Greyisheep  
• Bio: Data Scientist and Full-Stack Developer...
• Followers: 28
• Following: 120
• Public Repositories: 70"

User: "Get info about my openapi-chat-agent repository"
Agent: "Here is the information for the Greyisheep/openapi-chat-agent repository:
• Language: Python
• Stars: 0 • Forks: 0 • Issues: 0
• Created: 2025-08-23
• Description: Not set
• URL: https://github.com/Greyisheep/openapi-chat-agent"

User: "Create an issue titled 'Add Docker support'"  
Agent: "I'll create that issue for you in your repository..."
```

**✨ The smart authentication system automatically used `Authorization: token <token>` for GitHub!**

## 🔌 API Endpoints

### 🔐 Authentication Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register new user |
| `POST` | `/auth/login` | Login user |
| `POST` | `/auth/token` | Get access token (OAuth2 flow) |
| `POST` | `/auth/logout` | Logout user |
| `GET` | `/auth/me` | Get current user info |
| `PUT` | `/auth/me` | Update user profile |
| `POST` | `/auth/change-password` | Change password |
| `POST` | `/auth/api-keys/gemini` | Set Gemini API key |
| `GET` | `/auth/api-keys` | Get API key status |
| `DELETE` | `/auth/api-keys/gemini` | Remove Gemini API key |

### 🎯 Marketplace Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/marketplace/templates` | List agent templates |
| `GET` | `/marketplace/templates/{id}` | Get template details |
| `GET` | `/marketplace/categories` | List template categories |
| `POST` | `/marketplace/templates/{id}/create-agent` | Create agent from template |

### 🤖 Agent Management Endpoints (🔒 Requires Authentication)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (public) |
| `POST` | `/api/v1/agents/` | Create new agent |
| `GET` | `/api/v1/agents/` | List user's agents |
| `GET` | `/api/v1/agents/{id}` | Get agent info |
| `POST` | `/api/v1/agents/{id}/chat` | Chat with agent |
| `GET` | `/api/v1/agents/{id}/tools` | List agent's available tools |
| `GET` | `/api/v1/agents/{id}/conversations` | Get conversation history |
| `GET` | `/api/v1/agents/{id}/tool-executions` | Get tool execution history |
| `DELETE` | `/api/v1/agents/{id}` | Delete agent |

**Interactive Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs) | [Live Demo](https://paradise-newman-shareholders-earning.trycloudflare.com/docs)

## 🏗️ Architecture

### 🔧 **Core Components**
- **🧠 ADK LLM Agents**: Real Google ADK agents powered by Gemini models
- **🔧 OpenAPI Toolsets**: Automatic tool generation from OpenAPI specifications
- **📊 Callback System**: Before/after hooks for comprehensive tool execution monitoring
- **🛡️ Graceful Fallback**: Works with or without ADK installed

### 🗄️ **Data Layer**
- **PostgreSQL Database**: Production-ready persistence with async SQLAlchemy 2.0
- **Alembic Migrations**: Version-controlled database schema management
- **Encrypted Storage**: API keys and sensitive data are encrypted at rest
- **Connection Pooling**: Optimized database performance

### 🔐 **Security & Authentication**
- **Smart Auth Detection**: Automatically configures authentication for different APIs:
  - GitHub: `Authorization: token <token>`
  - Slack: `Authorization: Bearer <token>` 
  - Others: `X-API-Key: <token>` or custom headers
- **JWT-Based User Auth**: Secure token-based sessions with refresh/revocation
- **AES Encryption**: User API keys encrypted at rest with platform key
- **Password Security**: bcrypt hashing (configurable rounds)
- **Token Management**: Access tokens, refresh tokens, revocation, audit trails
- **Database Security**: Async PostgreSQL with connection pooling and migrations

### 🐳 **Infrastructure**
- **Docker Compose**: Multi-service orchestration (API + PostgreSQL + PgAdmin)
- **Health Checks**: Container and service health monitoring
- **Persistent Volumes**: Data persistence across container restarts
- **Environment Configuration**: Comprehensive environment variable support

### 🎯 **Agent Marketplace**
- **Template System**: Pre-built agent configurations for popular APIs
- **Category Organization**: Organized by use case (Development, Communication, etc.)
- **One-Click Deployment**: Instant agent creation from templates
- **Custom Instructions**: Template-based agents with user customization

## 🚀 Deployment

### 🏠 **Local Development**
```bash
# Quick start with Docker
docker compose up -d

# Access services
API: http://localhost:8000
API Docs: http://localhost:8000/docs
PgAdmin: http://localhost:8080
```

### ☁️ **Production Deployment**
This project features **automated deployment** with every push to the main branch:

1. **GitHub Actions** triggers on push to `main`
2. **Builds** Docker container on Hetzner Cloud
3. **Deploys** with zero downtime
4. **Cloudflare Tunnel** provides secure HTTPS access

### 🔧 **Infrastructure Components**
- **Server**: Hetzner Cloud VPS
- **Container**: Docker + Docker Compose
- **Database**: PostgreSQL 16 with connection pooling
- **Monitoring**: Health checks and logging
- **Tunnel**: Cloudflare Tunnel for HTTPS
- **CI/CD**: GitHub Actions

## 📝 License

This project is a Proof of Concept (PoC) for demonstrating OpenAPI to conversational agent transformation.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Push to main branch (auto-deploys!)

---

**Live Demo**: [https://paradise-newman-shareholders-earning.trycloudflare.com](https://paradise-newman-shareholders-earning.trycloudflare.com) 🚀
