import json

import httpx

from .base import Message, Delta


class OllamaProvider:
    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    async def stream(self, messages: list[Message], tools: list[dict]):
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    if content := data.get("message", {}).get("content", ""):
                        yield Delta(text=content)
                    if data.get("done"):
                        yield Delta(text="", is_final=True)
                        return
