"""Pre-built agent templates for popular APIs."""

from typing import Dict, List, Any
from enum import Enum


class AgentCategory(str, Enum):
    """Agent categories for marketplace organization."""
    DEVELOPMENT = "development"
    PRODUCTIVITY = "productivity"
    COMMUNICATION = "communication"
    ECOMMERCE = "ecommerce"
    SOCIAL_MEDIA = "social_media"
    FINANCE = "finance"
    UTILITY = "utility"


class AuthType(str, Enum):
    """Supported authentication types."""
    NONE = "none"
    BEARER = "bearer"  # Authorization: Bearer <token>
    TOKEN = "token"    # Authorization: token <token> (GitHub style)
    API_KEY = "api_key"  # X-API-Key: <token>
    CUSTOM = "custom"  # Custom header format


class AgentTemplate:
    """Template for creating pre-configured agents."""
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        category: AgentCategory,
        openapi_spec: Dict[str, Any],
        default_instructions: str,
        auth_type: str = "bearer",
        auth_header: str = "Authorization",
        auth_prefix: str = None,  # e.g., "Bearer", "token", etc.
        featured: bool = False,
        tags: List[str] = None,
        documentation_url: str = None,
        logo_url: str = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.openapi_spec = openapi_spec
        self.default_instructions = default_instructions
        self.auth_type = auth_type
        self.auth_header = auth_header
        self.auth_prefix = auth_prefix
        self.featured = featured
        self.tags = tags or []
        self.documentation_url = documentation_url
        self.logo_url = logo_url


