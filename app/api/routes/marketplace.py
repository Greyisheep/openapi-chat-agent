"""Agent marketplace API routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user
from app.database.config import get_db
from app.database.models.user import User
from app.marketplace.templates import (
    AgentTemplate,
    AgentCategory,
    get_template,
    list_templates,
    get_categories,
)
from app.models.marketplace import (
    TemplateResponse,
    TemplateListResponse,
    CreateAgentFromTemplateRequest,
    CategoryResponse,
)


router = APIRouter()


@router.get("/templates", response_model=TemplateListResponse)
async def list_agent_templates(
    category: Optional[AgentCategory] = None,
    featured: bool = False,
    search: Optional[str] = None
) -> TemplateListResponse:
    """List available agent templates."""
    
    templates = list_templates(category=category, featured_only=featured)
    
    # Apply search filter if provided
    if search:
        search_lower = search.lower()
        templates = [
            t for t in templates
            if (search_lower in t.name.lower() or 
                search_lower in t.description.lower() or
                any(search_lower in tag.lower() for tag in t.tags))
        ]
    
    # Convert to response format
    template_responses = []
    for template in templates:
        template_responses.append(TemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            category=template.category,
            featured=template.featured,
            tags=template.tags,
            auth_type=template.auth_type,
            auth_header=template.auth_header,
            documentation_url=template.documentation_url,
            logo_url=template.logo_url
        ))
    
    return TemplateListResponse(
        templates=template_responses,
        total=len(template_responses),
        categories=get_categories()
    )


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_agent_template(template_id: str) -> TemplateResponse:
    """Get a specific agent template by ID."""
    
    template = get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found"
        )
    
    return TemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        category=template.category,
        featured=template.featured,
        tags=template.tags,
        auth_type=template.auth_type,
        auth_header=template.auth_header,
        documentation_url=template.documentation_url,
        logo_url=template.logo_url,
        openapi_spec=template.openapi_spec,
        default_instructions=template.default_instructions
    )


@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories() -> List[CategoryResponse]:
    """List all available agent categories."""
    
    categories = get_categories()
    
    # Count templates per category
    category_responses = []
    for category in categories:
        templates_in_category = list_templates(category=category)
        category_responses.append(CategoryResponse(
            id=category.value,
            name=category.value.replace('_', ' ').title(),
            description=_get_category_description(category),
            template_count=len(templates_in_category)
        ))
    
    return category_responses


@router.post("/templates/{template_id}/create-agent")
async def create_agent_from_template(
    template_id: str,
    request: CreateAgentFromTemplateRequest,
    http_request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Create a new agent from a marketplace template."""
    
    # Get the template
    template = get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found"
        )
    
    # Validate required fields based on auth type
    if template.auth_type != "none" and not request.api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"API key is required for {template.name} (auth type: {template.auth_type})"
        )
    
    # Build agent configuration
    agent_config = {
        "name": request.agent_name or f"{template.name} Agent",
        "openapi_spec": template.openapi_spec,
        "user_api_key": request.api_key or "",
        "user_instructions": request.custom_instructions or template.default_instructions,
        "api_base_url": template.openapi_spec.get("servers", [{}])[0].get("url", ""),
        "user_id": str(current_user.id),
        "auth_type": template.auth_type,
        "auth_header": template.auth_header,
        "auth_prefix": template.auth_prefix
    }
    
    # Create the agent using the agent manager
    agent_manager = http_request.state.agent_manager
    try:
        agent_id = await agent_manager.create_agent(agent_config, db)
        return {
            "agent_id": agent_id,
            "status": "created",
            "template_id": template_id,
            "message": f"Agent created successfully from {template.name} template"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create agent from template: {str(e)}"
        )


def _get_category_description(category: AgentCategory) -> str:
    """Get a human-readable description for an agent category."""
    descriptions = {
        AgentCategory.DEVELOPMENT: "Tools for software development, version control, and DevOps",
        AgentCategory.PRODUCTIVITY: "Agents to boost productivity and workflow automation",
        AgentCategory.COMMUNICATION: "Messaging, email, and team collaboration tools",
        AgentCategory.ECOMMERCE: "E-commerce platforms, payment processing, and online stores",
        AgentCategory.SOCIAL_MEDIA: "Social media platforms and content management",
        AgentCategory.FINANCE: "Financial services, banking, and payment APIs",
        AgentCategory.UTILITY: "General purpose tools and testing utilities"
    }
    return descriptions.get(category, f"Agents in the {category.value} category")
