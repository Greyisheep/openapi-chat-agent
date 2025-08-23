# OpenAPI Chat Agent

A chat agent that can interact with OpenAPI specifications and provide intelligent responses.

## Features

- Chat interface for OpenAPI specifications
- Intelligent agent responses
- Docker containerization
- CI/CD pipeline with GitHub Actions

## Quick Start

1. Clone the repository
2. Install dependencies: `pip install -e .`
3. Run the application: `uvicorn app.main:app --reload`

## Docker

Build and run with Docker Compose:

```bash
docker compose up -d
```

## CI/CD

This project uses GitHub Actions for automated deployment to Hetzner Cloud.

**Test deployment triggered!** 🚀

# OpenAPI Conversational Agent Platform (PoC)

**Transform any OpenAPI specification into a conversational agent using Google ADK**

## Features

- **Google ADK Integration**: Uses real ADK LLM agents with OpenAPI toolsets
- **Before/After Tool Callbacks**: Monitor and log all API interactions
- **User-Provided Instructions**: Combine system instructions with user context
- **Secure API Key Handling**: Encrypted storage of user credentials
- **Docker + uv**: Modern containerized deployment

## Quick Start

**Build and Run:**

```bash
docker build -t openapi-chat-agent .
docker run --rm -p 8000:8000 openapi-chat-agent
```

**Health Check:**

```bash
curl http://localhost:8000/health
```

**Create an Agent:**

```bash
curl -X POST http://localhost:8000/api/v1/agents/ \
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
curl -X POST http://localhost:8000/api/v1/agents/{agent_id}/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "Show me all available pets"}'
```

**View Tool Execution History:**

```bash
curl http://localhost:8000/api/v1/agents/{agent_id}/tool-executions
```

## API Endpoints

- `GET /health` - Health check
- `POST /api/v1/agents/` - Create new agent
- `GET /api/v1/agents/` - List all agents  
- `GET /api/v1/agents/{id}` - Get agent info
- `POST /api/v1/agents/{id}/chat` - Chat with agent
- `GET /api/v1/agents/{id}/tools` - List agent's available tools
- `GET /api/v1/agents/{id}/conversations` - Get conversation history
- `GET /api/v1/agents/{id}/tool-executions` - Get tool execution history
- `DELETE /api/v1/agents/{id}` - Delete agent

## Architecture

- **ADK LLM Agents**: Real Google ADK agents with Gemini models
- **OpenAPI Toolsets**: Automatic tool generation from OpenAPI specs
- **Callback System**: Before/after hooks for every tool execution
- **Graceful Fallback**: Works with or without ADK installed
