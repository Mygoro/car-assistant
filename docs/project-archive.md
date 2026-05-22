# 프로젝트 아카이브
Byunghun Kwon · 2022195171

---

## 프로젝트 1 (메인) — Discord Bot 기반 차량용 Voice AI 어시스턴트

### 현재 상태 요약
- **Phase 0 완료** — Discord 봇 기초, 자동 접속, 재접속 watchdog
- **Phase 1 완료** — 오디오 수신 및 저장 (DAVE E2E 패치, WAV 디버그 검증)
- **Phase 2 완료** — Wake word 게이트 (크랭크 오토, openwakeword, threshold=0.85, CONFIRM_FRAMES=1)
- **Phase 3 완료** — STT 통합 (Silero VAD 8kHz, faster-whisper large-v3, capture_queue 분리, MIN_SPEECH 가드)
- **다음 작업**: **데스크탑 이식 → Phase 4 (LLM)**
- **개발 환경**: CPU-only 노트북 → 데스크탑 이식 대기 중

---

### ⚡ 다음 세션 시작 지점 (2026-05-23 이후)

**Step 1 — 데스크탑 이식** (노트북 → NVIDIA GPU 데스크탑)
```
git clone https://github.com/Mygoro/car-assistant.git
cd car-assistant
uv sync
cp .env.example .env   # 또는 노트북 .env 내용 복사
```
`config.yaml` 두 줄 수정:
```yaml
stt:
  device: "cuda"           # "cpu" → "cuda"
  compute_type: "int8_float16"  # "int8" → "int8_float16"
```
`uv run bot.py` 실행 후 Discord에서 "크랭크 오토" 테스트 → STT 응답 1-2초 이내 확인

**Step 2 — Phase 4 시작**
`docs/implementation-manual.md` Phase 4 섹션 읽고 구현 시작

### 확정된 아키텍처
```
Discord mobile (클라이언트, zero-code)
    ↓ 음성 메시지
Python bot (홈 서버)
    → Porcupine wake word detection
    → faster-whisper STT (VAD silence tail: 4000ms)
    → Claude Sonnet API (MCP tool integration, 응답 길이 무제한)
    → ElevenLabs Flash TTS
    ↓ 오디오
Discord mobile (재생)
```

### 주요 결정 사항
- **클라이언트**: Discord mobile — 네이티브 앱 개발 생략, 데이터/배터리 비용 감수
- **VAD silence tail**: 400ms → 4000ms (자연스러운 발화 포즈 수용)
- **LLM 응답 길이**: 제한 없음 (정확성 우선)
- **장기 메모리**: `memory.md` 파일 → 매 세션 시스템 프롬프트 주입, 주 1회 수동 업데이트

### 날짜별 작업 내역

#### 2026-05-22 — Phase 1 마무리 + Phase 2 wake word 시행착오 및 피벗

**Phase 1 버그 수정**
- WAV 오프셋 버그 발견: 짧은 문장을 여러 번 말하면 "하나" 차례에 무음, "둘" 차례에 "하나" 오디오가 저장되는 현상. silence flush 타이밍 문제였고 `_flush_watcher` 방식으로 수정.
- `_flush_debug_wav` 스레드 안전성 개선: `buf_to_save, self._debug_buf = self._debug_buf, []` 원자적 swap으로 마지막 패킷 누락 방지.
- `cleanup()` 구현: 봇 종료 시 미완성 버퍼 유실 방지.

**Phase 2 구현**
- `core/wake_word.py`: openwakeword 기반 `WakeWordDetector` 구현
- `bot.py`: IDLE/LISTENING 상태 머신, `!record positive/negative/status` Discord 명령어, Phase 2 stub (2초 후 IDLE 복귀)
- `tools/train_wake_word.py`: AudioFeatures 임베딩 + MLP + ONNX 내보내기 커스텀 학습 스크립트
- `tools/generate_tts_samples.py`: ElevenLabs 다화자 TTS positive 샘플 생성 도구
- Discord 텍스트 채널 wake word 감지 알림 (`_notify_wake_word`)

**"hey otto" 학습 시행착오 요약**

