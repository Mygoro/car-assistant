from dataclasses import dataclass, field
from typing import Protocol, AsyncIterator, runtime_checkable


@dataclass
class Message:
    role: str   # "user" | "assistant" | "system"
    content: str


@dataclass
class Delta:
    text: str
    is_final: bool = False


@runtime_checkable
class LLMProvider(Protocol):
    async def stream(
        self,
        messages: list[Message],
        tools: list[dict],
    ) -> AsyncIterator[Delta]: ...
