# car-assistant

이 프로젝트는 Discord 봇 기반 차량용 음성 AI 어시스턴트다.
2026-06-02 학기말 전시 데모 + 본인 실사용을 동시 목표로 한다.

원문 정의:
> A voice-activated AI assistant that listens through Discord,
> runs on your home server, and responds with speech — hands-free, in your car.

---

## 작업 시작 전 반드시 읽을 것

순서대로 읽고 현재 상태와 Phase 구조를 완전히 파악할 것.
읽지 않고 추측해서 작성/구현하지 말 것.

1. `docs/implementation-manual.md` — 전체 Phase 구조 (Phase 0~8) 및 구현 지침
2. `docs/project-archive.md` — 의사결정 이력과 현재까지의 진행 상태
3. `C:\Users\win10\Second Brain\Documentations(Claude)\daily\` — 가장 최근 날짜의 car-assistant 로그 파일 (미해결 항목, 검증 체크리스트 확인)

---

## 현재 상태

- **완료**
  - Phase 0 — Discord 봇 기초 (자동 접속, 재접속 watchdog)
  - Phase 1 — 오디오 수신 및 저장 (DAVE E2E 패치 적용, WAV 디버그 검증)
  - Phase 2 — Wake Word 게이트 (크랭크 오토, openwakeword, threshold=0.85, CONFIRM_FRAMES=1)
  - Phase 3 — STT 통합 (Silero VAD 8kHz + faster-whisper large-v3, capture_queue 분리, MIN_SPEECH 가드)
  - Phase 4 — LLM 텍스트 응답 (3-tier 인텐트, Orchestrator, dual-response JSON, voice-first 스트리밍)
  - Phase 5 — ElevenLabs TTS 스트리밍 (`_StreamingPCMAudio`), Discord 음성 송출, 세션 모드, 효과음 cue
  - 전시 로드맵 설계 (2026-06-09 전시)
- **완료 (이어서)**
  - 데스크탑 GPU 이식 (2026-06-03, RTX 5070 Ti). `core/cuda_setup.py`로 Blackwell DLL 문제 해결. STT 0.75s.
  - TTS 지연 최적화 (2026-06-03) — ④ optimize_streaming_latency/ffmpeg + ⑥ WebSocket overlap. *코드 보존; bot은 통합 라우터 `run_voice_first`(voice-first) 경로 사용 — voice_response는 짧게 강제돼 토큰 overlap 실이득 작음.*
  - E2E 타임로그 Discord 출력 + 슬립 오토 종료 키워드 제거 (2026-06-05). warm 발화끝→첫소리 **~3.4s** 실측, docs 목표(5~6s) 충족.
- **진행 중**
  - Phase 6 — MCP/native 툴 통합 (2026-06-02): **코드 작성 완료, 런타임 연결 미검증**
    - Orchestrator tool-use 루프 (ToolHandle 레지스트리, AsyncExitStack 기반 MCP 생명주기)
    - Notion stdio MCP + native 툴 3종 (Calendar 실구현 / Hyundai Bluelink stub / KakaoMap)
- **다음 (세션 시작 시)**
  1. **Phase 6 런타임 검증** — `uv sync` → `.env`에 `NOTION_API_KEY`/`KAKAO_REST_API_KEY` 등록 → `uv run tools/chat_test.py` → `!tools` 확인 → Calendar OAuth 실행 → "내일 일정 뭐야?" / "기름 얼마 남았어?" 테스트 (`docs/project-archive.md` 다음 세션 시작 지점 체크리스트 참조)

---

## 환경

- **개발**: 노트북 (CPU only) — 현재 작업 중
- **운영**: 데스크탑 (NVIDIA GPU) — 추후 이식
  - 이식 시 `config.yaml`에서 `device: "cpu"` → `"cuda"`, `compute_type: "int8"` → `"int8_float16"`로 변경
- 패키지: `uv` 사용
- 저장소: GitHub `Mygoro/car-assistant` (private)

---

## 작업 원칙

1. **마일스톤 검증 전 다음 단계 진행 금지.** 각 Phase의 품질 검증 항목을 통과해야 다음 Phase로 넘어간다.
2. **한 번에 하나만 변경.** 문제 발생 시 원인 추적을 위해 변경을 작게 유지한다.
3. **오디오 파이프라인을 절대 블로킹하지 않는다.** 파일 I/O, 네트워크, 무거운 연산은 `asyncio.create_task` 또는 `run_in_executor`로 감싼다.
4. **에러를 삼키지 않는다.** `except Exception: pass` 금지. 항상 로깅하고 사용자가 알아야 할 것은 알린다.
5. **모델 인스턴스는 봇 시작 시 한 번만 생성한다.** 매 호출마다 재로드 금지.
6. **민감 값은 `.env`에만 저장.** 코드에 하드코딩 금지.
7. **세션 종료 또는 `/log` 시 두 문서를 반드시 갱신한다.**
   - `docs/project-archive.md` — 날짜별 작업 내역, 결정 사항, 다음 시작 지점
   - `docs/implementation-manual.md` — 완료된 Phase 섹션을 실제 구현에 맞게 수정 (설계와 달라진 부분 반드시 반영)
8. **테스트 시 반드시 `otto_events.log`를 확인한다.** 콘솔 스팸 때문에 중요한 이벤트가 묻히므로, 문제 진단 시 로그 파일을 먼저 읽고 판단한다. 새 터미널에서 열려도 이 습관을 유지할 것.

---

## 전시 제약 (2026-06-02)

- 부스: 1인용 테이블 + 노트북, 콘센트 1개
- 시간: 약 6시간
- 시연 방식: 본인 시연 기본, 방문자 직접 호출 확장, 데모 영상 폴백
- 음성 데이터: 저장 없음, 즉시 폐기
- 동의: 안내문 + 구두 안내
- Wake word: "크랭크 오토" (openwakeword 커스텀 모델, 화자 독립)
- 차량: 지하 주차, 차내 캠 송출 가능

---

## 기능 우선순위

- **P0 (반드시)**: Wake word → STT → Claude → TTS 루프 / 차량 데이터 질의 / 스케줄 조회 및 추천
- **P1 (가능하면)**: 차량 브리핑, 차내 캠 라이브, 방문자 호출 모드
- **P2 (시간 남으면)**: 음악/유튜브 원격 제어, 위치 기반 주변 검색

---

## 작업 폴더 구조

```
car-assistant/
├── CLAUDE.md                    ← 이 파일
├── bot.py
├── config.yaml
├── pyproject.toml
├── .env (gitignored)
├── core/
│   ├── audio_sink.py
│   ├── wake_word.py
│   ├── vad.py
│   ├── stt.py
│   ├── orchestrator.py
│   ├── tts.py
│   ├── memory.md
│   ├── system_prompt_template.txt
│   └── providers/
├── wake_word/
│   └── crank_otto.onnx
├── cues/
│   ├── otto_enter.mp3
│   └── otto_quit.mp3
├── fillers/
├── tools/
│   ├── chat_test.py
│   ├── train_wake_word.py
│   └── generate_tts_samples.py
├── docs/
│   ├── implementation-manual.md
│   ├── project-archive.md
│   ├── hyundai-api-survey.md
│   └── map-api-survey.md
└── exhibition/
    ├── roadmap.md
    ├── booth-plan.md
    └── demo-script.md
```
