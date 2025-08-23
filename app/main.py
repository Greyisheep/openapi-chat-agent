from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.agent_manager import AgentManager
from app.api.routes import agents, health
from app.utils.logging import setup_logging


_agent_manager: AgentManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
	global _agent_manager
	_agent_manager = AgentManager()
	setup_logging()
	yield


app = FastAPI(title="OpenAPI Conversational Agent Platform", version="0.1.0", lifespan=lifespan)


app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])


@app.middleware("http")
async def add_agent_manager(request, call_next):
	request.state.agent_manager = _agent_manager
	return await call_next(request)


@app.get("/")
async def root():
	return {"message": "OpenAPI Conversational Agent Platform"}




