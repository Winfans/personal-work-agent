"""Agent orchestration service."""

from src.schemas.agent import AgentRequest, AgentResponse


class AgentService:
    """Coordinates model calls, tools, memory, and business workflows."""

    async def run(self, request: AgentRequest) -> AgentResponse:
        # Replace this starter response with the actual agent runtime.
        return AgentResponse(
            reply=f"Agent received: {request.message}",
            session_id=request.session_id,
        )


def get_agent_service() -> AgentService:
    return AgentService()
