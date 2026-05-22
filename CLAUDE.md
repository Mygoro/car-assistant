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

---

## 현재 상태

- **완료**
  - Phase 0 — Discord 봇 기초 (자동 접속, 재접속 watchdog)
  - Phase 1 — 오디오 수신 및 저장 (DAVE E2E 패치 적용, WAV 디버그 검증)
  - 전시 로드맵 설계 (2026-06-02 전시 + 2026-06-09 문서 제출)
- **진행 중**
  - Phase 2 — Wake Word 게이트 (openwakeword 기반, wake word: "hey otto")
- **다음**
  - Phase 2 품질 검증 통과 후 Phase 3 (STT) 진입

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
7. **세션 종료 시 변경사항을 documentation에 기록한다.** (다큐멘팅 에이전트 설계 후 자동화 예정)

---

## 전시 제약 (2026-06-02)

- 부스: 1인용 테이블 + 노트북, 콘센트 1개
- 시간: 약 6시간
- 시연 방식: 본인 시연 기본, 방문자 직접 호출 확장, 데모 영상 폴백
- 음성 데이터: 저장 없음, 즉시 폐기
- 동의: 안내문 + 구두 안내
- Wake word: "hey otto" (openwakeword 커스텀 모델, 화자 독립)
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
│   └── providers/
├── wake_word/
├── fillers/
├── archive/
│   ├── sessions/
│   ├── daily/
│   ├── artifacts/
│   └── audio/
├── docs/
│   ├── implementation-manual.md
│   └── project-archive.md
└── exhibition/ (설계자 산출물 예정)
    ├── roadmap.md
    ├── booth-plan.md
    └── demo-script.md
```
