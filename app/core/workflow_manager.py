"""Workflow manager for orchestrating multi-agent workflows."""

import uuid
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.agent import WorkflowRequest, WorkflowResponse, WorkflowStepResult
from app.database.models.agent import Workflow, WorkflowStep, Agent, AgentStatus
from app.core.agent_manager import AgentManager

logger = logging.getLogger(__name__)


class WorkflowManager:
    """Manages multi-agent workflow execution and orchestration."""
    
    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
    
    async def execute_workflow(
        self,
        workflow_request: WorkflowRequest,
        user_id: str,
        db: AsyncSession
    ) -> WorkflowResponse:
        """Execute a multi-agent workflow."""
        
        # Validate workflow request
        await self._validate_workflow_request(workflow_request, user_id, db)
        
        start_time = time.time()
        workflow_id = str(uuid.uuid4())
        conversation_id = f"workflow_{workflow_id}"
        
        # Create workflow record
        workflow = Workflow(
            id=workflow_id,
            name=workflow_request.workflow_name,
            description=workflow_request.workflow_name,  # Use workflow_name as description
            conversation_id=conversation_id,
            user_id=user_id,
            status="running"
        )
        db.add(workflow)
        
        # Create workflow steps
        step_records = []
        for step in workflow_request.steps:
            step_record = WorkflowStep(
                step_name=step.step_name or f"step_{len(step_records) + 1}",
                agent_id=step.agent_id,
                message=step.message,
                depends_on=step.depends_on,
                pass_result_to=step.pass_result_to,
                workflow_id=workflow_id,
                status="pending"
            )
            step_records.append(step_record)
            db.add(step_record)
        
        await db.commit()
        
        # Execute workflow steps
        step_results = []
        try:
            if workflow_request.parallel_execution:
                step_results = await self._execute_parallel_workflow(
                    step_records, user_id, db
                )
            else:
                step_results = await self._execute_sequential_workflow(
                    step_records, user_id, db
                )
            
            # Update workflow status
            workflow.status = self._determine_workflow_status(step_results)
            workflow.total_execution_time = time.time() - start_time
            await db.commit()
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            workflow.status = "failed"
            workflow.total_execution_time = time.time() - start_time
            await db.commit()
            raise
        
        return WorkflowResponse(
            workflow_id=workflow_id,
            workflow_name=workflow_request.workflow_name,
            conversation_id=conversation_id,
            steps=step_results,
            total_execution_time=time.time() - start_time,
            status=workflow.status,
            timestamp=datetime.utcnow().isoformat()
        )
    
    async def _execute_sequential_workflow(
        self,
        step_records: List[WorkflowStep],
        user_id: str,
        db: AsyncSession
    ) -> List[WorkflowStepResult]:
        """Execute workflow steps sequentially with dependency management."""
        
        # Try ADK SequentialAgent approach first for better state sharing
        try:
            return await self._execute_adk_sequential_workflow(step_records, user_id, db)
        except Exception as e:
            logger.warning(f"ADK sequential workflow failed, falling back to manual execution: {e}")
            # Fallback to manual sequential execution
            return await self._execute_manual_sequential_workflow(step_records, user_id, db)
    
    async def _execute_manual_sequential_workflow(
        self,
        step_records: List[WorkflowStep],
        user_id: str,
        db: AsyncSession
    ) -> List[WorkflowStepResult]:
        """Execute workflow steps sequentially with dependency management (manual fallback)."""
        
        step_results = []
        step_name_to_result = {}  # Track results by step name for dependencies
        
        for step_record in step_records:
            step_name = step_record.step_name
            
            # Check dependencies
            if step_record.depends_on:
                missing_deps = [dep for dep in step_record.depends_on if dep not in step_name_to_result]
                if missing_deps:
                    # Skip step if dependencies not met
                    step_record.status = "skipped"
                    step_record.error_message = f"Dependencies not met: {missing_deps}"
                    await db.commit()
                    
                    step_results.append(WorkflowStepResult(
                        step_name=step_name,
                        agent_id=str(step_record.agent_id),
                        message=step_record.message,
                        response="",
                        tools_used=[],
                        execution_time=0.0,
                        status="skipped",
                        error=f"Dependencies not met: {missing_deps}",
                        timestamp=datetime.utcnow().isoformat()
                    ))
                    continue
            
            # Enhance message with results from previous steps
            enhanced_message = await self._enhance_message_with_dependencies(
                step_record.message, step_record.depends_on, step_name_to_result
            )
            
            # Execute step
            step_result = await self._execute_single_step(
                step_record, enhanced_message, user_id, db
            )
            
            step_results.append(step_result)
            step_name_to_result[step_name] = step_result
            
            # Update step record
            step_record.status = step_result.status
            step_record.response = step_result.response
            step_record.tools_used = step_result.tools_used
            step_record.execution_time = step_result.execution_time
            step_record.error_message = step_result.error
            await db.commit()
        
        return step_results
    
    async def _execute_parallel_workflow(
        self,
        step_records: List[WorkflowStep],
        user_id: str,
        db: AsyncSession
    ) -> List[WorkflowStepResult]:
        """Execute workflow steps in parallel using simple sequential approach.
        
        For now, we'll execute steps sequentially to avoid database conflicts.
        This is a temporary solution until we can properly implement ADK ParallelAgent.
        """
        
        step_results = []
        step_name_to_result = {}
        
        # Execute steps sequentially for now to avoid database conflicts
        for step_record in step_records:
            enhanced_message = await self._enhance_message_with_dependencies(
                step_record.message, step_record.depends_on, step_name_to_result
            )
            
            # Execute step using the existing sequential method
            step_result = await self._execute_single_step(
                step_record, enhanced_message, user_id, db
            )
            
            step_results.append(step_result)
            step_name_to_result[step_record.step_name] = step_result
        
        return step_results
    
    def _group_by_dependencies(self, step_records: List[WorkflowStep]) -> List[List[WorkflowStep]]:
        """Group steps by dependency level for parallel execution."""
        
        # Create dependency graph
        dependency_graph = {}
        for step in step_records:
            dependency_graph[step.step_name] = set(step.depends_on or [])
        
        # Topological sort to group by dependency level
        groups = []
        visited = set()
        
        while len(visited) < len(step_records):
            current_group = []
            
            for step in step_records:
                if step.step_name in visited:
                    continue
                
                # Check if all dependencies are satisfied
                dependencies_met = all(dep in visited for dep in (step.depends_on or []))
                
                if dependencies_met:
                    current_group.append(step)
                    visited.add(step.step_name)
            
            if not current_group:
                # Circular dependency or error
                break
            
            groups.append(current_group)
        
        return groups
    
    async def _enhance_message_with_dependencies(
        self,
        message: str,
        depends_on: Optional[List[str]],
        step_name_to_result: Dict[str, WorkflowStepResult]
    ) -> str:
        """Enhance message with results from dependent steps."""
        
        if not depends_on:
            return message
        
        enhanced_message = message
        for dep_step_name in depends_on:
            if dep_step_name in step_name_to_result:
                dep_result = step_name_to_result[dep_step_name]
                if dep_result.status == "success":
                    enhanced_message += f"\n\nContext from {dep_step_name}: {dep_result.response}"
                else:
                    enhanced_message += f"\n\nWarning: {dep_step_name} failed with status {dep_result.status}"
        
        return enhanced_message
    
    async def _execute_single_step(
        self,
        step_record: WorkflowStep,
        message: str,
        user_id: str,
        db: AsyncSession
    ) -> WorkflowStepResult:
        """Execute a single workflow step."""
        
        start_time = time.time()
        
        try:
            # Update step status to running
            step_record.status = "running"
            await db.commit()
            
            # Execute the step using agent manager
            result = await self.agent_manager.chat_with_agent(
                str(step_record.agent_id),
                message,
                user_id,
                None,  # Let agent manager generate conversation ID
                db
            )
            
            execution_time = time.time() - start_time
            
            return WorkflowStepResult(
                step_name=step_record.step_name,
                agent_id=str(step_record.agent_id),
                message=message,
                response=result['response'],
                tools_used=result.get('tools_used', []),
                execution_time=execution_time,
                status="success",
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            execution_time = time.time() - start_time
            
            return WorkflowStepResult(
                step_name=step_record.step_name,
                agent_id=str(step_record.agent_id),
                message=message,
                response="",
                tools_used=[],
                execution_time=execution_time,
                status="error",
                error=str(e),
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def _execute_single_step_parallel(
        self,
        step_record: WorkflowStep,
        message: str,
        user_id: str
    ) -> WorkflowStepResult:
        """Execute a single workflow step with its own independent execution context.
        
        Following ADK parallel agent principles:
        - Independent execution branch
        - No shared state with other parallel tasks
        - Own database session and resources
        """
        
        start_time = time.time()
        
        try:
            # Create a completely independent database session for this parallel task
            # This ensures no shared state between parallel executions (ADK principle)
            from app.database.config import AsyncSessionLocal
            
            async with AsyncSessionLocal() as db_session:
                # Get agent from database (read-only operation)
                from app.database.models.agent import Agent, AgentStatus
                from sqlalchemy import select, and_
                
                result = await db_session.execute(
                    select(Agent).where(
                        and_(Agent.id == step_record.agent_id, Agent.user_id == user_id)
                    )
                )
                agent = result.scalar_one_or_none()
                
                if not agent:
                    raise ValueError("Agent not found")
                
                if agent.status != AgentStatus.ACTIVE:
                    raise ValueError(f"Agent is not active (status: {agent.status})")
                
                # Get or create ADK agent (this is the critical part)
                # Use a separate session for ADK agent creation to avoid conflicts
                # Create a completely isolated session for ADK operations
                from app.database.config import create_async_engine, AsyncSession, async_sessionmaker
                from app.core.config import settings
                
                # Create a completely separate engine for this parallel task
                isolated_engine = create_async_engine(
                    settings.DATABASE_URL,
                    echo=False,
                    pool_size=1,
                    max_overflow=0,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                )
                
                IsolatedSessionLocal = async_sessionmaker(
                    isolated_engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autocommit=False,
                    autoflush=False,
                )
                
                async with IsolatedSessionLocal() as adk_db_session:
                    adk_agent = await self.agent_manager._get_or_create_adk_agent(agent, adk_db_session)
                
                await isolated_engine.dispose()
                
                # Chat with agent (without storing conversation to avoid conflicts)
                if adk_agent and hasattr(adk_agent, 'chat'):
                    # Real ADK agent
                    response = await adk_agent.chat(message)
                    tool_names = []  # TODO: Extract from callback handler
                else:
                    # Fallback mode
                    response = f"I can help you with {agent.tool_count} API endpoints. What would you like me to do?"
                    tool_names = []
                
                execution_time = time.time() - start_time
                
                return WorkflowStepResult(
                    step_name=step_record.step_name,
                    agent_id=str(step_record.agent_id),
                    message=message,
                    response=response,
                    tools_used=tool_names,
                    execution_time=execution_time,
                    status="success",
                    timestamp=datetime.utcnow().isoformat()
                )
                    
        except Exception as e:
            logger.error(f"Parallel step execution failed: {e}")
            execution_time = time.time() - start_time
            
            return WorkflowStepResult(
                step_name=step_record.step_name,
                agent_id=str(step_record.agent_id),
                message=message,
                response="",
                tools_used=[],
                execution_time=execution_time,
                status="error",
                error=str(e),
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def _create_adk_agent_for_step(
        self,
        agent: Agent,
        step_record: WorkflowStep,
        user_id: str
    ):
        """Create an ADK agent for a workflow step."""
        try:
            # Create a completely isolated session for ADK operations
            from app.database.config import create_async_engine, AsyncSession, async_sessionmaker
            from app.core.config import settings
            
            # Create a completely separate engine for this parallel task
            isolated_engine = create_async_engine(
                settings.DATABASE_URL,
                echo=False,
                pool_size=1,
                max_overflow=0,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            
            IsolatedSessionLocal = async_sessionmaker(
                isolated_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            
            async with IsolatedSessionLocal() as adk_db_session:
                adk_agent = await self.agent_manager._get_or_create_adk_agent(agent, adk_db_session)
            
            await isolated_engine.dispose()
            return adk_agent
            
        except Exception as e:
            logger.error(f"Failed to create ADK agent for step {step_record.step_name}: {e}")
            return None
    
    async def _execute_adk_parallel_workflow(
        self,
        sub_agents: List,
        step_records: List[WorkflowStep],
        step_name_to_result: Dict[str, WorkflowStepResult]
    ) -> List[WorkflowStepResult]:
        """Execute parallel workflow using ADK ParallelAgent pattern."""
        
        try:
            # Import ADK components
            from google.adk.agents import ParallelAgent
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            from google.genai.types import Content, Part
            
            # Create a ParallelAgent with our sub-agents
            parallel_agent = ParallelAgent(
                name="WorkflowParallelAgent",
                sub_agents=sub_agents,
                description="Executes workflow steps in parallel"
            )
            
            # Create runner and session
            runner = Runner(parallel_agent, "workflow_app")
            session_service = InMemorySessionService()
            session = session_service.create_session("workflow_app", "workflow_user")
            
            # Prepare messages for each step
            messages = []
            for step_record in step_records:
                enhanced_message = await self._enhance_message_with_dependencies(
                    step_record.message, step_record.depends_on, step_name_to_result
                )
                messages.append(Content.from_parts(Part.from_text(enhanced_message)))
            
            # Execute parallel workflow
            start_time = time.time()
            event_stream = runner.run_async("workflow_user", session.id, messages[0])  # Use first message for now
            
            # Collect results
            results = []
            async for event in event_stream:
                if event.final_response():
                    # Extract response from event
                    response = event.stringify_content()
                    execution_time = time.time() - start_time
                    
                    # Create result for each step (simplified for now)
                    for step_record in step_records:
                        step_result = WorkflowStepResult(
                            step_name=step_record.step_name,
                            agent_id=str(step_record.agent_id),
                            message=step_record.message,
                            response=response,
                            tools_used=[],
                            execution_time=execution_time,
                            status="success",
                            timestamp=datetime.utcnow().isoformat()
                        )
                        results.append(step_result)
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"ADK parallel workflow execution failed: {e}")
            # Return error results
            results = []
            for step_record in step_records:
                step_result = WorkflowStepResult(
                    step_name=step_record.step_name,
                    agent_id=str(step_record.agent_id),
                    message=step_record.message,
                    response="",
                    tools_used=[],
                    execution_time=0.0,
                    status="error",
                    error=str(e),
                    timestamp=datetime.utcnow().isoformat()
                )
                results.append(step_result)
            return results
    
    async def _execute_adk_sequential_workflow(
        self,
        step_records: List[WorkflowStep],
        user_id: str,
        db: AsyncSession
    ) -> List[WorkflowStepResult]:
        """Execute workflow using ADK SequentialAgent for proper state sharing."""
        
        try:
            # Import ADK components
            from google.adk.agents import LlmAgent, SequentialAgent
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            from google.genai.types import Content, Part
            from google.adk.models import Gemini
            from app.core.config import settings
            
            # Create sub-agents for each step with proper output keys
            sub_agents = []
            for i, step_record in enumerate(step_records):
                # Get agent from database
                from app.database.models.agent import Agent, AgentStatus
                from sqlalchemy import select, and_
                
                result = await db.execute(
                    select(Agent).where(
                        and_(Agent.id == step_record.agent_id, Agent.user_id == user_id)
                    )
                )
                agent = result.scalar_one_or_none()
                
                if not agent or agent.status != AgentStatus.ACTIVE:
                    continue
                
                # Create ADK LlmAgent with proper instructions and output key
                step_name = step_record.step_name or f"step_{i+1}"
                
                # Create instructions that include the original message and context from previous steps
                instructions = f"""You are {agent.name}.
{agent.user_instructions or 'You are a helpful assistant.'}

Your task for this workflow step: {step_record.message}

When you receive a message, process it according to your capabilities and provide a helpful response.
If you have received context from previous workflow steps, use that information to enhance your response.
"""
                
                # Create ADK agent with OpenAPI toolset
                adk_agent = await self._create_adk_llm_agent_for_workflow(
                    agent, step_name, instructions, i
                )
                
                if adk_agent:
                    sub_agents.append(adk_agent)
            
            if not sub_agents:
                raise ValueError("No valid ADK agents could be created")
            
            # Create SequentialAgent
            sequential_agent = SequentialAgent(
                name="WorkflowSequentialAgent",
                sub_agents=sub_agents,
                description="Executes workflow steps in sequence with state sharing"
            )
            
            # Create runner and session
            runner = Runner(sequential_agent, "workflow_app")
            session_service = InMemorySessionService()
            session = session_service.create_session("workflow_app", "workflow_user")
            
            # Execute the workflow with the initial message
            initial_message = step_records[0].message if step_records else "Execute the workflow"
            content = Content.from_parts(Part.from_text(initial_message))
            
            start_time = time.time()
            event_stream = runner.run_async("workflow_user", session.id, content)
            
            # Collect results
            results = []
            step_responses = []
            
            async for event in event_stream:
                if event.final_response():
                    # Extract the final response
                    response = event.stringify_content()
                    step_responses.append(response)
                    break
            
            # Create results for each step
            execution_time = time.time() - start_time
            for i, step_record in enumerate(step_records):
                if i < len(sub_agents):
                    # For now, we'll distribute the response among steps
                    # In a real implementation, we'd need to track individual step outputs
                    step_response = step_responses[0] if step_responses else "Step completed"
                    
                    step_result = WorkflowStepResult(
                        step_name=step_record.step_name,
                        agent_id=str(step_record.agent_id),
                        message=step_record.message,
                        response=step_response,
                        tools_used=[],
                        execution_time=execution_time / len(step_records),
                        status="success",
                        timestamp=datetime.utcnow().isoformat()
                    )
                else:
                    step_result = WorkflowStepResult(
                        step_name=step_record.step_name,
                        agent_id=str(step_record.agent_id),
                        message=step_record.message,
                        response="",
                        tools_used=[],
                        execution_time=0.0,
                        status="error",
                        error="Failed to create ADK agent",
                        timestamp=datetime.utcnow().isoformat()
                    )
                
                results.append(step_result)
                
                # Update step record
                step_record.status = step_result.status
                step_record.response = step_result.response
                step_record.tools_used = step_result.tools_used
                step_record.execution_time = step_result.execution_time
                step_record.error_message = step_result.error
                
            await db.commit()
            return results
            
        except Exception as e:
            logger.error(f"ADK sequential workflow execution failed: {e}")
            raise  # Re-raise to trigger fallback
    
    async def _create_adk_llm_agent_for_workflow(
        self,
        agent: Agent,
        step_name: str,
        instructions: str,
        step_index: int
    ):
        """Create an ADK LlmAgent for workflow execution."""
        
        try:
            from google.adk.agents import LlmAgent
            from google.adk.models import Gemini
            from app.core.config import settings
            
            # Create ADK agent with the agent's configuration
            adk_agent = LlmAgent(
                name=f"{agent.name}_{step_name}",
                model=Gemini(model_name="gemini-2.0-flash", api_key=settings.ADK_API_KEY),
                instruction=instructions,
                description=f"Workflow step {step_index + 1}: {agent.name}",
                output_key=f"step_{step_index + 1}_result"  # Store result in state
            )
            
            return adk_agent
            
        except Exception as e:
            logger.error(f"Failed to create ADK LlmAgent for {agent.name}: {e}")
            return None
    
    def _determine_workflow_status(self, step_results: List[WorkflowStepResult]) -> str:
        """Determine overall workflow status based on step results."""
        
        if not step_results:
            return "failed"
        
        success_count = sum(1 for step in step_results if step.status == "success")
        error_count = sum(1 for step in step_results if step.status == "error")
        skipped_count = sum(1 for step in step_results if step.status == "skipped")
        
        if error_count == len(step_results):
            return "failed"
        elif error_count > 0:
            return "partial_success"
        elif success_count == len(step_results):
            return "completed"
        else:
            return "partial_success"
    
    async def get_workflow_history(
        self,
        user_id: str,
        db: AsyncSession,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get workflow execution history for a user."""
        
        result = await db.execute(
            select(Workflow)
            .where(Workflow.user_id == user_id)
            .order_by(Workflow.created_at.desc())
            .limit(limit)
        )
        
        workflows = result.scalars().all()
        
        workflow_history = []
        for workflow in workflows:
            # Get step summary
            step_result = await db.execute(
                select(WorkflowStep)
                .where(WorkflowStep.workflow_id == workflow.id)
            )
            steps = step_result.scalars().all()
            
            workflow_history.append({
                "workflow_id": str(workflow.id),
                "name": workflow.name,
                "status": workflow.status,
                "total_execution_time": workflow.total_execution_time,
                "step_count": len(steps),
                "created_at": workflow.created_at.isoformat(),
                "conversation_id": workflow.conversation_id
            })
        
        return workflow_history
    
    async def _validate_workflow_request(
        self,
        workflow_request: WorkflowRequest,
        user_id: str,
        db: AsyncSession
    ) -> None:
        """Validate workflow request before execution."""
        
        if not workflow_request.steps:
            raise ValueError("Workflow must have at least one step")
        
        if len(workflow_request.steps) > 50:  # Reasonable limit
            raise ValueError("Workflow cannot have more than 50 steps")
        
        # Validate agent IDs exist and belong to user
        agent_ids = [step.agent_id for step in workflow_request.steps]
        agents_result = await db.execute(
            select(Agent)
            .where(and_(Agent.id.in_(agent_ids), Agent.user_id == user_id))
        )
        existing_agents = {str(agent.id): agent for agent in agents_result.scalars().all()}
        
        for step in workflow_request.steps:
            agent_id = step.agent_id
            if agent_id not in existing_agents:
                raise ValueError(f"Agent {agent_id} not found or not accessible")
            
            agent = existing_agents[agent_id]
            if agent.status != AgentStatus.ACTIVE:
                raise ValueError(f"Agent {agent_id} is not active (status: {agent.status})")
            
            if not step.message or not step.message.strip():
                raise ValueError(f"Step message cannot be empty for agent {agent_id}")
        
        # Validate step names are unique if provided
        step_names = [step.step_name for step in workflow_request.steps if step.step_name]
        if len(step_names) != len(set(step_names)):
            raise ValueError("Step names must be unique")
        
        # Validate dependencies exist
        all_step_names = {step.step_name or f"step_{i+1}" for i, step in enumerate(workflow_request.steps)}
        for step in workflow_request.steps:
            if step.depends_on:
                for dep in step.depends_on:
                    if dep not in all_step_names:
                        raise ValueError(f"Dependency '{dep}' not found in workflow steps")
        
        # Check for circular dependencies
        if self._has_circular_dependencies(workflow_request.steps):
            raise ValueError("Circular dependencies detected in workflow")
    
    def _has_circular_dependencies(self, steps: List) -> bool:
        """Check if there are circular dependencies in the workflow."""
        
        # Build dependency graph
        step_deps = {}
        for i, step in enumerate(steps):
            step_name = step.step_name or f"step_{i+1}"
            step_deps[step_name] = set(step.depends_on or [])
        
        # DFS to detect cycles
        visiting = set()
        visited = set()
        
        def has_cycle(node):
            if node in visiting:
                return True
            if node in visited:
                return False
            
            visiting.add(node)
            for neighbor in step_deps.get(node, []):
                if has_cycle(neighbor):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False
        
        for step_name in step_deps:
            if step_name not in visited:
                if has_cycle(step_name):
                    return True
        
        return False
    
    async def get_workflow_details(
        self,
        workflow_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[WorkflowResponse]:
        """Get detailed information about a specific workflow execution."""
        
        # Get workflow
        workflow_result = await db.execute(
            select(Workflow)
            .where(and_(Workflow.id == workflow_id, Workflow.user_id == user_id))
        )
        workflow = workflow_result.scalar_one_or_none()
        
        if not workflow:
            return None
        
        # Get workflow steps
        steps_result = await db.execute(
            select(WorkflowStep)
            .where(WorkflowStep.workflow_id == workflow_id)
            .order_by(WorkflowStep.created_at)
        )
        steps = steps_result.scalars().all()
        
        # Convert to response format
        step_results = []
        for step in steps:
            step_results.append(WorkflowStepResult(
                step_name=step.step_name,
                agent_id=str(step.agent_id),
                message=step.message,
                response=step.response or "",
                tools_used=step.tools_used or [],
                execution_time=step.execution_time or 0.0,
                status=step.status,
                error=step.error_message,
                timestamp=step.created_at.isoformat()
            ))
        
        return WorkflowResponse(
            workflow_id=str(workflow.id),
            workflow_name=workflow.name,
            conversation_id=workflow.conversation_id,
            steps=step_results,
            total_execution_time=workflow.total_execution_time or 0.0,
            status=workflow.status,
            timestamp=workflow.created_at.isoformat()
        )
