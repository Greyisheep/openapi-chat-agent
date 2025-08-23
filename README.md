# 🤖 OpenAPI Conversational Agent Platform

**Transform any OpenAPI specification into an intelligent conversational agent using Google ADK**

## 🌐 Live Demo

**Try it now:** [https://paradise-newman-shareholders-earning.trycloudflare.com](https://paradise-newman-shareholders-earning.trycloudflare.com)

Access the interactive API documentation at: `/docs`

## ✨ Features

- 🔗 **OpenAPI Integration**: Convert any OpenAPI spec into functional tools
- 🧠 **Google ADK Agents**: Powered by real Google ADK with Gemini models
- 📞 **Tool Execution Monitoring**: Before/after callbacks for all API interactions
- 🎯 **Custom Instructions**: Combine system prompts with user-specific context
- 🔐 **Secure Credential Storage**: Encrypted API key handling
- 🐳 **Docker Ready**: Modern containerized deployment with Docker Compose
- 🚀 **CI/CD Pipeline**: Automated deployment with GitHub Actions
- 🌐 **HTTPS Tunnel**: Secure access via Cloudflare Tunnel
- 📊 **Conversation History**: Track all interactions and tool executions
- 🛠️ **RESTful API**: Full API for programmatic access

## 🚀 Quick Start

### Option 1: Use the Live Demo
Visit [https://paradise-newman-shareholders-earning.trycloudflare.com/docs](https://paradise-newman-shareholders-earning.trycloudflare.com/docs) and interact with the API directly.

### Option 2: Run Locally

**With Docker (Recommended):**
```bash
git clone https://github.com/Greyisheep/openapi-chat-agent.git
cd openapi-chat-agent
docker compose up -d
```

**Or Build from Source:**
```bash
pip install -e .
uvicorn app.main:app --reload
```

**Health Check:**
```bash
curl https://paradise-newman-shareholders-earning.trycloudflare.com/health
# or locally: curl http://localhost:8000/health
```

**Create an Agent:**

```bash
curl -X POST https://paradise-newman-shareholders-earning.trycloudflare.com/api/v1/agents/ \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Petstore Manager",
    "openapi_spec": {
      "openapi": "3.0.0",
      "info": {"title": "Pet Store", "version": "1.0.0"},
      "servers": [{"url": "https://petstore.swagger.io/v2"}],
      "paths": {
        "/pet/findByStatus": {
          "get": {
            "operationId": "findPetsByStatus",
            "parameters": [{"name": "status", "in": "query", "required": true, "schema": {"type": "string"}}],
            "responses": {"200": {"description": "OK"}}
          }
        }
      }
    },
    "user_api_key": "your-api-key",
    "user_instructions": "You help manage my pet store. Be friendly and provide clear summaries."
  }'
```

**Chat with Agent:**

```bash
# Replace {agent_id} with the returned agent ID
curl -X POST https://paradise-newman-shareholders-earning.trycloudflare.com/api/v1/agents/{agent_id}/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "Show me all available pets"}'
```

**View Tool Execution History:**

```bash
curl https://paradise-newman-shareholders-earning.trycloudflare.com/api/v1/agents/{agent_id}/tool-executions
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/agents/` | Create new agent |
| `GET` | `/api/v1/agents/` | List all agents |
| `GET` | `/api/v1/agents/{id}` | Get agent info |
| `POST` | `/api/v1/agents/{id}/chat` | Chat with agent |
| `GET` | `/api/v1/agents/{id}/tools` | List agent's available tools |
| `GET` | `/api/v1/agents/{id}/conversations` | Get conversation history |
| `GET` | `/api/v1/agents/{id}/tool-executions` | Get tool execution history |
| `DELETE` | `/api/v1/agents/{id}` | Delete agent |

**Interactive Documentation:** [https://paradise-newman-shareholders-earning.trycloudflare.com/docs](https://paradise-newman-shareholders-earning.trycloudflare.com/docs)

## 🏗️ Architecture

- **🧠 ADK LLM Agents**: Real Google ADK agents powered by Gemini models
- **🔧 OpenAPI Toolsets**: Automatic tool generation from OpenAPI specifications
- **📊 Callback System**: Before/after hooks for comprehensive tool execution monitoring
- **🛡️ Graceful Fallback**: Works with or without ADK installed
- **🔐 Security**: Encrypted API key storage and secure credential handling
- **☁️ Cloud-Ready**: Containerized with Docker and deployed via CI/CD

## 🚀 Deployment

This project features **automated deployment** with every push to the main branch:

1. **GitHub Actions** triggers on push to `main`
2. **Builds** Docker container on Hetzner Cloud
3. **Deploys** with zero downtime
4. **Cloudflare Tunnel** provides secure HTTPS access

### Infrastructure
- **Server**: Hetzner Cloud VPS
- **Container**: Docker + Docker Compose
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
