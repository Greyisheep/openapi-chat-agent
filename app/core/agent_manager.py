import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from app.core.openapi_parser import OpenAPIParser, get_spec_from_url
from app.core.tool_builder import OpenAPIToolBuilder
from app.adapters.adk import ADKAgentWrapper, ADKUnavailable
from app.adapters.callbacks import AgentCallbackHandler
from app.models.agent import AgentStatus, AgentInfo
from app.utils.security import encrypt_api_key


logger = logging.getLogger(__name__)


class AgentManager:
	def __init__(self):
		self.agents: Dict[str, Dict[str, Any]] = {}
		self.conversations: Dict[str, List[Dict[str, Any]]] = {}

	async def create_agent(self, config: Dict[str, Any]) -> str:
		agent_id = str(uuid.uuid4())
		encrypted_key = encrypt_api_key(config['user_api_key'])
		
		# Fetch spec from URL if provided, otherwise use the provided spec
		if config.get('openapi_spec_url'):
			openapi_spec = await get_spec_from_url(config['openapi_spec_url'])
		else:
			openapi_spec = config['openapi_spec']
		
		parser = OpenAPIParser(openapi_spec)
		tool_builder = OpenAPIToolBuilder(openapi_spec, config['user_api_key'], config.get('api_base_url'))
		tools = tool_builder.build_all_tools()
		endpoints = parser.parse_endpoints()
		instructions = self._get_system_instructions()
		user_ctx = config.get('user_instructions')
		if user_ctx:
			instructions = f"{instructions}\n\nUser Context:\n{user_ctx}"

		# Create callback handler for this agent
		callback_handler = AgentCallbackHandler(agent_id)

		# Try to create a real ADK agent, fall back to mock metadata
		try:
			adk_agent = ADKAgentWrapper(
				instructions=instructions,
				openapi_spec=openapi_spec,
				api_key=config['user_api_key'],
				model_name=None,
				callback_handler=callback_handler
			)
			agent_obj = adk_agent
		except ADKUnavailable as e:
			logger.warning(f"ADK not available, using fallback: {e}")
			agent_obj = {'instructions': instructions, 'tools': tools}

		self.agents[agent_id] = {
			'id': agent_id,
			'name': config['name'],
			'status': AgentStatus.ACTIVE,
			'created_at': datetime.utcnow().isoformat(),
			'agent': agent_obj,
			'callback_handler': callback_handler,
			'config': config,
			'encrypted_api_key': encrypted_key,
			'tool_builder': tool_builder,
			'endpoints': endpoints,
			'tool_count': len(tools),
			'api_base_url': parser.base_url or config.get('api_base_url', '')
		}
		self.conversations[agent_id] = []
		logger.info(f"Created agent {agent_id} with {len(tools)} tools")
		return agent_id

	async def chat_with_agent(self, agent_id: str, message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
		if agent_id not in self.agents:
			raise ValueError("Agent not found")
		agent = self.agents[agent_id]['agent']
		callback_handler = self.agents[agent_id]['callback_handler']
		
		if not conversation_id:
			conversation_id = f"conv_{agent_id}_{len(self.conversations[agent_id]) + 1}"
		
		# Use ADK agent if available, otherwise fallback
		if hasattr(agent, 'chat'):
			# Real ADK agent
			response = await agent.chat(message)
			# Get tool usage from callback handler
			last_execution = callback_handler.get_last_execution()
			tool_names = [last_execution['tool_name']] if last_execution else []
		else:
			# Fallback mode
			tools = agent['tools']
			tool_names = [t.__name__ for t in tools]
			response = f"I can call {len(tool_names)} endpoints. First few: {', '.join(tool_names[:3])}. What would you like me to do?"
		entry = {
			'conversation_id': conversation_id,
			'timestamp': datetime.utcnow().isoformat(),
			'message': message,
			'response': response,
			'tools_used': []
		}
		self.conversations[agent_id].append(entry)
		self.agents[agent_id]['last_conversation'] = conversation_id
		return {'conversation_id': conversation_id, 'response': response, 'tools_used': []}

	async def list_agents(self) -> List[AgentInfo]:
		return [AgentInfo(
			id=a['id'], name=a['name'], status=a['status'], created_at=a['created_at'],
			tool_count=a['tool_count'], api_base_url=a['api_base_url'], last_conversation=a.get('last_conversation')
		) for a in self.agents.values()]

	async def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
		a = self.agents.get(agent_id)
		if not a:
			return None
		return AgentInfo(
			id=a['id'], name=a['name'], status=a['status'], created_at=a['created_at'],
			tool_count=a['tool_count'], api_base_url=a['api_base_url'], last_conversation=a.get('last_conversation')
		)

	async def delete_agent(self, agent_id: str) -> bool:
		if agent_id not in self.agents:
			return False
		del self.agents[agent_id]
		self.conversations.pop(agent_id, None)
		return True

	async def get_agent_tools(self, agent_id: str):
		a = self.agents.get(agent_id)
		if not a:
			return None
		tools = []
		for ep in a['endpoints']:
			tools.append({'name': ep.operation_id, 'method': ep.method, 'path': ep.path, 'summary': ep.summary, 'description': ep.description})
		return tools

	async def get_conversations(self, agent_id: str):
		return self.conversations.get(agent_id)

	async def get_tool_execution_history(self, agent_id: str):
		"""Get tool execution history for an agent"""
		if agent_id not in self.agents:
			return None
		callback_handler = self.agents[agent_id]['callback_handler']
		return callback_handler.get_tool_execution_history()

	def _get_system_instructions(self) -> str:
		return (
			"You are an API interaction assistant. Understand requests, map to API calls, "
			"execute with tools, present results clearly, handle errors, ask clarifying questions."
		)