# GitHub Agent Template
GITHUB_TEMPLATE = AgentTemplate(
    id="github",
    name="GitHub Assistant",
    description="Manage repositories, issues, pull requests, and more on GitHub",
    category=AgentCategory.DEVELOPMENT,
    featured=True,
    tags=["git", "code", "development", "collaboration"],
    documentation_url="https://docs.github.com/en/rest",
    openapi_spec={
        "openapi": "3.0.0",
        "info": {
            "title": "GitHub REST API",
            "version": "1.0.0",
            "description": "GitHub's REST API for managing repositories, issues, and more"
        },
        "servers": [
            {"url": "https://api.github.com"}
        ],
        "security": [
            {"BearerAuth": []}
        ],
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": "GitHub Personal Access Token"
                }
            }
        },
        "paths": {
            "/user": {
                "get": {
                    "operationId": "getUserInfo",
                    "summary": "Get authenticated user information",
                    "responses": {"200": {"description": "User information"}}
                }
            },
            "/user/repos": {
                "get": {
                    "operationId": "listUserRepos",
                    "summary": "List repositories for authenticated user",
                    "parameters": [
                        {
                            "name": "type",
                            "in": "query",
                            "schema": {"type": "string", "enum": ["all", "owner", "member"]},
                            "description": "Repository type filter"
                        }
                    ],
                    "responses": {"200": {"description": "List of repositories"}}
                }
            },
            "/repos/{owner}/{repo}/issues": {
                "get": {
                    "operationId": "listRepoIssues",
                    "summary": "List repository issues",
                    "parameters": [
                        {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                        {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}},
                        {
                            "name": "state",
                            "in": "query",
                            "schema": {"type": "string", "enum": ["open", "closed", "all"]},
                            "description": "Issue state filter"
                        }
                    ],
                    "responses": {"200": {"description": "List of issues"}}
                },
                "post": {
                    "operationId": "createIssue",
                    "summary": "Create a new issue",
                    "parameters": [
                        {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                        {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["title"],
                                    "properties": {
                                        "title": {"type": "string"},
                                        "body": {"type": "string"},
                                        "labels": {"type": "array", "items": {"type": "string"}}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Issue created"}}
                }
            },
            "/repos/{owner}/{repo}/pulls": {
                "get": {
                    "operationId": "listPullRequests",
                    "summary": "List pull requests",
                    "parameters": [
                        {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                        {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}},
                        {
                            "name": "state",
                            "in": "query",
                            "schema": {"type": "string", "enum": ["open", "closed", "all"]},
                            "description": "Pull request state filter"
                        }
                    ],
                    "responses": {"200": {"description": "List of pull requests"}}
                }
            },
            "/repos/{owner}/{repo}": {
                "get": {
                    "operationId": "getRepository",
                    "summary": "Get repository information",
                    "parameters": [
                        {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                        {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "Repository information"}}
                }
            }
        }
    },
    default_instructions="""You are a GitHub assistant that helps users manage their repositories, issues, and pull requests.

Your capabilities include:
- Viewing user and repository information  
- Listing and creating issues
- Managing pull requests
- Browsing repository contents

Always be helpful and provide clear summaries of the information you retrieve. When creating issues or PRs, ask for clarification if the user's request is ambiguous.

For repository references, you can accept formats like "owner/repo" or just "repo" if it's clear from context.""",
    auth_type="token",
    auth_header="Authorization",
    auth_prefix="token"
)


# Slack Agent Template  
SLACK_TEMPLATE = AgentTemplate(
    id="slack",
    name="Slack Assistant",
    description="Send messages, manage channels, and interact with your Slack workspace",
    category=AgentCategory.COMMUNICATION,
    featured=True,
    tags=["messaging", "communication", "team", "collaboration"],
    documentation_url="https://api.slack.com/web",
    openapi_spec={
        "openapi": "3.0.0",
        "info": {
            "title": "Slack Web API",
            "version": "1.0.0",
            "description": "Slack Web API for workspace interaction"
        },
        "servers": [
            {"url": "https://slack.com/api"}
        ],
        "security": [
            {"BearerAuth": []}
        ],
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": "Slack Bot Token"
                }
            }
        },
        "paths": {
            "/auth.test": {
                "get": {
                    "operationId": "testAuth",
                    "summary": "Test API authentication",
                    "responses": {"200": {"description": "Authentication test result"}}
                }
            },
            "/conversations.list": {
                "get": {
                    "operationId": "listChannels",
                    "summary": "List channels in workspace",
                    "parameters": [
                        {
                            "name": "types",
                            "in": "query",
                            "schema": {"type": "string"},
                            "description": "Channel types (public_channel,private_channel,mpim,im)"
                        }
                    ],
                    "responses": {"200": {"description": "List of channels"}}
                }
            },
            "/chat.postMessage": {
                "post": {
                    "operationId": "sendMessage",
                    "summary": "Send a message to a channel",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["channel", "text"],
                                    "properties": {
                                        "channel": {"type": "string", "description": "Channel ID or name"},
                                        "text": {"type": "string", "description": "Message text"},
                                        "as_user": {"type": "boolean", "description": "Send as authenticated user"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Message sent"}}
                }
            },
            "/users.list": {
                "get": {
                    "operationId": "listUsers",
                    "summary": "List workspace users",
                    "responses": {"200": {"description": "List of users"}}
                }
            }
        }
    },
    default_instructions="""You are a Slack assistant that helps users interact with their Slack workspace.

Your capabilities include:
- Sending messages to channels and users
- Listing channels and workspace members
- Testing API authentication

When sending messages, you can reference channels by name (e.g., #general) or ID. Always confirm before sending messages to ensure accuracy.

Be helpful and concise in your responses, and let users know when operations are successful.""",
    auth_type="bearer",
    auth_header="Authorization"
)


# JSONPlaceholder Demo Template
JSONPLACEHOLDER_TEMPLATE = AgentTemplate(
    id="jsonplaceholder",
    name="JSONPlaceholder Demo",
    description="Demo agent using JSONPlaceholder API for testing and development",
    category=AgentCategory.UTILITY,
    featured=False,
    tags=["demo", "testing", "development", "json"],
    documentation_url="https://jsonplaceholder.typicode.com/",
    openapi_spec={
        "openapi": "3.0.0",
        "info": {
            "title": "JSONPlaceholder API",
            "version": "1.0.0",
            "description": "Fake REST API for testing and prototyping"
        },
        "servers": [
            {"url": "https://jsonplaceholder.typicode.com"}
        ],
        "paths": {
            "/posts": {
                "get": {
                    "operationId": "getPosts",
                    "summary": "Get all posts",
                    "responses": {"200": {"description": "List of posts"}}
                },
                "post": {
                    "operationId": "createPost",
                    "summary": "Create a new post",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "body": {"type": "string"},
                                        "userId": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Post created"}}
                }
            },
            "/posts/{id}": {
                "get": {
                    "operationId": "getPost",
                    "summary": "Get a specific post",
                    "parameters": [
                        {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                    ],
                    "responses": {"200": {"description": "Post details"}}
                }
            },
            "/users": {
                "get": {
                    "operationId": "getUsers",
                    "summary": "Get all users",
                    "responses": {"200": {"description": "List of users"}}
                }
            },
            "/users/{id}": {
                "get": {
                    "operationId": "getUser",
                    "summary": "Get a specific user",
                    "parameters": [
                        {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                    ],
                    "responses": {"200": {"description": "User details"}}
                }
            }
        }
    },
    default_instructions="""You are a demo assistant using the JSONPlaceholder API for testing and development.

This is a fake REST API that provides sample data for:
- Posts (blog-style posts with titles and content)
- Users (sample user profiles)
- Comments, albums, photos, and todos

You can help users explore the API, fetch sample data, and demonstrate how REST APIs work. This is perfect for learning and testing purposes.

Note: This is a read-only demo API - while you can make POST requests, they won't actually persist data.""",
    auth_type="none"
)


# HTTPBin Testing Template
HTTPBIN_TEMPLATE = AgentTemplate(
    id="httpbin",
    name="HTTPBin Testing",
    description="HTTP testing service for debugging and testing HTTP requests",
    category=AgentCategory.UTILITY,
    featured=False,
    tags=["testing", "http", "debugging", "development"],
    documentation_url="https://httpbin.org/",
    openapi_spec={
        "openapi": "3.0.0",
        "info": {
            "title": "HTTPBin API",
            "version": "1.0.0",
            "description": "HTTP testing service"
        },
        "servers": [
            {"url": "https://httpbin.org"}
        ],
        "paths": {
            "/get": {
                "get": {
                    "operationId": "testGet",
                    "summary": "Test GET request",
                    "responses": {"200": {"description": "GET request details"}}
                }
            },
            "/post": {
                "post": {
                    "operationId": "testPost",
                    "summary": "Test POST request",
                    "requestBody": {
                        "content": {
                            "application/json": {"schema": {"type": "object"}}
                        }
                    },
                    "responses": {"200": {"description": "POST request details"}}
                }
            },
            "/headers": {
                "get": {
                    "operationId": "getHeaders",
                    "summary": "Get request headers",
                    "responses": {"200": {"description": "Request headers"}}
                }
            },
            "/ip": {
                "get": {
                    "operationId": "getIP",
                    "summary": "Get client IP address",
                    "responses": {"200": {"description": "Client IP"}}
                }
            },
            "/status/{code}": {
                "get": {
                    "operationId": "getStatus",
                    "summary": "Return specific HTTP status code",
                    "parameters": [
                        {"name": "code", "in": "path", "required": True, "schema": {"type": "integer"}}
                    ],
                    "responses": {"default": {"description": "HTTP status response"}}
                }
            }
        }
    },
    default_instructions="""You are an HTTP testing assistant using HTTPBin.

HTTPBin is a testing service that helps debug and test HTTP requests. You can:
- Test different HTTP methods (GET, POST, etc.)
- Inspect headers and request details
- Test different HTTP status codes
- Check client IP and other request information

This is useful for developers testing HTTP clients, debugging API issues, or learning about HTTP protocols.""",
    auth_type="none"
)


# Registry of all available templates
AGENT_TEMPLATES = {
    template.id: template for template in [
        GITHUB_TEMPLATE,
        SLACK_TEMPLATE,
        JSONPLACEHOLDER_TEMPLATE,
        HTTPBIN_TEMPLATE,
    ]
}


def get_template(template_id: str) -> AgentTemplate:
    """Get a specific agent template by ID."""
    return AGENT_TEMPLATES.get(template_id)


def list_templates(category: AgentCategory = None, featured_only: bool = False) -> List[AgentTemplate]:
    """List available agent templates with optional filtering."""
    templates = list(AGENT_TEMPLATES.values())
    
    if category:
        templates = [t for t in templates if t.category == category]
    
    if featured_only:
        templates = [t for t in templates if t.featured]
    
    return templates


def get_categories() -> List[AgentCategory]:
    """Get all available agent categories."""
    return list(AgentCategory)