| 시도 | 문제 | 조치 |
|------|------|------|
| 녹음 1차 (2초) | 14/15 샘플 skip — openwakeword embedding 모델이 최소 ~2.2초 필요 | 녹음 시간 3초로 증가, 전체 재녹음 |
| 학습 1차 | `np.vstack` shape 불일치 오류 | reshape 후 vstack, X_neg 오버샘플링 경로 추가 |
| 학습 2차 | recall 97.6% / specificity 100% — 과적합 (1개 샘플에서 81 windows) | 원인: 봇 미재시작으로 2초 설정 그대로 녹음됨 |
| 학습 3차 (무음 패딩) | 오탐 심각: 타건음, "헤이", "오토" 등 거의 모든 소리 반응 | 원인: 무음 패딩 → 절반 window가 무음인데 positive 레이블. "무음 = wake word" 학습 |
| 학습 4차 (타일 패딩) | recall 98.3% / specificity 99.2%. 실제 테스트에서 "헤이 맨", "헤이 호" 등 오탐 | 타일 패딩으로 모든 window에 실제 발화 포함 |
| negative 30개 추가 (헤이+계열, 오토+계열) | recall 99.4% / specificity 98.2%. 명확한 오발음 차단. "헤이", "오토", "오토바이" 등 여전히 반응 | threshold 0.75 → 0.85 → 0.90 상향 조정했으나 개선 미미 |

**근본 원인 분석**
- "헤이"와 "오토" 모두 한국어 일상 발화에서 매우 흔한 단어
- MLP가 전체 문장이 아닌 구성 음절 패턴에 반응
- 15개 단일 화자 샘플만으로는 구성 음절과 전체 문장을 구별하는 결정 경계 학습 불가
- negative 추가로 완화되나 근본 해결 불가

**피벗 결정: "크랭크 오토"로 wake word 변경**
- "OTTO" 캐릭터명 및 아이콘 유지
- 시동어를 phonetically 덜 흔한 "크랭크"로 교체
- "크랭크"는 일상 대화에서 거의 사용되지 않아 오탐 가능성 낮음
- 엔진 크랭킹 연상이 차량 AI 어시스턴트 콘셉트와 부합
- 코드 전체(config.yaml, train_wake_word.py, generate_tts_samples.py, bot.py) 일괄 변경 완료
- positive 샘플 전부 삭제, "크랭크 오토" 재녹음 대기 중

#### 2026-05-12
- 전체 아키텍처 설계 및 확정
- 초기 안(Android native + WireGuard)에서 Discord bot 방식으로 피벗
- Claude Code 구현 매뉴얼 (Phase 0–8) 작성
- 메모리 관리 시스템 설계: stateless API의 한계 → `memory.md` 인젝션 패턴 채택

### 세부 진행 내용
> **[인수인계 프롬프트 — Discord Bot Voice AI]**
> 
> ```
> 이 프로젝트는 Discord mobile을 클라이언트로 사용하는 차량용 Voice AI 어시스턴트야.
> 아래는 현재까지의 설계 및 결정 사항이야. 읽고 현재 상태를 파악한 뒤,
> 내가 무엇을 물어보든 이 맥락 위에서 대답해줘.
>
> <architecture>
> Discord mobile → Python bot (홈 서버) → Porcupine (wake word) →
> faster-whisper STT (VAD 4000ms) → Claude Sonnet API (MCP 통합, 응답 무제한) →
> ElevenLabs Flash TTS → Discord mobile (재생)
> </architecture>
>
> <decisions>
> - 클라이언트: Discord mobile (네이티브 앱 개발 없음)
> - VAD silence tail: 4000ms
> - 응답 길이: 무제한 (정확성 우선)
> - 메모리: memory.md 파일 → 시스템 프롬프트 주입, 주 1회 수동 업데이트
> - 개발 환경: CPU-only 노트북 → 추후 NVIDIA GPU 데스크탑 마이그레이션 예정
> </decisions>
>
> <status>
> 현재 상태: 아키텍처 확정, 구현 매뉴얼(Phase 0–8) 작성 완료, 코드 미착수
> 다음 단계: Phase 0부터 실제 구현 시작
> </status>
>
> 현재 상태에서 무엇을 이어서 해야 할지, 또는 특정 Phase를 구현하는 방법을 알려줘.
> ```

---

## 프로젝트 2 (서브) — 강의 녹음 자동화 파이프라인

### 현재 상태 요약
- **Phase 3 완료** (2026-05-13~14) — GitHub Actions 클라우드 마이그레이션 완료
- **Phase 4 진행 중** — 가독성 개선, `dict` 타입 버그 수정 완료, 추가 개선 예정
- **처리 실적**: Notion DB 처리 이력 31개 파일 기준 작동 확인

