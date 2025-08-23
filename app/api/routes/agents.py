from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict
import time
from datetime import datetime

from app.models.agent import CreateAgentRequest, AgentInfo, ChatRequest, ChatResponse


router = APIRouter()


@router.post("/", response_model=Dict[str, str])
async def create_agent(request: CreateAgentRequest, http_request: Request):
	agent_manager = http_request.state.agent_manager
	try:
		agent_id = await agent_manager.create_agent(request.dict())
		return {"agent_id": agent_id, "status": "created"}
	except Exception as e:
		raise HTTPException(status_code=400, detail=f"Failed to create agent: {str(e)}")


@router.get("/", response_model=List[AgentInfo])
async def list_agents(request: Request):
	return await request.state.agent_manager.list_agents()


@router.get("/{agent_id}", response_model=AgentInfo)
async def get_agent(agent_id: str, request: Request):
	info = await request.state.agent_manager.get_agent_info(agent_id)
	if not info:
		raise HTTPException(status_code=404, detail="Agent not found")
	return info


@router.post("/{agent_id}/chat", response_model=ChatResponse)
async def chat_with_agent(agent_id: str, chat_request: ChatRequest, request: Request):
	start = time.time()
	try:
		result = await request.state.agent_manager.chat_with_agent(agent_id, chat_request.message, chat_request.conversation_id)
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
async def delete_agent(agent_id: str, request: Request):
	ok = await request.state.agent_manager.delete_agent(agent_id)
	if not ok:
		raise HTTPException(status_code=404, detail="Agent not found")
	return {"message": "Agent deleted successfully"}


@router.get("/{agent_id}/tools")
async def get_agent_tools(agent_id: str, request: Request):
	tools = await request.state.agent_manager.get_agent_tools(agent_id)
	if tools is None:
		raise HTTPException(status_code=404, detail="Agent not found")
	return {"agent_id": agent_id, "tools": tools}


@router.get("/{agent_id}/conversations")
async def get_conversations(agent_id: str, request: Request):
	convs = await request.state.agent_manager.get_conversations(agent_id)
	if convs is None:
		raise HTTPException(status_code=404, detail="Agent not found")
	return {"agent_id": agent_id, "conversations": convs}


@router.get("/{agent_id}/tool-executions")
async def get_tool_executions(agent_id: str, request: Request):
	"""Get tool execution history for an agent"""
	agent_manager = request.state.agent_manager
	executions = await agent_manager.get_tool_execution_history(agent_id)
	if executions is None:
		raise HTTPException(status_code=404, detail="Agent not found")
	return {"agent_id": agent_id, "tool_executions": executions}


