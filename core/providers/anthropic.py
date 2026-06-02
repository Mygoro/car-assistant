import anthropic as _anthropic

from .base import Message, Delta


def _to_anthropic_messages(messages: list[Message]) -> list[dict]:
    result = []
    for m in messages:
        if m.role == "system":
            continue
        result.append({"role": m.role, "content": m.content})
    return result


class AnthropicProvider:
    def __init__(self, api_key: str, model: str, max_tokens: int):
        self._client = _anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def _build_kwargs(self, messages: list[Message], tools: list[dict]) -> dict:
        system = next((m.content for m in messages if m.role == "system"), None)
        kwargs: dict = dict(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=_to_anthropic_messages(messages),
            tools=tools if tools else [],
        )
        if system:
            # 시스템 프롬프트 캐싱: 매 턴 재전송 없이 5분간 캐시
            kwargs["system"] = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        return kwargs

    async def stream(self, messages: list[Message], tools: list[dict]):
        """스트리밍 텍스트 응답 (tool 없는 trivial 경로용)."""
        async with self._client.messages.stream(**self._build_kwargs(messages, tools)) as s:
            async for text in s.text_stream:
                yield Delta(text=text)
        yield Delta(text="", is_final=True)

    async def complete(self, messages: list[Message], tools: list[dict]) -> _anthropic.types.Message:
        """비스트리밍 완전 응답. tool_use 처리용."""
        return await self._client.messages.create(**self._build_kwargs(messages, tools))
