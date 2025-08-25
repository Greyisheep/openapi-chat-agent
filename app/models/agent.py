from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional, List
from enum import Enum


class AgentStatus(str, Enum):
	CREATING = "creating"
	ACTIVE = "active"
	ERROR = "error"
	DELETED = "deleted"


class CreateAgentRequest(BaseModel):
	name: str = Field(...)
	openapi_spec: Optional[Dict[str, Any]] = Field(None)
	openapi_spec_url: Optional[str] = Field(None)
	user_api_key: str = Field(...)
	api_base_url: Optional[str] = Field(None)
	user_instructions: Optional[str] = Field(None)

	@field_validator('openapi_spec_url')
	def validate_spec_source(cls, v, values):
		if not v and not values.data.get('openapi_spec'):
			raise ValueError("Either 'openapi_spec' or 'openapi_spec_url' must be provided.")
		if v and values.data.get('openapi_spec'):
			raise ValueError("Provide either 'openapi_spec' or 'openapi_spec_url', not both.")
		return v


class AgentInfo(BaseModel):
	id: str
	name: str
	status: AgentStatus
	created_at: str
	tool_count: int
	api_base_url: str
	last_conversation: Optional[str] = None


class ChatRequest(BaseModel):
	message: str
	conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
	agent_id: str
	conversation_id: str
	message: str
	response: str
	tools_used: List[str] = Field(default_factory=list)
	execution_time: float
	timestamp: str


class AgentError(BaseModel):
	error: str
	details: Optional[str] = None
	error_code: Optional[str] = None


# Workflow Models
class WorkflowStep(BaseModel):
	agent_id: str
	message: str
	step_name: Optional[str] = None
	depends_on: Optional[List[str]] = Field(default_factory=list)


class WorkflowRequest(BaseModel):
	workflow_name: str
	steps: List[WorkflowStep]
	parallel_execution: bool = False


class WorkflowStepResult(BaseModel):
	step_name: str
	agent_id: str
	message: str
	response: str
	tools_used: List[str] = Field(default_factory=list)
	execution_time: float
	status: str
	error: Optional[str] = None
	timestamp: str


class WorkflowResponse(BaseModel):
	workflow_id: str
	workflow_name: str
	conversation_id: str
	steps: List[WorkflowStepResult]
	total_execution_time: float
	status: str
	timestamp: str



