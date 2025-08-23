from typing import Any, Dict, List, Optional
import asyncio
import logging
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)


class ADKUnavailable(Exception):
	pass


def _import_adk():
	try:
		# Based on ADK docs: google-adk package with specific imports
		from google.adk.agents import LlmAgent  # type: ignore
		from google.adk.models import Gemini  # type: ignore 
		from google.adk.tools.openapi_tool import OpenAPIToolset  # type: ignore
		return {
			'LlmAgent': LlmAgent,
			'GeminiModel': Gemini, 
			'OpenAPIToolset': OpenAPIToolset
		}
	except ImportError as exc:
		raise ADKUnavailable(f"ADK not available: {exc}")


class ADKAgentWrapper:
	def __init__(
		self, 
		instructions: str, 
		openapi_spec: Dict[str, Any],
		api_key: str,
		model_name: Optional[str] = None,
		callback_handler: Optional[Any] = None,
		auth_type: str = "bearer",
		auth_header: str = "Authorization", 
		auth_prefix: Optional[str] = None
	):
		adk_components = _import_adk()
		
		self._instructions = instructions
		self._openapi_spec = openapi_spec
		self._api_key = api_key
		self._model_name = model_name or "gemini-2.5-flash"
		self._auth_type = auth_type
		self._auth_header = auth_header
		self._auth_prefix = auth_prefix
		
		# Create ADK model - we need to set the Google API key as an environment variable
		import os
		# The API key should be set via environment variable GOOGLE_API_KEY
		if not os.environ.get('GOOGLE_API_KEY'):
			raise ValueError("GOOGLE_API_KEY environment variable is required")
		
		self._model = adk_components['GeminiModel'](
			model=self._model_name
		)
		
		# Create OpenAPI toolset from user's spec
		if api_key and api_key.strip() and self._auth_type != "none":
			# Only set up authentication if API key is provided and auth type is not none
			from google.adk.tools.openapi_tool.auth import auth_helpers
			
			# Build the authentication value based on the auth configuration
			if self._auth_type == "token":
				# GitHub style: Authorization: token <token>
				auth_value = f"token {api_key}"
				auth_scheme, auth_credential = auth_helpers.token_to_scheme_credential(
					"apikey", "header", self._auth_header, auth_value
				)
			elif self._auth_type == "bearer":
				# Standard Bearer: Authorization: Bearer <token>
				auth_value = f"Bearer {api_key}"
				auth_scheme, auth_credential = auth_helpers.token_to_scheme_credential(
					"bearer", "header", self._auth_header, auth_value
				)
			elif self._auth_type == "api_key":
				# API Key style: X-API-Key: <token>
				auth_scheme, auth_credential = auth_helpers.token_to_scheme_credential(
					"apikey", "header", self._auth_header, api_key
				)
			elif self._auth_type == "custom" and self._auth_prefix:
				# Custom prefix: <header>: <prefix> <token>
				auth_value = f"{self._auth_prefix} {api_key}"
				auth_scheme, auth_credential = auth_helpers.token_to_scheme_credential(
					"apikey", "header", self._auth_header, auth_value
				)
			else:
				# Fallback to bearer if no specific type matches
				auth_value = f"Bearer {api_key}"
				auth_scheme, auth_credential = auth_helpers.token_to_scheme_credential(
					"bearer", "header", self._auth_header, auth_value
				)
			
			self._openapi_toolset = adk_components['OpenAPIToolset'](
				spec_dict=openapi_spec,
				auth_scheme=auth_scheme,
				auth_credential=auth_credential
			)
		else:
			# No authentication needed
			self._openapi_toolset = adk_components['OpenAPIToolset'](
				spec_dict=openapi_spec
			)
		
		# Create LLM agent with tools and callbacks (matching your working pattern)
		self._agent = adk_components['LlmAgent'](
			name="openapi_agent",
			model=self._model,
			instruction=instructions,
			tools=[self._openapi_toolset],
			before_tool_callback=self._before_tool_callback if callback_handler else None
			# Note: No after_tool_callback - following your working pattern
		)
		
		self._callback_handler = callback_handler

	async def chat(self, message: str) -> str:
		"""Send message to ADK agent and get response"""
		try:
			# Import the Runner and types from Google ADK (following your working pattern)
			from google.adk.runners import Runner
			from google.genai import types
			from google.adk.sessions import InMemorySessionService
			
			# Create an in-memory session service (simpler than DatabaseSessionService for our use case)
			session_service = InMemorySessionService()
			
			# Create a session first (following your pattern)
			session = await session_service.create_session(app_name="openapi_app", user_id="anonymous")
			logger.info(f"Created session {session.id} for user anonymous")
			
			runner = Runner(app_name="openapi_app", agent=self._agent, session_service=session_service)
			
			# Create content with user role as required by ADK
			content = types.Content(role="user", parts=[types.Part(text=message)])
			
			# Collect events from the runner
			invocation_events = []
			
			# Use the same pattern as your working code
			async for evt in runner.run_async(
				user_id="anonymous",
				session_id=session.id,  # Use the created session ID
				new_message=content
			):
				invocation_events.append(evt)
				logger.debug(f"Agent event received: type={type(evt).__name__}")
			
			# Extract text using the same helper function pattern from your code
			def _extract_text_from_event(evt) -> str | None:
				"""Safely extract the first *text* part from an ADK event."""
				content = getattr(evt, "content", None)
				if content is None:
					return None

				parts = getattr(content, "parts", None)
				if not parts:
					return None

				first_part = parts[0]

				# Skip function calls – they are handled internally by the runner.
				if getattr(first_part, "function_call", None) is not None:
					return None

				return getattr(first_part, "text", None) or None
			
			# Extract the final response
			final_response = None
			response_parts = []
			
			for i, evt in enumerate(invocation_events):
				maybe_text = _extract_text_from_event(evt)
				if maybe_text:
					response_parts.append(maybe_text)
					final_response = maybe_text  # Keep the last non-empty response
					logger.debug(f"Extracted text from event {i}: {maybe_text[:100]}...")
			
			logger.info(f"Response extraction completed: {len(response_parts)} text parts found")
			
			if final_response is None:
				logger.error("No response generated by agent")
				return "I'm here to help you with the pet store API!"
			
			return final_response
			
		except Exception as e:
			import traceback
			logger.error(f"ADK chat error: {e}")
			logger.error(f"Traceback: {traceback.format_exc()}")
			return f"Error processing request: {str(e)}"

	def _before_tool_callback(self, tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext):
		"""Called before each tool execution - matches your working pattern exactly"""
		if self._callback_handler:
			# Adapt to our callback handler interface
			tool_name = getattr(tool, 'name', str(tool))
			return self._callback_handler.before_tool_execution(tool_name, args, tool_context)
		
		logger.info(f"Executing tool: {getattr(tool, 'name', str(tool))} with args: {args}")
		
		# Following your pattern: return None, not modified args
		return None

	def get_available_tools(self) -> List[str]:
		"""Get list of available OpenAPI operations"""
		try:
			return self._openapi_toolset.get_tool_names() if hasattr(self._openapi_toolset, 'get_tool_names') else []
		except:
			return []


