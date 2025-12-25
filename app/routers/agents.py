"""
Multi-Agent router - Agent orchestration
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.agents.agent_orchestrator import AgentOrchestrator

router = APIRouter()


class AgentRequest(BaseModel):
    task: str
    agents: Optional[List[str]] = None
    strategy: str = "parallel"  # parallel, sequential, collaborative


class AgentResponse(BaseModel):
    result: str
    agents_used: List[str]
    execution_time: float


@router.post("/execute", response_model=AgentResponse)
async def execute_with_agents(request: AgentRequest):
    """Execute task using multiple agents"""
    try:
        orchestrator = AgentOrchestrator()
        result = await orchestrator.execute_task(
            task=request.task,
            agents=request.agents,
            strategy=request.strategy
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_agents():
    """List available agents"""
    return {
        "agents": [
            {"id": "researcher", "name": "Research Agent", "description": "Web research and information gathering"},
            {"id": "coder", "name": "Code Agent", "description": "Code generation and debugging"},
            {"id": "analyst", "name": "Analysis Agent", "description": "Data analysis and insights"},
            {"id": "writer", "name": "Writing Agent", "description": "Content creation and editing"},
        ]
    }

