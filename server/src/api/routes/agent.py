"""Agent execution endpoints."""

from fastapi import APIRouter, Depends

from src.schemas.agent import AgentRequest, AgentResponse
from src.services.agent import AgentService, get_agent_service

router = APIRouter()


@router.post("/run", response_model=AgentResponse)
async def run_agent(
    request: AgentRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    return await service.run(request)
