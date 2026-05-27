# car-assistant 전시 로드맵

작성일 2026-05-22 · 대상 마일스톤: 전시 2026-06-02(화), 문서 제출 2026-06-09(화)

이 문서는 전시 데모와 본인 실사용을 동시에 달성하기 위한 마스터 설계 문서다.
짝 문서: `booth-plan.md`(부스·포스터·운영 매뉴얼), `demo-script.md`(시연 대본).

---

## 0. 문서 간 불일치 정정 (필독)

이 로드맵은 아래 3건을 정정해 작성되었다. 기존 문서와 충돌 시 이 문서가 우선한다.

1. **`docs/implementation-manual.md`의 Phase 2(Porcupine)는 폐기.** openwakeword로 대체한다.
   매뉴얼의 `pvporcupine` 코드 예시, `.ppn` 파일, Picovoice Console 학습 절차는 모두 무시한다.
2. **`docs/project-archive.md`는 2026-05-12에서 갱신이 멈췄다.** "구현 미착수"로 적혀 있으나
   실제로는 Phase 0~1 완료(DAVE E2E 패치·라우터 스레드 패치 반영)다. → 5/22 다큐멘팅 자동화로 해결.
3. **매뉴얼 Phase 구조에 차량 연동 단계가 없다.** P0 핵심인 차량 데이터 질의가 자리가 없다.
   → Phase 6.5(차량 데이터)를 신규 삽입한다.

---

## 1. 두 목표와 기능 우선순위

- **목표 1**: 6월 2일 전시에서 일정 수준 이상의 완성도로 시연 가능
- **목표 2**: 전시 후에도 본인 실사용 가능한 시스템 유지

| 우선순위 | 기능 | 전시 시연 방식 |
|---------|------|---------------|
| P0 | Wake word → STT → Claude → TTS 기본 루프 | 라이브 |
| P0 | 차량 데이터 질의(연료/위치/주행거리) | mock 라이브 (Bluelink 실연동은 best-effort) |
| P0 | 스케줄 조회 및 추천(Calendar+Notion) | 라이브 |
| P1 | 차량 브리핑(탑승 직후 자동 요약) | 시간 남으면 |
| P1 | 차내 캠 라이브 송출 | 사전 녹화 주력 + 짧은 라이브 시도 |
| P1 | 방문자 직접 호출 모드 | exhibition 프로파일로 지원 |
| P2 | 음악/유튜브 원격 제어 | 데모 영상으로만 |
| P2 | 위치 기반 주변 검색 | 데모 영상으로만 |

---

## 2. 전시 버전 / 실사용 버전 분리 설계

### 공유 코어 (단일 코드베이스, 단일 git 저장소)

`audio_sink` · `wake_word` · `vad` · `stt` · `orchestrator` · `providers/*` · `tts` · `archive`
· MCP 클라이언트 — 전부 공유한다. 버전 차이는 코드가 아니라 **설정에서만** 발생시킨다.

### 분기 방식 — config 프로파일 + CLI 플래그 (별도 entry point 없음)

`bot.py`는 `--profile` 인자를 읽어 `active_profile`을 덮어쓴다. 기본값 `personal`.
전시 당일은 `uv run bot.py --profile exhibition` 한 줄로 전환된다.

```yaml
# config.yaml 에 추가
active_profile: personal      # --profile 인자로 덮어쓰기 가능

profiles:
  personal:
    wake_word_model: "wake_word/hey_otto.onnx"
    wake_word_sensitivity: 0.5
    memory_file: "memory.md"
    vehicle_backend: "bluelink"
    write_intents_enabled: true          # note.create, calendar.write, memory.update
    history_reset_each_session: false
    response_style: "full"
    audio_archive: false
  exhibition:
    wake_word_model: "wake_word/hey_otto.onnx"   # 폴백 시 사전학습 hey_jarvis
    wake_word_sensitivity: 0.35          # 전시장 소음 → 오탐 방지로 낮춤
    memory_file: "memory.exhibition.md"  # 개인 일정·연락처·메모 제거한 축약본
    vehicle_backend: "mock"
    write_intents_enabled: false         # 방문자가 본인 Notion/Calendar 수정 차단
    history_reset_each_session: true     # 방문자 간 대화 격리
    response_style: "concise"
    audio_archive: false
```

`exhibition` 프로파일을 켜는 것만으로 ① 개인정보 보호 ② 방문자 격리 ③ 오탐 억제가
동시에 달성된다. 시연 직전 점검은 "`--profile exhibition` 확인" 한 줄로 끝난다.

---

## 3. 개발 Phase 재구성

Phase 0~1 완료 상태에서 6/2까지 도달해야 할 Phase. 매뉴얼 Phase 2는 폐기, Phase 6.5는 신규.

