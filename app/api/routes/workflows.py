"""API routes for workflow orchestration."""

from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List, Dict, Optional
import time
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import WorkflowRequest, WorkflowResponse, WorkflowStep
from pydantic import BaseModel
from app.core.auth import get_current_active_user
from app.database.config import get_db
from app.database.models.user import User
from app.core.workflow_manager import WorkflowManager

router = APIRouter()


@router.post("/execute", response_model=WorkflowResponse)
async def execute_workflow(
    workflow_request: WorkflowRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute a multi-agent workflow."""
    
    agent_manager = request.state.agent_manager
    workflow_manager = WorkflowManager(agent_manager)
    
    try:
        result = await workflow_manager.execute_workflow(
            workflow_request, str(current_user.id), db
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.get("/history")
async def get_workflow_history(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50
):
    """Get workflow execution history for the current user."""
    
    agent_manager = request.state.agent_manager
    workflow_manager = WorkflowManager(agent_manager)
    
    try:
        history = await workflow_manager.get_workflow_history(
            str(current_user.id), db, limit
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow history: {str(e)}")


@router.get("/details/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow_details(
    workflow_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific workflow execution."""
    
    agent_manager = request.state.agent_manager
    workflow_manager = WorkflowManager(agent_manager)
    
    try:
        result = await workflow_manager.get_workflow_details(
            workflow_id, str(current_user.id), db
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow details: {str(e)}")


class SimpleChainRequest(BaseModel):
    """Request for simple agent chaining."""
    agent_ids: List[str]
    message: str
    workflow_name: Optional[str] = None
    parallel_execution: bool = False

    class Config:
        schema_extra = {
            "example": {
                "agent_ids": ["github-agent-id", "slack-agent-id"],
                "message": "Get my repositories and send a summary to Slack",
                "workflow_name": "GitHub to Slack Integration",
                "parallel_execution": False
            }
        }


class MultiStepWorkflowRequest(BaseModel):
    """Request for multi-step workflow with custom messages per step."""
    steps: List[Dict]
    workflow_name: Optional[str] = None
    parallel_execution: bool = False
    
    class Config:
        schema_extra = {
            "example": {
                "steps": [
                    {
                        "agent_id": "github-agent-id",
                        "message": "List my top 5 most recent repositories",
                        "step_name": "get_repos"
                    },
                    {
                        "agent_id": "slack-agent-id", 
                        "message": "Send repository information to #dev-team channel",
                        "step_name": "notify_team",
                        "depends_on": ["get_repos"]
                    }
                ],
                "workflow_name": "Repository Review Workflow",
                "parallel_execution": False
            }
        }


class WorkflowTemplateRequest(BaseModel):
    """Request for predefined workflow templates."""
    template_name: str
    template_params: Dict
    workflow_name: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "template_name": "github_to_slack",
                "template_params": {
                    "github_agent_id": "your-github-agent-id",
                    "slack_agent_id": "your-slack-agent-id",
                    "repository_filter": "recent"
                },
                "workflow_name": "Daily Repo Summary"
            }
        }


