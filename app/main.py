from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.agent_manager import AgentManager
from app.api.routes import agents, health, auth, marketplace, workflows
from app.utils.logging import setup_logging
from app.database.config import init_db, close_db
from app.core.config import settings

logger = logging.getLogger(__name__)
_agent_manager: AgentManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
	"""Application lifespan manager."""
	global _agent_manager
	
	# Initialize logging
	setup_logging()
	logger.info("Starting OpenAPI Conversational Agent Platform")
	
	# Initialize database
	try:
		await init_db()
		logger.info("Database initialized successfully")
	except Exception as e:
		logger.error(f"Database initialization failed: {e}")
		raise
	
	# Initialize agent manager
	_agent_manager = AgentManager()
	logger.info("Agent manager initialized")
	
	yield
	
	# Cleanup
	try:
		await close_db()
		logger.info("Database connections closed")
	except Exception as e:
		logger.error(f"Database cleanup failed: {e}")


app = FastAPI(
	title=settings.PLATFORM_NAME,
	version=settings.PLATFORM_VERSION,
	description="Transform any OpenAPI specification into an intelligent conversational agent using Google ADK",
	lifespan=lifespan
)


app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(marketplace.router, prefix="/marketplace", tags=["Marketplace"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["Workflows"])


@app.middleware("http")
async def add_agent_manager(request, call_next):
	request.state.agent_manager = _agent_manager
	return await call_next(request)


@app.get("/")
async def root():
	return {"message": "OpenAPI Conversational Agent Platform"}





