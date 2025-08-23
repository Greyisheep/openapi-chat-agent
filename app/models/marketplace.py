"""Pydantic models for the agent marketplace."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from app.marketplace.templates import AgentCategory


class TemplateResponse(BaseModel):
    """Agent template information for API responses."""
    
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    category: AgentCategory = Field(..., description="Template category")
    featured: bool = Field(..., description="Whether template is featured")
    tags: List[str] = Field(..., description="Template tags")
    auth_type: str = Field(..., description="Authentication type required")
    auth_header: str = Field(..., description="Authentication header name")
    documentation_url: Optional[str] = Field(None, description="API documentation URL")
    logo_url: Optional[str] = Field(None, description="Template logo URL")
    
    # Full template details (included when requesting specific template)
    openapi_spec: Optional[Dict[str, Any]] = Field(None, description="OpenAPI specification")
    default_instructions: Optional[str] = Field(None, description="Default agent instructions")
    
    class Config:
        use_enum_values = True


class TemplateListResponse(BaseModel):
    """Response for listing agent templates."""
    
    templates: List[TemplateResponse] = Field(..., description="List of templates")
    total: int = Field(..., description="Total number of templates")
    categories: List[AgentCategory] = Field(..., description="Available categories")
    
    class Config:
        use_enum_values = True


class CategoryResponse(BaseModel):
    """Agent category information."""
    
    id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Category display name")
    description: str = Field(..., description="Category description")
    template_count: int = Field(..., description="Number of templates in category")


class CreateAgentFromTemplateRequest(BaseModel):
    """Request to create an agent from a marketplace template."""
    
    agent_name: Optional[str] = Field(None, description="Custom name for the agent")
    api_key: Optional[str] = Field(None, description="API key for the target service")
    custom_instructions: Optional[str] = Field(None, description="Custom instructions (overrides template defaults)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "My GitHub Assistant",
                "api_key": "ghp_xxxxxxxxxxxxxxxxxxxx",
                "custom_instructions": "Focus on helping with open source projects and code reviews."
            }
        }
