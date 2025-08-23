from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List, Dict
import time
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import CreateAgentRequest, AgentInfo, ChatRequest, ChatResponse
from app.core.auth import get_current_active_user
from app.database.config import get_db
from app.database.models.user import User


router = APIRouter()


@router.post("/", response_model=Dict[str, str])
async def create_agent(
	request: CreateAgentRequest,
	http_request: Request,
	current_user: User = Depends(get_current_active_user),
	db: AsyncSession = Depends(get_db)
):
	agent_manager = http_request.state.agent_manager
	try:
		# Add user context to the request
		request_data = request.dict()
		request_data['user_id'] = str(current_user.id)
		agent_id = await agent_manager.create_agent(request_data, db)
		return {"agent_id": agent_id, "status": "created"}
	except Exception as e:
		raise HTTPException(status_code=400, detail=f"Failed to create agent: {str(e)}")


@router.get("/", response_model=List[AgentInfo])
async def list_agents(
	request: Request,
	current_user: User = Depends(get_current_active_user),
	db: AsyncSession = Depends(get_db)
):
	return await request.state.agent_manager.list_agents(current_user.id, db)


@router.get("/{agent_id}", response_model=AgentInfo)
async def get_agent(
	agent_id: str,
	request: Request,
	current_user: User = Depends(get_current_active_user),
	db: AsyncSession = Depends(get_db)
):
	info = await request.state.agent_manager.get_agent_info(agent_id, current_user.id, db)
	if not info:
		raise HTTPException(status_code=404, detail="Agent not found")
	return info


@router.post("/{agent_id}/chat", response_model=ChatResponse)
async def chat_with_agent(
	agent_id: str,
	chat_request: ChatRequest,
	request: Request,
	current_user: User = Depends(get_current_active_user),
	db: AsyncSession = Depends(get_db)
):
	start = time.time()
	try:
		result = await request.state.agent_manager.chat_with_agent(
			agent_id, chat_request.message, current_user.id, chat_request.conversation_id, db
		)
		return ChatResponse(
			agent_id=agent_id,
			conversation_id=result['conversation_id'],
			message=chat_request.message,
			response=result['response'],
			tools_used=result.get('tools_used', []),
			execution_time=time.time() - start,
			timestamp=datetime.utcnow().isoformat()
		)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.delete("/{agent_id}")
async def delete_agent(
	agent_id: str,
	request: Request,
	current_user: User = Depends(get_current_active_user),
	db: AsyncSession = Depends(get_db)
):
	ok = await request.state.agent_manager.delete_agent(agent_id, current_user.id, db)
	if not ok:
		raise HTTPException(status_code=404, detail="Agent not found")
	return {"message": "Agent deleted successfully"}


@router.get("/{agent_id}/tools")
async def get_agent_tools(
	agent_id: str,
	request: Request,
	current_user: User = Depends(get_current_active_user),
	db: AsyncSession = Depends(get_db)
):
	tools = await request.state.agent_manager.get_agent_tools(agent_id, current_user.id, db)
	if tools is None:
		raise HTTPException(status_code=404, detail="Agent not found")
	return {"agent_id": agent_id, "tools": tools}


@router.get("/{agent_id}/conversations")
async def get_conversations(
	agent_id: str,
	request: Request,
	current_user: User = Depends(get_current_active_user),
	db: AsyncSession = Depends(get_db)
):
	convs = await request.state.agent_manager.get_conversations(agent_id, current_user.id, db)
	if convs is None:
		raise HTTPException(status_code=404, detail="Agent not found")
	return {"agent_id": agent_id, "conversations": convs}


@router.get("/{agent_id}/tool-executions")
async def get_tool_executions(
	agent_id: str,
	request: Request,
	current_user: User = Depends(get_current_active_user),
	db: AsyncSession = Depends(get_db)
):
	"""Get tool execution history for an agent"""
	agent_manager = request.state.agent_manager
	executions = await agent_manager.get_tool_execution_history(agent_id, current_user.id, db)
	if executions is None:
		raise HTTPException(status_code=404, detail="Agent not found")
	return {"agent_id": agent_id, "tool_executions": executions}