@router.post("/simple-chain", response_model=WorkflowResponse)
async def simple_agent_chain(
    chain_request: SimpleChainRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Simple endpoint to chain multiple agents with the same message."""
    
    if not chain_request.agent_ids or not chain_request.message:
        raise HTTPException(
            status_code=400, 
            detail="agent_ids and message are required"
        )
    
    # Create workflow steps from agent IDs
    steps = []
    for i, agent_id in enumerate(chain_request.agent_ids):
        step_name = f"step_{i + 1}"
        depends_on = [f"step_{j + 1}" for j in range(i)] if i > 0 and not chain_request.parallel_execution else []
        
        steps.append(WorkflowStep(
            agent_id=agent_id,
            message=chain_request.message,
            step_name=step_name,
            depends_on=depends_on
        ))
    
    workflow_request = WorkflowRequest(
        workflow_name=chain_request.workflow_name or f"Simple Chain - {len(chain_request.agent_ids)} agents",
        steps=steps,
        parallel_execution=chain_request.parallel_execution
    )
    
    agent_manager = request.state.agent_manager
    workflow_manager = WorkflowManager(agent_manager)
    
    try:
        result = await workflow_manager.execute_workflow(
            workflow_request, str(current_user.id), db
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simple chain execution failed: {str(e)}")


@router.post("/multi-step", response_model=WorkflowResponse)
async def multi_step_workflow(
    workflow_request: MultiStepWorkflowRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute a multi-step workflow with custom messages per step."""
    
    if not workflow_request.steps:
        raise HTTPException(
            status_code=400, 
            detail="At least one workflow step is required"
        )
    
    # Convert steps to WorkflowStep objects
    workflow_steps = []
    for i, step_data in enumerate(workflow_request.steps):
        if "agent_id" not in step_data or "message" not in step_data:
            raise HTTPException(
                status_code=400,
                detail=f"Step {i+1} must have 'agent_id' and 'message' fields"
            )
        
        step = WorkflowStep(
            agent_id=step_data["agent_id"],
            message=step_data["message"],
            step_name=step_data.get("step_name", f"step_{i + 1}"),
            depends_on=step_data.get("depends_on", [])
        )
        workflow_steps.append(step)
    
    workflow_req = WorkflowRequest(
        workflow_name=workflow_request.workflow_name or "Multi-Step Workflow",
        steps=workflow_steps,
        parallel_execution=workflow_request.parallel_execution
    )
    
    agent_manager = request.state.agent_manager
    workflow_manager = WorkflowManager(agent_manager)
    
    try:
        result = await workflow_manager.execute_workflow(
            workflow_req, str(current_user.id), db
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-step workflow execution failed: {str(e)}")


@router.get("/templates/list")
async def list_workflow_templates():
    """List all available workflow templates."""
    
    templates = {
        "github_to_slack": {
            "name": "GitHub to Slack Integration",
            "description": "Get GitHub repositories and send summary to Slack",
            "required_params": ["github_agent_id", "slack_agent_id"],
            "example_usage": {
                "template_name": "github_to_slack",
                "template_params": {
                    "github_agent_id": "your-github-agent-id",
                    "slack_agent_id": "your-slack-agent-id"
                }
            }
        },
        "code_review_workflow": {
            "name": "Code Review Workflow", 
            "description": "Get latest commits and create review summary",
            "required_params": ["github_agent_id", "slack_agent_id"],
            "example_usage": {
                "template_name": "code_review_workflow",
                "template_params": {
                    "github_agent_id": "your-github-agent-id",
                    "slack_agent_id": "your-slack-agent-id"
                }
            }
        }
    }
    
    return {
        "templates": templates,
        "usage_instructions": "Use POST /api/v1/workflows/templates/{template_name} to execute a template"
    }


@router.post("/templates/{template_name}", response_model=WorkflowResponse)
async def execute_workflow_template(
    template_name: str,
    template_request: WorkflowTemplateRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute a predefined workflow template."""
    
    # Define workflow templates
    templates = {
        "github_to_slack": {
            "name": "GitHub to Slack Integration",
            "description": "Get GitHub repositories and send summary to Slack",
            "required_params": ["github_agent_id", "slack_agent_id"],
            "steps": [
                {
                    "agent_key": "github_agent_id",
                    "message": "Get my GitHub repositories with names and descriptions",
                    "step_name": "fetch_repos"
                },
                {
                    "agent_key": "slack_agent_id",
                    "message": "Send the repository information to Slack",
                    "step_name": "send_to_slack",
                    "depends_on": ["fetch_repos"]
                }
            ]
        },
        "code_review_workflow": {
            "name": "Code Review Workflow",
            "description": "Get latest commits and create review summary",
            "required_params": ["github_agent_id", "slack_agent_id"],
            "steps": [
                {
                    "agent_key": "github_agent_id",
                    "message": "Get recent commits and pull requests",
                    "step_name": "get_commits"
                },
                {
                    "agent_key": "slack_agent_id",
                    "message": "Send code review summary to development team",
                    "step_name": "notify_reviewers",
                    "depends_on": ["get_commits"]
                }
            ]
        }
    }
    
    if template_name not in templates:
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_name}' not found. Available templates: {list(templates.keys())}"
        )
    
    template = templates[template_name]
    params = template_request.template_params
    
    # Validate required parameters
    missing_params = [p for p in template["required_params"] if p not in params]
    if missing_params:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required parameters: {missing_params}"
        )
    
    # Build workflow steps from template
    workflow_steps = []
    for step_template in template["steps"]:
        agent_id = params[step_template["agent_key"]]
        
        step = WorkflowStep(
            agent_id=agent_id,
            message=step_template["message"],
            step_name=step_template["step_name"],
            depends_on=step_template.get("depends_on", [])
        )
        workflow_steps.append(step)
    
    workflow_req = WorkflowRequest(
        workflow_name=template_request.workflow_name or template["name"],
        description=template["description"],
        steps=workflow_steps,
        parallel_execution=False  # Templates are sequential by default
    )
    
    agent_manager = request.state.agent_manager
    workflow_manager = WorkflowManager(agent_manager)
    
    try:
        result = await workflow_manager.execute_workflow(
            workflow_req, str(current_user.id), db
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template workflow execution failed: {str(e)}")


@router.get("/status/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the current status of a workflow execution."""
    
    agent_manager = request.state.agent_manager
    workflow_manager = WorkflowManager(agent_manager)
    
    try:
        result = await workflow_manager.get_workflow_details(
            workflow_id, str(current_user.id), db
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "workflow_id": workflow_id,
            "status": result.status,
            "total_execution_time": result.total_execution_time,
            "step_count": len(result.steps),
            "completed_steps": len([s for s in result.steps if s.status == "success"]),
            "failed_steps": len([s for s in result.steps if s.status == "error"]),
            "timestamp": result.timestamp
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")
