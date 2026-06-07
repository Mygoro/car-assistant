"""회귀 테스트 러너 — tests/regression_cases.yaml의 케이스를 실행·검증한다.

케이스는 발화(또는 멀티턴)를 Orchestrator에 넣고, 호출된 tool·인텐트·응답을
결정적으로 검증한다. 200+ 케이스를 매번 LLM으로 돌리면 비싸므로,
기본은 --dry-run(실행 없이 케이스 통계만)이고 --run으로만 실제 호출한다.

사용법:
    uv run tools/run_regression.py                       # dry-run: 케이스 수·카테고리 통계
    uv run tools/run_regression.py --run                 # 전체 실행(비용 큼)
    uv run tools/run_regression.py --run --category vehicle
    uv run tools/run_regression.py --run --limit 20      # 앞 20개만
    uv run tools/run_regression.py --run --category calendar_read,vehicle

스키마 (tests/regression_cases.yaml):
    - id: <고유 id>
      category: <카테고리>
      utterance: "<단일 발화>"          # 또는 turns
      turns: ["발화1", "발화2"]          # 멀티턴(마지막 턴 결과로 검증)
      expect_intent: default|trivial|complex_reasoning   # (선택) classify_intent 기대
      expect_tools: [tool_a, tool_b]    # (선택) 호출돼야 할 tool(부분집합)
      forbid_tools: [tool_x]            # (선택) 호출되면 안 되는 tool
      must_include: ["문자열"]           # (선택) voice+text에 있어야 함
      must_not_include: ["연료", "%"]    # (선택) 있으면 실패
      allow_empty: true                 # (선택) voice·text 둘 다 빈 게 정상(필러 등)
      notes: "<의도 설명>"
"""
import argparse
import asyncio
import io
import os
import sys
from collections import Counter
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from dotenv import load_dotenv

from core.orchestrator import Orchestrator, classify_intent, validate_voice_length

load_dotenv()

GREEN, RED, YELLOW, GREY, CYAN, BOLD, RESET = (
    "\033[92m", "\033[91m", "\033[93m", "\033[90m", "\033[96m", "\033[1m", "\033[0m"
)

CASES_PATH = Path("tests/regression_cases.yaml")


def load_cases() -> list[dict]:
    if not CASES_PATH.exists():
        print(f"{RED}케이스 파일 없음: {CASES_PATH}{RESET}")
        sys.exit(1)
    with open(CASES_PATH, encoding="utf-8") as f:
        cases = yaml.safe_load(f) or []
    # id 중복 검사
    ids = [c.get("id") for c in cases]
    dup = [i for i, n in Counter(ids).items() if n > 1]
    if dup:
        print(f"{RED}중복 id: {dup}{RESET}")
        sys.exit(1)
    return cases


def print_stats(cases: list[dict]) -> None:
    by_cat = Counter(c.get("category", "?") for c in cases)
    print(f"\n{BOLD}=== 회귀 케이스 통계 ==={RESET}")
    print(f"총 {BOLD}{len(cases)}{RESET}개 / 카테고리 {len(by_cat)}종\n")
    for cat, n in sorted(by_cat.items()):
        bar = "█" * n
        print(f"  {cat:24s} {n:3d}  {GREY}{bar}{RESET}")
    # 검증 항목을 가진 케이스 비율
    with_tools = sum(1 for c in cases if c.get("expect_tools"))
    with_assert = sum(1 for c in cases if c.get("must_include") or c.get("must_not_include"))
    print(f"\n  {GREY}expect_tools 지정: {with_tools} / must_(not_)include 지정: {with_assert}{RESET}")