| Phase | 산출물 | 완료 기준 | 머신 |
|-------|--------|----------|------|
| 2. Wake Word | openwakeword 통합 (사전학습 → "hey OTTO" 커스텀) | wake word 감지 로그 / 일반 대화엔 미감지 | CPU 노트북 |
| — 데스크탑 이식 — | git clone → uv sync → .env → config cuda 전환 | `uv run bot.py` 정상 기동 | **이 시점 이전** |
| 3. STT | Silero VAD + faster-whisper(cuda) | 발화 → 채팅 채널에 트랜스크립트 게시 | GPU 데스크탑 |
| 4. LLM 텍스트 | providers 추상화 + 인텐트 분류기 | 발화 → 텍스트 응답(마크다운 없음) | 데스크탑 |
| 5. TTS | ElevenLabs 스트리밍 + Discord 음성 송출 | wake→발화→음성 응답 / TTS 중 재트리거 없음 | 데스크탑 |
| 6. MCP 읽기 | Calendar read + Notion read | "내일 일정" → 실제 일정 음성 응답 | 데스크탑 |
| 6.5. 차량 데이터 (신규) | `vehicle` 모듈 — mock + Bluelink 백엔드 | mock: "기름 얼마 남았어"→응답 | 데스크탑 |
| 8. 안정화 (일부) | 에러 핸들링, 봇 무중단, 재접속 watchdog 강화 | 어떤 에러에도 봇 프로세스 미종료 | 데스크탑 |

**데스크탑 이식 시점 = Phase 2 완료 직후.** 근거: ① CPU에서 large-v3 STT 검증은 무의미(매뉴얼 명시)
② 데스크탑이 곧 전시 봇 머신 → 일찍 이식하면 개발=운영=전시 환경이 일치해 이식 리스크가 사라진다.

**전시 P0 최소선 = Phase 2~6.5.** Phase 7(아카이브)은 문서 제출용 JSONL만 최소 구현.
P1/P2는 일정에 편성하지 않음 — 5절 절단 순서대로 시간 남을 때만.

### 3-A. Phase 2 상세 — openwakeword (기능 설계)

매뉴얼의 Porcupine 래퍼를 폐기하고 openwakeword로 교체한다. 봇 메인 루프 인터페이스
(`process` / `pause` / `resume` / `delete`)는 그대로 유지하고 내부 엔진만 교체한다.

- **의존성**: `pyproject.toml`에서 `pvporcupine` 제거, `openwakeword` 추가. `.env`의
  `PICOVOICE_ACCESS_KEY`는 더 이상 불필요(주석 처리).
- **입력 규격**: 16kHz mono int16 PCM. openwakeword는 내부적으로 80ms(1280 샘플) 윈도로 처리.
  기존 audio_sink의 16kHz 변환 출력을 그대로 사용 가능.
- **엔진 API**:
  ```python
  from openwakeword.model import Model
  oww = Model(wakeword_models=["wake_word/hey_otto.onnx"], inference_framework="onnx")
  scores = oww.predict(frame)            # {"hey_otto": 0.0~1.0}
  detected = scores["hey_otto"] > threshold
  ```
- **"hey OTTO" 커스텀 모델 학습**: openwakeword 자동 학습 파이프라인(automatic training notebook)
  사용. Piper TTS로 "hey OTTO" 합성 양성 샘플 수천 개 생성 + 공개 음성 데이터로 음성 샘플 학습 →
  `.onnx` 모델 출력. GPU 데스크탑 또는 Colab에서 약 1시간.
- **폴백**: 커스텀 학습 품질이 미달이면 사전학습 모델 `hey_jarvis`로 즉시 폴백
  (전시는 영어 확정이라 손실 적음). 폴백 결정 게이트 = 5/23 작업 종료 시점.
- **검증**: 매뉴얼 Phase 2 품질 검증 항목 그대로 적용 (감지 로그, 미감지 확인, 6시간 안정성).
  [확인 필요: 봇 이름 표기 "OTTO" 음소 — 영어 합성 시 발음이 의도대로 나오는지 학습 후 청취 확인]

### 3-B. Phase 6.5 상세 — 차량 데이터 (기능 설계)

P0 기능이지만 Bluelink 연동이 미착수다. **mock을 기본 데모 경로로** 설계해
실연동 성공 여부와 무관하게 시연이 보장되게 한다.

- **모듈**: `core/vehicle.py` — `VehicleBackend` Protocol + 두 구현.
  ```python
  class VehicleBackend(Protocol):
      async def get_status(self) -> dict: ...   # {fuel_pct, range_km, location, odometer_km}

  class MockVehicle:      # config에서 값 주입, 데모 결정성 확보
  class BluelinkVehicle:  # 실연동
  ```
