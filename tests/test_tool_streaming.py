"""티어2 _tool_voice_streaming 오프라인 검증 (실 API 없음).

가짜 provider.stream_tools로 (a) 최종 turn에서 voice가 text보다 먼저, 정확히 디코딩돼
방출되는지, (b) tool turn → end_turn 멀티 iteration에서 filler·tool 실행·순서가 맞는지 확인.
"""
import asyncio
import json

from core.orchestrator import Orchestrator
from core.providers.base import Message


class _Blk:
    def __init__(self, **kw):
        self.__dict__.update(kw)
    def model_dump(self):
        return {k: v for k, v in self.__dict__.items()}


class _Final:
    def __init__(self, stop_reason, content):
        self.stop_reason = stop_reason
        self.content = content


def _chunks(s, n=7):
    return [s[i:i + n] for i in range(0, len(s), n)]


class _FakeProvider:
    """scripted turns: 각 turn은 (text, final). stream_tools가 text를 조각내 흘리고 final 방출."""
    model = "fake"
    def __init__(self, turns):
        self._turns = list(turns)
    async def stream_tools(self, messages, tools):
        text, final = self._turns.pop(0)
        for c in _chunks(text):
            yield ("text_delta", c)
        yield ("final", final)


def _orch():
    cfg = {"llm": {}, "tool_use": {"stream_final": True}}
    return Orchestrator(cfg=cfg, anthropic_api_key="")


async def _drain(agen):
    return [x async for x in agen]


def test_final_turn_voice_before_text():
    o = _orch()
    raw = json.dumps({"voice_response": "강남 카페 추천해요", "text_response": "## 상세\n" + "x" * 500}, ensure_ascii=False)
    prov = _FakeProvider([(raw, _Final("end_turn", []))])
    out = asyncio.run(_drain(o._tool_voice_streaming(prov, [Message("user", "q")], "q")))
    stages = [s for s, _ in out]
    assert stages == ["voice", "text"], stages
    assert out[0][1] == "강남 카페 추천해요", out[0]
    assert out[1][1].startswith("## 상세")
    print("OK final_turn_voice_before_text")


def test_escaped_and_korean_voice():
    o = _orch()
    raw = json.dumps({"voice_response": '그는 "안녕" 했어요', "text_response": "t"}, ensure_ascii=False)
    prov = _FakeProvider([(raw, _Final("end_turn", []))])
    out = asyncio.run(_drain(o._tool_voice_streaming(prov, [Message("user", "q")], "q")))
    assert out[0] == ("voice", '그는 "안녕" 했어요'), out[0]
    print("OK escaped_and_korean_voice")


def test_tool_iteration_then_final():
    o = _orch()
    # tool turn은 JSON 없음(프롬프트 규칙) → voice 미방출. native 툴 등록.
    async def fake_tool(args):
        return "- 카몽: 서울 서초구\n"
    from core.orchestrator import ToolHandle
    o._tools["search_nearby_places"] = ToolHandle(
        name="search_nearby_places",
        schema={"name": "search_nearby_places", "description": "d", "input_schema": {}},
        kind="native", native_fn=fake_tool,
    )
    tool_final = _Final("tool_use", [_Blk(type="tool_use", name="search_nearby_places", input={"query": "강남"}, id="t1")])
    raw = json.dumps({"voice_response": "카몽 추천해요", "text_response": "상세"}, ensure_ascii=False)
    prov = _FakeProvider([("", tool_final), (raw, _Final("end_turn", []))])
    out = asyncio.run(_drain(o._tool_voice_streaming(prov, [Message("user", "q")], "q")))
    stages = [s for s, _ in out]
    assert stages == ["filler", "voice", "text"], stages
    assert out[1][1] == "카몽 추천해요", out[1]
    print("OK tool_iteration_then_final")


if __name__ == "__main__":
    test_final_turn_voice_before_text()
    test_escaped_and_korean_voice()
    test_tool_iteration_then_final()
    print("ALL PASS")
