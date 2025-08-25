"""Agent models for managing conversational agents and their data."""

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, JSON, Enum, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.database.config import Base


class AgentStatus(str, enum.Enum):
    """Agent status enumeration."""
    CREATING = "creating"
    ACTIVE = "active" 
    ERROR = "error"
    PAUSED = "paused"
    DELETED = "deleted"


class Agent(Base):
    """Agent model for storing conversational agents."""
    
    __tablename__ = "agents"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Agent configuration
    name = Column(String(255), nullable=False)
    status = Column(Enum(AgentStatus), default=AgentStatus.CREATING, nullable=False)
    user_instructions = Column(Text, nullable=True)
    system_instructions = Column(Text, nullable=True)
    
    # OpenAPI configuration
    openapi_spec = Column(JSON, nullable=False)  # Store the full OpenAPI spec
    api_base_url = Column(String(500), nullable=True)
    encrypted_api_key = Column(Text, nullable=True)  # Encrypted user API key for the target API
    
    # Authentication configuration
    auth_type = Column(String(50), default="bearer", nullable=False)  # bearer, token, api_key, none, custom
    auth_header = Column(String(100), default="Authorization", nullable=False)  # Header name for auth
    auth_prefix = Column(String(50), nullable=True)  # Optional prefix like "Bearer", "token", etc.
    
    # Tool configuration
    tool_count = Column(Integer, default=0, nullable=False)
    available_tools = Column(JSON, nullable=True)  # List of available tool names/descriptions
    
    # ADK configuration
    model_name = Column(String(100), default="gemini-2.5-flash", nullable=False)
    use_user_gemini_key = Column(String(1), default="Y", nullable=False)  # Y/N flag
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_conversation_at = Column(DateTime(timezone=True), nullable=True)
    total_conversations = Column(Integer, default=0, nullable=False)
    total_tool_executions = Column(Integer, default=0, nullable=False)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="agents")
    conversations = relationship("Conversation", back_populates="agent", cascade="all, delete-orphan")
    tool_executions = relationship("ToolExecution", back_populates="agent", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name}, status={self.status})>"


class Conversation(Base):
    """Conversation model for storing chat history."""
    
    __tablename__ = "conversations"
    
    # Primary key  
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Conversation data
    conversation_id = Column(String(255), nullable=False, index=True)  # External conversation ID
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    execution_time = Column(String(50), nullable=True)  # Response time in seconds
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Foreign keys
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    agent = relationship("Agent", back_populates="conversations")
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, agent_id={self.agent_id}, conversation_id={self.conversation_id})>"


class ToolExecution(Base):
    """Tool execution model for tracking API calls and tool usage."""
    
    __tablename__ = "tool_executions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Tool execution data
    tool_name = Column(String(255), nullable=False, index=True)
    operation_id = Column(String(255), nullable=True, index=True)
    method = Column(String(10), nullable=True)  # GET, POST, etc.
    endpoint_path = Column(String(500), nullable=True)
    
    # Request/Response data
    request_args = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    status_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)  # Execution time in milliseconds
    
    # Context
    conversation_id = Column(String(255), nullable=True, index=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Foreign keys
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships  
    agent = relationship("Agent", back_populates="tool_executions")
    
    def __repr__(self) -> str:
        return f"<ToolExecution(id={self.id}, agent_id={self.agent_id}, tool_name={self.tool_name})>"


class Workflow(Base):
	"""Workflow model for storing multi-agent workflow executions."""
	
	__tablename__ = "workflows"
	
	# Primary key
	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
	
	# Workflow configuration
	name = Column(String(255), nullable=True)
	description = Column(Text, nullable=True)
	conversation_id = Column(String(255), nullable=False, index=True)
	
	# Execution metadata
	status = Column(String(50), default="running", nullable=False)  # running, completed, failed, partial_success
	total_execution_time = Column(Float, nullable=True)
	
	# Metadata
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
	
	# Foreign keys
	user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
	
	# Relationships
	user = relationship("User", back_populates="workflows")
	workflow_steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan")
	
	def __repr__(self) -> str:
		return f"<Workflow(id={self.id}, name={self.name}, status={self.status})>"


class WorkflowStep(Base):
	"""WorkflowStep model for storing individual steps in a workflow."""
	
	__tablename__ = "workflow_steps"
	
	# Primary key
	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
	
	# Step configuration
	step_name = Column(String(255), nullable=True)
	agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
	message = Column(Text, nullable=False)
	
	# Execution results
	response = Column(Text, nullable=True)
	tools_used = Column(JSON, nullable=True)  # List of tool names used
	execution_time = Column(Float, nullable=True)
	status = Column(String(50), default="pending", nullable=False)  # pending, running, success, error, skipped
	error_message = Column(Text, nullable=True)
	
	# Dependencies
	depends_on = Column(JSON, nullable=True)  # List of step names this depends on
	pass_result_to = Column(JSON, nullable=True)  # List of step names to pass result to
	
	# Metadata
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
	
	# Foreign keys
	workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False, index=True)
	
	# Relationships
	workflow = relationship("Workflow", back_populates="workflow_steps")
	agent = relationship("Agent")
	
	def __repr__(self) -> str:
		return f"<WorkflowStep(id={self.id}, step_name={self.step_name}, status={self.status})>"