async def run_case(orch: Orchestrator, case: dict) -> tuple[bool, list[str]]:
    """단일 케이스 실행 + 검증. (통과여부, 실패사유 목록) 반환."""
    fails: list[str] = []
    turns = case.get("turns") or [case.get("utterance", "")]

    # 케이스 독립성: 히스토리 초기화
    orch._history.clear()

    # tool 호출 추적 (마지막 턴 기준)
    called: list[str] = []
    orig_call = orch._call_tool_safe

    async def _traced(name, args):
        called.append(name)
        return await orig_call(name, args)

    orch._call_tool_safe = _traced
    voice = text = ""
    try:
        for i, utt in enumerate(turns):
            if i == len(turns) - 1:
                called.clear()  # 마지막 턴의 tool만 검증
            voice = text = ""
            async for stage, content in orch.run_voice_first(utt):
                if stage == "voice":
                    voice = content
                elif stage == "text":
                    text = content
    except Exception as e:
        fails.append(f"예외: {e}")
        return False, fails
    finally:
        orch._call_tool_safe = orig_call

    answer = f"{voice} {text}"

    # 1) 인텐트
    exp_intent = case.get("expect_intent")
    if exp_intent:
        got = classify_intent(turns[-1])
        if got != exp_intent:
            fails.append(f"intent {got}≠{exp_intent}")

    # 2) tool 호출
    for t in case.get("expect_tools", []):
        if t not in called:
            fails.append(f"tool 미호출:{t} (호출됨:{called or '없음'})")
    for t in case.get("forbid_tools", []):
        if t in called:
            fails.append(f"금지 tool 호출:{t}")

    # 3) 내용 포함/배제
    for s in case.get("must_include", []):
        if s not in answer:
            fails.append(f"누락:'{s}'")
    for s in case.get("must_not_include", []):
        if s in answer:
            fails.append(f"금지어:'{s}'")

    # 4) 빈 응답 규칙
    if case.get("allow_empty"):
        pass
    elif not voice and not text:
        fails.append("voice·text 모두 빔")

    # 5) voice 길이 (하드 상한 초과 = 검증 누락)
    if voice and validate_voice_length(voice) != voice:
        fails.append(f"voice 길이초과({len(voice)}자)")

    return (not fails), fails


async def run_all(cases: list[dict]) -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print(f"{RED}ANTHROPIC_API_KEY 없음{RESET}")
        sys.exit(1)
    with open("config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    orch = Orchestrator(cfg=cfg, anthropic_api_key=api_key)
    await orch.start()

    passed = 0
    fail_cases: list[tuple[str, list[str]]] = []
    try:
        for n, case in enumerate(cases, 1):
            cid = case.get("id", f"#{n}")
            ok, fails = await run_case(orch, case)
            if ok:
                passed += 1
                print(f"{GREEN}✓{RESET} {GREY}{cid}{RESET}")
            else:
                fail_cases.append((cid, fails))
                print(f"{RED}✗ {cid}{RESET} — {YELLOW}{'; '.join(fails)}{RESET}")
    finally:
        await orch.aclose()

    total = len(cases)
    print(f"\n{BOLD}=== 결과: {passed}/{total} 통과 ==={RESET}")
    if fail_cases:
        print(f"{RED}실패 {len(fail_cases)}건:{RESET}")
        for cid, fails in fail_cases:
            print(f"  {RED}{cid}{RESET}: {'; '.join(fails)}")
        sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser(description="Otto 회귀 테스트 러너")
    ap.add_argument("--run", action="store_true", help="실제 LLM 실행(비용 큼). 미지정 시 통계만")
    ap.add_argument("--category", help="카테고리 필터(쉼표 구분)")
    ap.add_argument("--limit", type=int, help="앞 N개만")
    args = ap.parse_args()

    cases = load_cases()
    if args.category:
        cats = {c.strip() for c in args.category.split(",")}
        cases = [c for c in cases if c.get("category") in cats]
    if args.limit:
        cases = cases[: args.limit]

    if not args.run:
        print_stats(cases)
        print(f"\n{GREY}실제 실행: --run (필터: --category, --limit){RESET}")
        return

    print(f"{YELLOW}⚠️  {len(cases)}개 케이스를 실제 LLM으로 실행합니다(비용 발생).{RESET}")
    asyncio.run(run_all(cases))


if __name__ == "__main__":
    main()
