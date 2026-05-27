import anthropic as _anthropic

from .base import Message, Delta


class AnthropicProvider:
    def __init__(self, api_key: str, model: str, max_tokens: int):
        self._client = _anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    async def stream(self, messages: list[Message], tools: list[dict]):
        anthropic_messages = [
            {"role": m.role, "content": m.content}
            for m in messages if m.role != "system"
        ]
        system = next((m.content for m in messages if m.role == "system"), None)

        kwargs: dict = dict(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=anthropic_messages,
            tools=tools if tools else [],
        )
        if system:
            # 시스템 프롬프트 캐싱: 매 턴 3700자를 새로 보내지 않고 5분간 캐시
            kwargs["system"] = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]

        async with self._client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield Delta(text=text)
        yield Delta(text="", is_final=True)
