from dataclasses import dataclass, field
from typing import Protocol, AsyncIterator, Union, runtime_checkable


@dataclass
class Message:
    role: str   # "user" | "assistant" | "system"
    content: Union[str, list[dict]]  # str: 일반 텍스트, list[dict]: tool_use/tool_result 블록


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
