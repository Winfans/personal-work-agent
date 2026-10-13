"""LangChain-powered streaming chat service."""

from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.config import settings
from src.schemas.chat import ChatMessage, TextChatRequest


def _to_langchain_message(message: ChatMessage) -> BaseMessage:
    message_types = {
        "system": SystemMessage,
        "user": HumanMessage,
        "assistant": AIMessage,
    }
    return message_types[message.role](content=message.content)


class ChatService:
    """Streams model output through LangChain's chat model interface."""

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    async def stream_text(self, request: TextChatRequest) -> AsyncIterator[str]:
        chat_model = ChatOpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            model=self._model,
            temperature=request.temperature,
            streaming=True,
        )
        messages = [_to_langchain_message(message) for message in request.messages]

        async for chunk in chat_model.astream(messages):
            content = chunk.content
            if isinstance(content, str) and content:
                yield content


def get_chat_service() -> ChatService:
    if not settings.bailian_api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not configured")

    return ChatService(
        api_key=settings.bailian_api_key,
        base_url=settings.bailian_base_url,
        model=settings.bailian_model,
    )