- **오케스트레이터 연동**: `get_vehicle_status` 를 Claude 툴로 등록. 인텐트 분류기에
  `vehicle.query` 추가 (키워드: 기름·연료·주유·위치·어디·주행거리·킬로).
- **MockVehicle**: `config.yaml`에서 연료 42%, 주행가능 320km, 위치 "연세대학교 인근",
  누적주행 38,200km 같은 값을 주입. 데모 응답이 매번 동일해 리허설이 가능.
- **BluelinkVehicle**: 한국 현대 Bluelink. 후보 경로 2개 —
  ① Python `hyundai_kia_connect_api`(region=Korea) — Bluelink 앱 계정으로 빠른 통합 가능
  ② Hyundai Developers Portal 공식 API — OAuth·앱 등록 필요, 더 안정적이나 승인 지연 가능.
  [확인 필요: 두 경로 모두 미검증. 어떤 데이터 필드를 실제로 읽을 수 있는지 확인 필요.
   실연동은 best-effort, 실패해도 mock으로 전시·문서 모두 성립]
- **프로파일**: `exhibition`=mock, `personal`=bluelink.

---

## 4. Claude Code 오케스트레이션 + 다큐멘팅 자동화

### 메인 / 서브에이전트

- **메인 에이전트**: Phase별 구현을 직접 수행. CLAUDE.md 작업 원칙(한 번에 하나, 마일스톤 검증) 준수.
- **서브에이전트**:

| 에이전트 | trigger | context | 산출물 |
|---------|---------|---------|--------|
| Explore | Phase 통합 시 기존 코드 위치 파악 | 코드베이스 | 파일·심볼 위치 |
| Plan | 각 Phase 착수 전 | 해당 Phase 절 | 단계별 구현 계획 |
| 다큐멘팅 | 세션 종료/시작 | 세션 diff | `project-archive.md` 갱신 |

활용 스킬: `dependency-check`(uv 패키지), `/add-feature`(Phase 6.5 골격),
`verify`·`/run`(마일스톤을 실제 봇 구동으로 검증 — 단위테스트 금지), `code-review`(Phase 완료 시).

### 다큐멘팅 자동화 — 2단계 hook (권장 설계)

`SessionEnd` hook은 "세션 종료 시" 1회 실행되지만, hook은 셸 명령일 뿐 Claude 프롬프트가
아니다. 종료 시점에 무거운 headless `claude` 호출을 돌리면 시간이 부족할 수 있다. 따라서:

- **SessionEnd hook = 값싼 캡처**: `git diff`를 `archive/pending/<timestamp>.diff`로 저장만. 즉시 끝남.
- **SessionStart hook = 다음 세션 시작 시 처리**: `archive/pending/`에 쌓인 diff를 headless
  `claude -p`로 요약해 `docs/project-archive.md` 날짜별 작업 내역에 append 후 pending 삭제.
  세션 시작 시점은 시간 여유가 있어 안정적이다.

```json
// .claude/settings.json
{
  "hooks": {
    "SessionEnd":   [{ "hooks": [{ "type": "command", "command": "python scripts/capture_session.py" }] }],
    "SessionStart": [{ "hooks": [{ "type": "command", "command": "python scripts/process_pending_docs.py" }] }]
  }
}
```

