import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.openapi_parser import OpenAPIParser, get_spec_from_url
from app.core.tool_builder import OpenAPIToolBuilder
from app.adapters.adk import ADKAgentWrapper, ADKUnavailable
from app.adapters.callbacks import AgentCallbackHandler
from app.models.agent import AgentInfo
from app.utils.security import encrypt_api_key, decrypt_api_key
from app.database.models.agent import Agent, AgentStatus, Conversation, ToolExecution
from app.database.models.user import User


logger = logging.getLogger(__name__)


class AgentManager:
	def __init__(self):
		# Cache for active ADK agents (in-memory for performance)
		self._active_agents: Dict[str, Any] = {}
		self._callback_handlers: Dict[str, AgentCallbackHandler] = {}

	async def create_agent(self, config: Dict[str, Any], db: AsyncSession) -> str:
		"""Create a new agent and store it in the database."""
		
		# Fetch spec from URL if provided, otherwise use the provided spec
		if config.get('openapi_spec_url'):
			openapi_spec = await get_spec_from_url(config['openapi_spec_url'])
		else:
			openapi_spec = config['openapi_spec']
		
		# Parse OpenAPI spec
		parser = OpenAPIParser(openapi_spec)
		tool_builder = OpenAPIToolBuilder(openapi_spec, config['user_api_key'], config.get('api_base_url'))
		tools = tool_builder.build_all_tools()
		endpoints = parser.parse_endpoints()
		
		# Build instructions
		instructions = self._get_system_instructions()
		user_ctx = config.get('user_instructions')
		if user_ctx:
			instructions = f"{instructions}\n\nUser Context:\n{user_ctx}"
		
		# Encrypt API key
		encrypted_key = encrypt_api_key(config['user_api_key'])
		
		# Create database record
		agent = Agent(
			name=config['name'],
			status=AgentStatus.CREATING,
			user_instructions=user_ctx,
			system_instructions=instructions,
			openapi_spec=openapi_spec,
			api_base_url=parser.base_url or config.get('api_base_url', ''),
			encrypted_api_key=encrypted_key,
			auth_type=config.get('auth_type', 'bearer'),
			auth_header=config.get('auth_header', 'Authorization'),
			auth_prefix=config.get('auth_prefix'),
			tool_count=len(tools),
			available_tools=[{
				'name': ep.operation_id,
				'method': ep.method,
				'path': ep.path,
				'summary': ep.summary,
				'description': ep.description
			} for ep in endpoints],
			model_name=config.get('model_name', 'gemini-2.5-flash'),
			use_user_gemini_key='Y',  # Default to using user's key
			user_id=config['user_id']
		)
		
		db.add(agent)
		await db.commit()
		await db.refresh(agent)
		
		agent_id = str(agent.id)
		logger.info(f"Created agent {agent_id} with {len(tools)} tools")
		
		# Try to initialize ADK agent and update status
		try:
			# Use platform key for initialization since user doesn't have a Gemini key
			from app.core.config import settings
			platform_key = settings.ADK_API_KEY
			await self._initialize_adk_agent(agent, platform_key, db)
			agent.status = AgentStatus.ACTIVE
		except ADKUnavailable as e:
			logger.warning(f"ADK not available for agent {agent_id}: {e}")
			agent.status = AgentStatus.ERROR
		except Exception as e:
			logger.error(f"Failed to initialize ADK agent {agent_id}: {e}")
			agent.status = AgentStatus.ERROR
		
		await db.commit()
		return agent_id

	async def chat_with_agent(
		self, 
		agent_id: str, 
		message: str, 
		user_id: str, 
		conversation_id: Optional[str] = None,
		db: AsyncSession = None
	) -> Dict[str, Any]:
		"""Chat with an agent and store the conversation in the database."""
		
		# Get agent from database
		result = await db.execute(
			select(Agent).where(
				and_(Agent.id == agent_id, Agent.user_id == user_id)
			)
		)
		agent = result.scalar_one_or_none()
		
		if not agent:
			raise ValueError("Agent not found")
		
		if agent.status != AgentStatus.ACTIVE:
			raise ValueError(f"Agent is not active (status: {agent.status})")
		
		# Generate conversation ID if not provided
		if not conversation_id:
			conversation_id = f"conv_{agent_id}_{int(datetime.utcnow().timestamp())}"
		
		start_time = datetime.utcnow()
		
		# Get or create ADK agent
		adk_agent = await self._get_or_create_adk_agent(agent, db)
		logger.info(f"ADK agent for {agent_id}: {adk_agent is not None}")
		
		# Chat with agent
		try:
			if adk_agent and hasattr(adk_agent, 'chat'):
				# Real ADK agent
				logger.info(f"Using real ADK agent for {agent_id}")
				response = await adk_agent.chat(message)
				tool_names = []  # TODO: Extract from callback handler
			else:
				# Fallback mode
				logger.info(f"Using fallback mode for {agent_id} - ADK agent not available")
				response = f"I can help you with {agent.tool_count} API endpoints. What would you like me to do?"
				tool_names = []
		except Exception as e:
			logger.error(f"Chat error for agent {agent_id}: {e}")
			response = f"I encountered an error: {str(e)}"
			tool_names = []
		
		end_time = datetime.utcnow()
		execution_time = (end_time - start_time).total_seconds()
		
		# Store conversation in database
		conversation = Conversation(
			agent_id=agent.id,
			conversation_id=conversation_id,
			message=message,
			response=response,
			execution_time=str(execution_time)
		)
		
		db.add(conversation)
		
		# Update agent statistics
		agent.last_conversation_at = end_time
		agent.total_conversations += 1
		
		await db.commit()
		
		return {
			'conversation_id': conversation_id,
			'response': response,
			'tools_used': tool_names
		}

	async def list_agents(self, user_id: str, db: AsyncSession) -> List[AgentInfo]:
		"""List all agents for a user."""
		result = await db.execute(
			select(Agent).where(Agent.user_id == user_id).order_by(Agent.created_at.desc())
		)
		agents = result.scalars().all()
		
		agent_infos = []
		for agent in agents:
			# Get last conversation ID
			last_conv_result = await db.execute(
				select(Conversation.conversation_id)
				.where(Conversation.agent_id == agent.id)
				.order_by(Conversation.created_at.desc())
				.limit(1)
			)
			last_conversation = last_conv_result.scalar_one_or_none()
			
			agent_infos.append(AgentInfo(
				id=str(agent.id),
				name=agent.name,
				status=agent.status,
				created_at=agent.created_at.isoformat(),
				tool_count=agent.tool_count,
				api_base_url=agent.api_base_url or '',
				last_conversation=last_conversation
			))
		
		return agent_infos

	async def get_agent_info(self, agent_id: str, user_id: str, db: AsyncSession) -> Optional[AgentInfo]:
		"""Get agent information for a specific user."""
		result = await db.execute(
			select(Agent).where(
				and_(Agent.id == agent_id, Agent.user_id == user_id)
			)
		)
		agent = result.scalar_one_or_none()
		
		if not agent:
			return None
		
		# Get last conversation ID
		last_conv_result = await db.execute(
			select(Conversation.conversation_id)
			.where(Conversation.agent_id == agent.id)
			.order_by(Conversation.created_at.desc())
			.limit(1)
		)
		last_conversation = last_conv_result.scalar_one_or_none()
		
		return AgentInfo(
			id=str(agent.id),
			name=agent.name,
			status=agent.status,
			created_at=agent.created_at.isoformat(),
			tool_count=agent.tool_count,
			api_base_url=agent.api_base_url or '',
			last_conversation=last_conversation
		)

	async def delete_agent(self, agent_id: str, user_id: str, db: AsyncSession) -> bool:
		"""Delete an agent for a specific user."""
		result = await db.execute(
			select(Agent).where(
				and_(Agent.id == agent_id, Agent.user_id == user_id)
			)
		)
		agent = result.scalar_one_or_none()
		
		if not agent:
			return False
		
		# Remove from cache if exists
		if agent_id in self._active_agents:
			del self._active_agents[agent_id]
		if agent_id in self._callback_handlers:
			del self._callback_handlers[agent_id]
		
		# Delete from database (cascade will handle related records)
		await db.delete(agent)
		await db.commit()
		
		return True

	async def get_agent_tools(self, agent_id: str, user_id: str, db: AsyncSession):
		"""Get available tools for an agent."""
		result = await db.execute(
			select(Agent.available_tools).where(
				and_(Agent.id == agent_id, Agent.user_id == user_id)
			)
		)
		available_tools = result.scalar_one_or_none()
		
		if available_tools is None:
			return None
		
		return available_tools

	async def get_conversations(self, agent_id: str, user_id: str, db: AsyncSession):
		"""Get conversation history for an agent."""
		# Verify agent belongs to user
		agent_result = await db.execute(
			select(Agent.id).where(
				and_(Agent.id == agent_id, Agent.user_id == user_id)
			)
		)
		
		if not agent_result.scalar_one_or_none():
			return None
		
		# Get conversations
		result = await db.execute(
			select(Conversation)
			.where(Conversation.agent_id == agent_id)
			.order_by(Conversation.created_at.desc())
		)
		conversations = result.scalars().all()
		
		return [
			{
				'conversation_id': conv.conversation_id,
				'timestamp': conv.created_at.isoformat(),
				'message': conv.message,
				'response': conv.response,
				'execution_time': conv.execution_time,
				'tools_used': []  # TODO: Extract from tool executions
			}
			for conv in conversations
		]

	async def get_tool_execution_history(self, agent_id: str, user_id: str, db: AsyncSession):
		"""Get tool execution history for an agent."""
		# Verify agent belongs to user
		agent_result = await db.execute(
			select(Agent.id).where(
				and_(Agent.id == agent_id, Agent.user_id == user_id)
			)
		)
		
		if not agent_result.scalar_one_or_none():
			return None
		
		# Get tool executions
		result = await db.execute(
			select(ToolExecution)
			.where(ToolExecution.agent_id == agent_id)
			.order_by(ToolExecution.created_at.desc())
		)
		executions = result.scalars().all()
		
		return [
			{
				'id': str(execution.id),
				'tool_name': execution.tool_name,
				'operation_id': execution.operation_id,
				'method': execution.method,
				'endpoint_path': execution.endpoint_path,
				'request_args': execution.request_args,
				'response_data': execution.response_data,
				'status_code': execution.status_code,
				'error_message': execution.error_message,
				'execution_time_ms': execution.execution_time_ms,
				'conversation_id': execution.conversation_id,
				'created_at': execution.created_at.isoformat()
			}
			for execution in executions
		]

	async def _initialize_adk_agent(self, agent: Agent, user_api_key: str, db: AsyncSession):
		"""Initialize an ADK agent and store it in cache."""
		agent_id = str(agent.id)
		
		# Create callback handler
		callback_handler = AgentCallbackHandler(agent_id)
		self._callback_handlers[agent_id] = callback_handler
		
		# Decrypt API key if needed
		if agent.encrypted_api_key:
			api_key = decrypt_api_key(agent.encrypted_api_key)
		else:
			api_key = user_api_key
		
		# Create ADK agent
		adk_agent = ADKAgentWrapper(
			instructions=agent.system_instructions,
			openapi_spec=agent.openapi_spec,
			api_key=api_key,
			model_name=agent.model_name,
			callback_handler=callback_handler,
			auth_type=agent.auth_type,
			auth_header=agent.auth_header,
			auth_prefix=agent.auth_prefix
		)
		
		# Store in cache
		self._active_agents[agent_id] = adk_agent
		
		return adk_agent
	
	async def _get_or_create_adk_agent(self, agent: Agent, db: AsyncSession):
		"""Get ADK agent from cache or create new one."""
		agent_id = str(agent.id)
		
		# Check cache first
		if agent_id in self._active_agents:
			return self._active_agents[agent_id]
		
		# Create new ADK agent
		try:
			if agent.encrypted_api_key:
				api_key = decrypt_api_key(agent.encrypted_api_key)
			else:
				# Get user's Gemini API key or use platform key
				result = await db.execute(
					select(User.gemini_api_key_encrypted)
					.where(User.id == agent.user_id)
				)
				user_key_encrypted = result.scalar_one_or_none()
				
				if user_key_encrypted and agent.use_user_gemini_key == 'Y':
					api_key = decrypt_api_key(user_key_encrypted)
				else:
					# Use platform key as fallback
					from app.core.config import settings
					api_key = settings.ADK_API_KEY
					if not api_key:
						raise ValueError("No Gemini API key available")
			
			# Always use platform key for ADK initialization
			from app.core.config import settings
			platform_key = settings.ADK_API_KEY
			return await self._initialize_adk_agent(agent, platform_key, db)
			
		except Exception as e:
			logger.error(f"Failed to create ADK agent for {agent_id}: {e}")
			logger.error(f"Exception type: {type(e).__name__}")
			logger.error(f"Exception details: {str(e)}")
			import traceback
			logger.error(f"Traceback: {traceback.format_exc()}")
			return None
	
	def _get_system_instructions(self) -> str:
		return (
			"You are an API interaction assistant. Understand requests, map to API calls, "
			"execute with tools, present results clearly, handle errors, ask clarifying questions."
		)