### 시스템 구조
```
강의 녹음 (수동) → Google Drive 업로드
    ↓ GitHub Actions (자동, 스케줄 또는 수동 트리거)
main.py
    → Whisper API (STT, 청크 분할 지원)
    → Claude Haiku (청크 분류: lecture_core / announcement / qa / smalltalk)
    → Claude Sonnet (토픽 구조 추출 + 요약 생성)
    → Notion 강의 노트 DB 업로드
```

### 비용 (실측, 파일당)
| 항목 | 비용 |
|------|------|
| Whisper (~114분) | ~$0.68 (941원) |
| Haiku (분류) | ~$0.009 (13원) |
| Sonnet (요약) | ~$0.19 (263원) |
| **합계** | **~$0.88 (1,217원)** |

### 날짜별 작업 내역

#### 2026-05-12 (10주차 Lab)
- `/start-project` 커맨드 업그레이드 완료
  - GitHub 접근 확인 (pre-flight) 추가
  - `git init` + `.gitignore` 자동 생성 추가
  - `~/.claude/project-rules.md` 읽기 + `CLAUDE.md` 자동 생성 추가
- `~/.claude/project-rules.md` 작성 및 커스터마이징
- 테스트 완료 — 10단계 플로우 순서대로 동작 확인

#### 2026-05-13~14 (강의 자동화)
- GitHub Actions 마이그레이션 (Phase 3 완료)
  - Windows 작업스케줄러 비활성화
  - `python -u main.py` (unbuffered output) 적용
- 버그 수정
  - `transcript.text` AttributeError: 청크 분할 경로가 dict 반환 → `hasattr` 분기 처리
  - `qa_segments` KeyError: `.get("qa_segments", [])` 폴백 처리
  - `extract_structure()` 빈 리스트 반환 원인 파악용 디버그 로그 추가
- 디버그 로그 추가: 라벨별 청크 수 + 토픽 추출 수 출력
- 첫 클라우드 성공 확인 — RDQM 6주차 파일 정상 처리

### 알려진 이슈
- `lecture_core` 청크가 없는 파일 (잡담·Q&A 위주) → 0/0 토픽 발생. 디버그 로그로 식별 가능, 근본 해결 미완
- 가독성 개선 (Notion 업로드 포맷) — Phase 4에서 예정

### 세부 진행 내용
> **[인수인계 프롬프트 — 강의 녹음 자동화]**
>
> ```
> 이 프로젝트는 강의 녹음 파일을 자동으로 Whisper STT → Claude 요약 →
> Notion 업로드하는 파이프라인이야. GitHub Actions에서 실행돼.
> 아래 상태를 읽고 이어서 도와줘.
>
> <status>
> Phase 3 완료: GitHub Actions 클라우드 마이그레이션 완료
> Phase 4 진행 중: 가독성 개선, 추가 버그 수정
> </status>
>
> <known_bugs>
> - lecture_core 청크가 없는 파일 → 0/0 토픽 (잡담·Q&A 위주 녹음에서 발생)
>   현재: 디버그 로그로 식별만 가능, 근본 해결 미완
> - 이외 주요 버그는 수정 완료 (transcript dict, qa_segments KeyError)
> </known_bugs>
>
> <next>
> - 0/0 토픽 케이스 처리 로직 추가
> - Notion 업로드 포맷 가독성 개선
> - Phase 4 PIPELINE_PLAN.md 업데이트
> </next>
>
> <cost>
> 파일당 평균 약 1,200원 (Whisper 70% / Sonnet 22% / Haiku 1%)
> </cost>
>
> 현재 상태에서 어떤 작업을 이어서 해야 할지, 또는 특정 버그 수정 방법을 알려줘.
> ```

---

## DigiTools 수업 진도

| 주차 | Lab 내용 | 완료 여부 |
|------|----------|-----------|
| 9주차 (4/28) | Skills / Commands / Hooks / Three.js 씬 빌드 | ✅ 완료 |
| 10주차 (5/12) | `/start-project` 업그레이드, `project-rules.md` | ✅ 완료 |

### 9주차 산출물 (4/28)
- `~/.claude/skills/dependency-check/SKILL.md` 생성
- `~/.claude/commands/start-project.md` 생성 (폴더 이름 제안 스텝 추가)
- PostToolUse hook — `.js` 파일 작성 시 `node --check` 자동 실행
- `.claude/commands/add-feature.md` 생성
- Three.js FPS 씬 빌드 + spacebar 점프 기능 추가 테스트

### 10주차 산출물 (5/12)
- `~/.claude/project-rules.md` 생성 및 커스터마이징
- `~/.claude/commands/start-project.md` 업그레이드 (pre-flight + git + CLAUDE.md)
- 10단계 플로우 테스트 통과