`update-config` 스킬로 위 설정을 적용. 이 방식은 수동 개입 없이 자동이며, `project-archive.md`
갱신 누락(불일치 #2)을 구조적으로 막는다.

### 6/9 제출 문서

다큐멘팅이 누적한 `project-archive.md` 항목 + 이 `roadmap.md` + 전시 후 회고(리스크 실현 결과)를
종합해 작성. 전시 후 별도 회고를 처음부터 쓸 필요 없음 — 기록이 이미 쌓여 있다.

---

## 5. 리스크 매트릭스

| 리스크 | 영향 | 폴백 |
|--------|------|------|
| 집 데스크탑/인터넷 6시간 무중단 실패 | 전시 전체 중단 | 데모 영상 모드 / (권장) 데스크탑 부스 반입 검토 |
| 강의실 Wi-Fi 불안정 | 봇 도달 불가 | 폰 핫스팟 / 영상 모드 |
| Bluelink 미착수 → 실연동 실패 | P0 차량 데이터 라이브 불가 | mock provider가 기본 경로 — 라이브 영향 없음 |
| 커스텀 wake word 학습 품질 미달 | 오탐/미감지 | 사전학습 hey_jarvis 폴백 (5/23 결정 게이트) |
| 차내 캠 지하 통신 두절 / 디바이스 충전 | P1 라이브 캠 불가 | 사전 녹화 주행 영상 (기본) |
| CPU→GPU 이식 실패 | 개발 중단 | Phase 2 직후 조기 이식으로 버퍼 확보 |
| STT 인식률 낮음(방문자 자유 발화) | 방문자 시연 실패 | 안내 카드 예시 질문 고정 |
| ElevenLabs/Claude API 장애 | 음성 루프 중단 | Phase 8 Ollama 폴백(후순위) / 영상 모드 |

### 시간 초과 시 절단 순서 (위 → 아래로 자름)

1. P2 전체(음악·위치검색) → 데모 영상으로만
2. Phase 7 아카이브 → JSONL 최소만, 일일 요약 생략
3. Phase 8 Ollama 폴백 → 미구현 허용
4. P1 차내 캠 라이브 → 녹화분으로 고정
5. P1 차량 브리핑 → 생략
6. **마지노선. P0 루프(Phase 2~6.5)와 디버깅 버퍼는 절대 자르지 않는다.**

---

## 6. 일자별 작업 분배 (5/22 ~ 6/9)

기준: 평일 최소 2시간, 주말 추가 확보. 디버깅 버퍼 = 5/31·6/1, 부스 준비 = 6/1 통합.

| 날짜 | 요일 | 그날 끝내야 할 것 (명령형) |
|------|------|--------------------------|
| 5/22 | 금 | 다큐멘팅 자동화를 설정하고, openwakeword 사전학습 모델로 wake word 감지 로그를 띄운다. |
| 5/23 | 토 | "hey OTTO" 커스텀 모델을 학습해 감지를 검증하고, 실패 시 사전학습 모델 폴백을 확정한다. |
| 5/24 | 일 | 봇을 GPU 데스크탑으로 이식해 cuda 모드 기동을 확인하고 Phase 3에 착수한다. |
| 5/25 | 월 | VAD 발화 캡처와 faster-whisper STT를 연결해 트랜스크립트를 채팅 채널에 게시한다. |
| 5/26 | 화 | 프로바이더 추상화와 인텐트 분류기를 완성해 텍스트 LLM 응답을 받는다. |
| 5/27 | 수 | ElevenLabs TTS 스트리밍과 Discord 음성 송출을 붙여 P0 음성 루프를 완성한다. |
| 5/28 | 목 | Calendar·Notion 읽기 MCP를 연결해 일정 조회를 검증하고, 데모 영상 P0 루프를 촬영한다. |
| 5/29 | 금 | 차량 mock provider와 exhibition 프로파일을 구현해 차량 데이터 질의를 시연 가능 상태로 만든다. |
| 5/30 | 토 | 에러 핸들링·JSONL 아카이브를 최소 구현하고, 데모 영상 편집·차내 캠 녹화를 완성하며 장비를 구매한다. |
| 5/31 | 일 | exhibition 프로파일로 전체 데모 루프를 반복 검증하고 6시간 안정성을 확인하며 포스터를 완성한다. |
| 6/1 | 월 | 최종 리허설을 마치고 부스 장비·인쇄물·폴백 영상을 모두 준비한다. |
| 6/2 | 화 | 전시 — 봇을 집 데스크탑에서 기동하고 부스 노트북 클라이언트로 6시간 운영한다. |
| 6/3 | 수 | 전시 회고를 작성해 리스크 매트릭스 중 실현된 항목과 대응 결과를 기록한다. |
| 6/4 | 목 | 다큐멘팅이 누적한 archive 기록을 종합해 제출 문서 초안을 작성한다. |
| 6/5 | 금 | 초안에 아키텍처 다이어그램과 Phase별 검증 결과를 채워 넣는다. |
| 6/6~6/7 | 토·일 | 스크린샷·데모 영상 링크를 정리하고 문서를 다듬는다. |
| 6/8 | 월 | 문서를 최종 검토하고 제출 형식을 확인한다. |
| 6/9 | 화 | 문서를 제출한다. |

일정 리스크: Phase 3~5(5/25~27)가 가장 빡빡함. 밀리면 5/30·5/31 버퍼로 흡수하고
6/1(리허설)은 불가침으로 둔다. 장비 구매는 5/30 배치, 6/1 검증.

---

## 7. 미해결 — 확인 필요 목록

- [ ] 봇 이름 "OTTO" 영어 합성 발음 — 커스텀 모델 학습 후 청취 확인
- [ ] Bluelink 실연동 경로(`hyundai_kia_connect_api` vs 공식 포털)와 읽기 가능 데이터 필드
- [ ] 차내 캠 디바이스 — 아이패드 + 보조배터리 조합 확정 또는 라이브 포기·녹화 전용
- [ ] 집 데스크탑 6시간 원격 무인 가동 안정성 — 부스 반입 대안 검토 여부
- [ ] headless `claude -p` 다큐멘팅 스크립트 동작 확인 (5/22)
- [ ] `SessionEnd`/`SessionStart` hook 정상 발화 확인 (5/22)
