from typing import Dict, Any
import logging
import time
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)


class AgentCallbackHandler:
	"""Handles before/after tool execution callbacks for ADK agents"""
	
	def __init__(self, agent_id: str):
		self.agent_id = agent_id
		self.tool_executions = []
	
	def before_tool_execution(self, tool_name: str, args: Dict, tool_context: ToolContext) -> None:
		"""Called before each tool execution - updated to match ADK ToolContext"""
		execution_id = f"{self.agent_id}_{tool_name}_{int(time.time() * 1000)}"
		
		# Log tool execution start
		logger.info(f"Agent {self.agent_id} starting tool {tool_name} with args: {args}")
		
		# Store execution metadata 
		execution = {
			'id': execution_id,
			'agent_id': self.agent_id,
			'tool_name': tool_name,
			'args': args,
			'context_state': 'state_present' if hasattr(tool_context, 'state') else 'no_state',
			'start_time': time.time(),
			'status': 'started'
		}
		self.tool_executions.append(execution)
		
		# Following your working pattern: return None, don't modify context
		return None
	
	# Note: No after_tool_execution method - following your working pattern of only using before_tool_callback
	
	def get_tool_execution_history(self) -> list:
		"""Get history of tool executions for this agent"""
		return self.tool_executions.copy()
	
	def get_last_execution(self) -> Dict[str, Any] | None:
		"""Get the most recent tool execution"""
		return self.tool_executions[-1] if self.tool_executions else None

