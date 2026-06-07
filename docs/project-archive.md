# 프로젝트 아카이브
Byunghun Kwon · 2022195171

---

## 프로젝트 1 (메인) — Discord Bot 기반 차량용 Voice AI 어시스턴트

### 현재 상태 요약
- **Phase 0 완료** — Discord 봇 기초, 자동 접속, 재접속 watchdog
- **Phase 1 완료** — 오디오 수신 및 저장 (DAVE E2E 패치, WAV 디버그 검증)
- **Phase 2 완료** — Wake word 게이트 (크랭크 오토, openwakeword, threshold=0.85, CONFIRM_FRAMES=1)
- **Phase 3 완료** — STT 통합 (Silero VAD 8kHz, faster-whisper large-v3, capture_queue 분리, MIN_SPEECH 가드)
- **Phase 4 완료** — LLM 텍스트 응답 파이프라인 (providers 추상화, Orchestrator, dual-response JSON)
- **Phase 5 완료** — ElevenLabs TTS + Discord 음성 송출, 세션 모드, 효과음, voice-first 스트리밍
- **GPU 이식 완료** (2026-06-03) — 데스크탑 RTX 5070 Ti. STT 11~13s → **0.75s** 실측. E2E 1턴 GPU 검증 통과.
- **TTS 지연 최적화 완료** (2026-06-03) — optimize_streaming_latency + ffmpeg 버퍼 off + WebSocket overlap (코드 보존; bot은 voice-first 경로 사용)
- **E2E 타임로그 + 슬립오토 제거 완료** (2026-06-05) — 타임로그 Discord 출력, 세션은 무응답 타임아웃으로만 종료(슬립오토 버그 동시 해소). warm 발화끝→첫소리 **~3.4s** 실측, 목표 충족.
- **분기 통합 완료** (2026-06-05) — `feat/tts-latency-ws-overlap`(GPU+TTS)와 `master`(Phase 6)가 `1270302`에서 분기돼 있던 것을 master로 통합. **이후 master에서 작업.**
- **Phase 6 완료** (2026-06-06) — Notion·Calendar·Hyundai·KakaoMap + web_search(Brave) + Google Places(get_place_details). E2E 라우팅 검증 통과.
- **Phase 7/8 신규 정의** (2026-06-06) — 7: 컨텍스트 오케스트레이션 & 페르소나 / 8: 품질 하드닝. 구 7(아카이브)·8(폴백)은 부록으로 이동.
- **Phase 7 완료** (2026-06-07) — ① memory.md 베이스+프로파일 게이팅, ② 소스 라우팅,
  ③ 맥락 통합(근거가드+멀티소스 few-shot). 실대화 로그로 검증(프로필 반영·소스 일관·복합질의 순서·
  carry-over). 사적·데이트 맥락은 전면 제거(전시용·사용자 요청). ③ 문구레벨 빡센 검증은 Phase 8로 이월.
- **tool 경로 지연 최적화** (2026-06-07) — 티어1(출력 축약)+티어2(최종 turn 스트리밍). 긴 답변 첫소리 ~45~52%↓.
  크래시 2종 수정(parsed_output 400, 캘린더 동시쓰기 SSL). 미해결: 캘린더 read 비대→truncation 재조회.
- **다음 작업**: 캘린더 출력 슬림화(아래 시작 지점). 이후 Phase 8 품질 하드닝.
- **개발 환경**: 데스크탑(NVIDIA RTX 5070 Ti) 이식 완료. 노트북은 CPU-only 개발용
- **전시 일정**: **2026-06-09 전시** (D-2)

---

### ⚡ 다음 세션 시작 지점 (2026-06-07 이후)

**1) 캘린더 출력 슬림화 (지연 절감 마무리 — 진단 완료, 미구현)**
- 증상: "올해 일정" 류가 `get_calendar_events`를 2회 호출(3 iteration). 원인은 프롬프트가 아니라
  **결과 비대→truncation**. 한 줄이 `[이메일::60자 event_id] 날짜: 제목`이라 id·이메일이 줄의 ~75%.
  1년치가 `max_result_chars=6000`을 넘겨 잘림 → 모델이 뒷 범위를 재조회.
- 권장(C): `core/native_tools/calendar.py` read 줄 슬림화(`[cid::id]`→`[id]`, 반복 이메일 제거) +
  캘린더 결과는 truncation 예외(캘린더는 maxResults=20/캘린더로 상한 있음, 노션 강의 본문과 다름).
  목표: 1년치 1회·미절단 → 그 류 질의 3→2 iteration.
- 부수: 맥락 재사용 프롬프트는 모델이 잘 안 따름(매 턴 재조회) — 슬림화로 결과가 온전해지면 개선 기대.

**2) 이후 Phase 8 품질 하드닝** — grounding 관측 로그(`[GROUND]`)·회귀 묶음(238케이스) 이미 일부 반영.
상세: `docs/implementation-manual.md` Phase 8 / 보류 항목.

---

### 2026-06-07 작업 로그 (Phase 7③ + 사적맥락 제거 + tool 지연 최적화 + 크래시 2종)

**Phase 7① memory.md + 게이팅 / ③ 맥락 통합**
- memory.md 비민감 베이스 + `core/memory.local.md`(gitignore) 민감 오버레이 분리. `_load_memory`가
  `OTTO_PROFILE=exhibition`이면 오버레이 미로드 + `[개인전용]` 줄 제거(안전망). `bot.py --profile` 추가
  (문서엔 있었으나 코드에 파싱이 없어 fail-open이던 구멍 차단). 시작 배너로 프로파일 육안 확인.
- ③ 맥락 통합: system_prompt에 "추천 이유 근거 가드"(분위기 등 주관 주장은 툴 결과가 뒷받침할 때만) +
  멀티소스 few-shot 추가.
- **사적·데이트 맥락 전면 제거**(사용자 강한 요청 — 전시용, 데이트 추천 불필요): memory.md 여자친구 줄,
  local 오버레이, orphan(`memory_exhibition.md`/`strip_personal.py`), update_prompt·manual의 예시까지.
  선호를 프로젝트 메모리에 기록([[no-personal-context-in-assistant]]).

**tool 경로 지연 최적화 (지연의 82~94%가 최종답 LLM 토큰 생성, r≈0.82)**
- 티어1: `get_place_details` 7일 영업시간 테이블→오늘 1줄+평점. text_response 간결화 프롬프트.
- 티어2: `anthropic.stream_tools` + `_tool_voice_streaming` — 최종 turn에서 voice_response가 닫히는
  즉시 발화(긴 text와 병렬). `tool_use.stream_final` 토글 + 예외 시 complete 폴백. bot/TTS 무변경.
  **실측: 긴 답변 첫소리 ~45~52%↓**(18.4s→8.8s, 30.9s→17.0s), 단일 iteration 2.2s.

**크래시 2종 (티어2 도입 중 발생, 둘 다 수정)**
- parsed_output 400: `messages.stream().get_final_message()`가 text 블록에 붙이는 `parsed_output`을
  model_dump로 재전송 → 거부. `_serialize_assistant_blocks`로 허용 필드만 직렬화.
- 캘린더 동시쓰기 SSL 크래시: 티어1에서 넣은 `asyncio.gather`가 calendar.py의 전역 싱글톤 `_service`
  (공유 SSL 소켓)를 두 스레드에서 동시 호출 → `RECORD_LAYER_FAILURE` → C레벨 하드 크래시(try/except로도
  못 잡음). **다중 tool_use 순차 실행으로 복원**(병렬 이득 ~1s, 크래시 유발이라 버림).

**프롬프트 round-trip 최소화 (부분 성공)** — 범위 분할·재조회·과다 details 억제 지시. "올해 일정"이
4→3 iteration으로 줆. **남은 병목은 프롬프트가 아니라 캘린더 출력 비대→truncation 재조회**(다음 시작 지점).

**인사이트**: ① 음성 지연의 본질은 "최종 답 길이"라 스트리밍(짧은 voice 선발화)이 가장 효과적, 단 tool
iteration 왕복은 못 줄임. ② 동시성 최적화(gather)는 공유·비동시성-안전 클라이언트(Google/MCP)에선 크래시
유발 — 순차가 답. ③ 프롬프트 유도엔 한계가 있고, 구조적 비대(거대 event_id)는 코드로 잘라야 한다.

커밋: `4d03e86`(③+사적제거) · `7883f2f`(티어1) · `9dbff78`(티어2) · `ca5decf`(parsed_output) ·
`9388a38`(순차복원) · `ac7101c`(round-trip) + 사용자 작업(`full` 길이컷·`[GROUND]`·회귀묶음 등).

---

### 2026-06-06 작업 로그 (E2E 피드백 7건 + 에이닷 인사이트 + 로깅 개편)

E2E에서 나온 7개 피드백을 인과별로 처리. 핵심은 "기능은 되는데 맥락·품질이 부족"이었고, 그중 소스의 구조적 한계에서 온 것을 갈라냈다.

- **차량 조회 실패 = 토큰 누적 버그**: 2시간마다 자동 갱신하는데 갱신 응답의 새 refresh 토큰을 저장 안 해, 한 번 실패하면 낡은 토큰으로 계속 재시도→500. 새 토큰도 저장하도록 수정(`vehicle.py`). 재인증 없이 자동 갱신.
- **음성 주소 억제**: 전체 도로명을 TTS가 읽어봐야 운전 중 무용 → voice는 장소명+동/역+거리만, 전체 주소는 텍스트에만(프롬프트).
- **미래 교통 예측**: 카카오내비 `future/directions` 발견 → `get_directions`에 `departure_time` 분기. "내일 9시 출발 기준" 답변 가능.
- **장소 상세(영업시간·평점·리뷰) — 소스 교체 결정**: 카카오는 미제공. Brave 웹검색으로 때우려 했으나 스니펫만 줘 부정확하고, 부실한 결과에 모델이 한 질문에 9번 재검색해 무료한도를 갉음. → **Google Places API(`get_place_details`) 채택**, Brave는 일반정보 보조로 격하 + 재검색 1~2회 제한 + 결과 정제. 상세 결정: [[car-assistant-003-place-data-source-google-places]].
- **에이닷 개발기 반영**: STT 고유명사 보정 + 환각 방지를 프롬프트에 위임(별도 모듈 대신 Claude에). 추론모델(Opus) 라우팅은 음성 지연 이유로 **Sonnet 통일**.
- **음성 숫자 깨짐**: TTS가 "17.5km"를 못 읽음(`latency=3` 정규화 생략) → voice에서 숫자·단위를 답변 언어로 풀어쓰기("십칠 점 오 킬로미터").
- **로깅 시스템 개편**: daily/decision/report 에이전트의 경로가 옛 머신(win10)으로 깨져 report가 늘 빈손이었음 → 경로 수정. daily 템플릿을 changelog식 → **인과·인사이트 서사**로 전환(에이닷 스타일). `Claude Base/.claude/agents/`.

**인사이트**: ① 구조화된 로컬 데이터는 검색이 아니라 전용 API로. ② 음성 UX에서 모델 재시도 폭주 = 비용·지연, 품질 높이거나 "못 찾음"으로 멈추게. ③ 상용팀(에이닷)과 독립적으로 같은 설계결론 — 전시 발표 프레이밍.

커밋: `bc67f7c`(토큰+라우팅) · `8842dbf`(에이닷 프롬프트) · `a70c3bc`(주소·미래교통·Brave) · `3e4c490`(검색 정제) · `65d1734`(Places).

---

### 2026-06-05 작업 로그 (KakaoMap)

- **카카오 콘솔 설정 발견**: 기존 kakao 툴들은 **[카카오맵] 사용설정이 OFF라 한 번도 동작 안 했음**(403 Forbidden). 2024-12 이후 신규 앱은 카카오맵 사용설정 필수 — 켜서 해결.
- **`search_nearby_places` 좌표 선택화**: `keyword.json`은 좌표가 optional이고 질의어에서 지역명을 직접 파싱(`same_name.region`). lon/lat 없으면 `query="강남역 주유소"`만으로 동작. orchestrator 스키마 `required`를 `["query"]`로 축소. → **GPS 없이도 검색 가능, 전시 데모 충분.**
- **`get_directions` 신규**: 카카오모빌리티 길찾기(`apis-navi.kakaomobility.com/v1/directions`). 지명 문자열 → 내부 `_geocode`(keyword 첫 결과) → 경로 탐색을 단일 native 함수로 체이닝(음성 지연 방지). `summary=true`로 vertexes 폭주 차단. 출력: "강남역→잠실역: 약 16분, 6.7km, 통행료 0원". 실호출 검증 통과.
- **키 구조**: 길찾기는 원래 developers.kakaomobility.com 별도 키(`KAKAOMOBILITY_REST_API_KEY`)가 필요하다는 게 공식 입장이나, **실측상 기존 `KAKAO_REST_API_KEY`로 통과**. 코드는 별도 키 우선 + 기존 키 폴백 구조라 어느 쪽이든 동작.
- **GPS 가용성 확정**: 현대차 공식 API 엔드포인트 전수 확인 → 위치/GPS 0개(DTE/odometer/EV/경고등 7종뿐). 카카오 API도 좌표는 입력 전용(위치 측정 불가). live GPS는 폰 능동 전송(브라우저 geolocation 등) 필요 → Phase 7로 보류. **전시장은 고정 위치라 애초에 불필요.**
- 보류: `get_region`·`address_to_coord`·카테고리 검색·세션 위치 툴 — GPS 또는 데모 보강 시점에 재검토.

---

### 2026-06-05 작업 로그 (Hyundai)

- `tools/hyundai_auth.py` 구현 — OAuth 4단계 자동화 (로그인→auth code→token→carlist), localhost:8080 임시 서버로 redirect 캐치
- 포털 설정: 계정 API / 데이터 API Redirect URL 등록, CLIENT_ID/SECRET .env 등록
- 개인정보 동의: 포털 차량 활성화 시점에 이미 완료 상태 → step3 자동 통과
- `core/native_tools/vehicle.py` 실구현 — 공식 Developers API (DTE + Odometer), token 자동 갱신
- **미제공 데이터 조사**: 연료 잔량 % / GPS 위치 — 공식 API 미지원, 한국 계정용 Python 비공식 라이브러리 없음 (hyundai-kia-connect-api v4.x 한국 미지원 확인)

---

### 이전 시작 지점 (2026-06-05 오전) — 처리됨

**Notion + Calendar 연결 완료 (2026-06-05)**

- Notion: API key 연결, 화이트리스트 5개 툴, 소스 라우팅(빠른메모/강의노트 DB ID 고정)
- Rate limit(429) 대응: 툴 22→5 화이트리스트(B), 결과 6000자 캡(C), 히스토리 10→6턴(D)
- parse_dual_response 폴백 버그 수정 (raw JSON → TTS 낭독 사고 방지)
- Calendar: Google Calendar API 활성화, OAuth read+write 스코프로 연결
  - create / update / delete / get 4종 모두 구현, event_id 반환으로 수정·삭제 연결
  - end_date == start_date 공집합 버그 수정
- 시스템 프롬프트: 현재 날짜 주입, 날짜 자연어 읽기 규칙, voice 청크 분할

---

### 이전 시작 지점 (2026-05-28 이후) — 처리됨

**GPU 이식 — 완료 (2026-06-03, 데스크탑 RTX 5070 Ti)**
`git clone` → `uv sync` → `env`→`.env` → `config.yaml`(cuda/int8_float16) → `uv run bot.py`.
이식 중 Blackwell(sm_120) DLL 문제 해결(아래 2026-06-03 항목 참조). STT warm **0.75s** 실측.
신규 기기 셋업 시 자동 조달되는 자산: `silero_vad.onnx`(vad.py 자동 다운로드),
openwakeword base 모델(`openwakeword.utils.download_models()` 1회 필요).

**Phase 4+5 E2E 검증 — GPU 1턴 통과 (2026-06-03)**
- Phase 4: Wake word → 발화 → Discord 채팅 채널 LLM 응답 게시 (마크다운 없음, 히스토리 동작)
- Phase 5: Wake word → 발화 → Discord 음성 채널 TTS 응답 (에코 방지, 세션 모드, cue 동작)
- E2E 검증 통과 후 Phase 6 진입.

**Phase 4+5 E2E 검증 — 완료 (2026-05-27 21:46~22:14)**
- "크랭크 오토" wake word 감지 성공 (score 0.887~1.000)
- LLM 응답 + Discord 텍스트 채널 게시 확인
- 세션 모드: wake → 연속 대화 → "슬립 오토" → IDLE 복귀 확인
- 에코 방지 동작 확인
- 실측 발화 끝→봇 발화 시작: 26s (CPU 기준, GPU 이식 후 5~6s 목표)

**다음 작업: Phase 6**
`docs/implementation-manual.md` Phase 6 섹션 참고.
우선순위: Calendar read → Notion read → Phase 6.5 mock vehicle provider.
MCP 클라이언트 인프라: `mcp` 패키지 추가 필요 (`uv add mcp`). Calendar/Notion MCP 서버 설치 필요.

### 확정된 아키텍처 (Phase 5 완료 기준)
```
Discord mobile (클라이언트, zero-code)
    ↓ 음성 메시지 (Krisp 노이즈 억제)
Python bot (홈 서버)
    → openwakeword "크랭크 오토" (threshold=0.85)
    → [CUE_ENTER MP3 재생]
    → Silero VAD (8kHz) + faster-whisper large-v3
    → Orchestrator (3-tier 인텐트 분류, 10턴 히스토리)
    → Claude Sonnet 4.6 (dual-response JSON, 시스템 프롬프트 캐싱)
    → ElevenLabs Flash v2.5 TTS (voice-first 스트리밍)
    ↓ 오디오 (ffmpeg → Opus)
Discord mobile (재생)
    + Discord 채팅 채널 (text_response 게시)
```

세션 모드: wake word 1회 → 연속 대화 → "슬립 오토" 또는 무응답 3초로 종료.

### 주요 결정 사항
- **클라이언트**: Discord mobile — 네이티브 앱 개발 생략, 데이터/배터리 비용 감수
- **VAD silence tail**: `tail_ms: 1500` (1.5s — 3000에서 단축. 첫 턴 1.5s, 이후 턴 3.0s 동적)
- **LLM 응답**: dual-response JSON (voice_response=짧음/TTS용, text_response=상세/채팅용)
- **장기 메모리**: `core/memory.md` 파일 → 매 세션 시스템 프롬프트 주입, 주 1회 수동 업데이트
- **인텐트 라우팅**: 3-tier (trivial→Haiku, default→Sonnet, complex_reasoning→Opus)
- **wake word**: "크랭크 오토" (openwakeword 커스텀, "hey otto" 오탐 문제로 피벗)

### 날짜별 작업 내역

#### 2026-06-05 (오후) — Phase 6 런타임 검증(Notion) + LLM 견고성/rate limit 대응

**Phase 6 런타임 검증 — Notion MCP 연결 성공 (실서비스 첫 외부 연결)**
- 셋업 이슈 해소: openwakeword 기본 모델(`melspectrogram.onnx`) 미다운로드로 `run.bat` 크래시
  → `openwakeword.utils.download_models()` 1회 실행으로 해결. 신규 기기 셋업 항목과 동일.
- **봇 다중 인스턴스 사고**: 진단 중 띄운 봇들이 종료 안 돼 4개 동시 실행 → 같은 음성 채널
  수신 분할로 STT 빈 transcript, GPU 경합으로 STT 0.75s→15s, CUE 2회 재생. 전부 종료로 해소.
  교훈: 봇 재시작 전 항상 이전 python 프로세스 종료 확인.
- **Notion 401 원인**: `.env`에 `NOTION_API_KEY` 미저장(IDE 저장 누락). 키가 비면
  `config.yaml`의 `${NOTION_API_KEY}`가 글자 그대로 MCP에 전달돼 invalid token. 저장 후 해결.
  통합 "OTTO"가 워크스페이스 100+ 객체 접근 확인.

**강의노트 "3월 8일 버전만 읽힘" — 중복 DB 문제 (코드 버그 아님)**
- 원인: 워크스페이스에 강의 DB가 둘. 살아있는 **"강의 노트"**(ds `33700100…`, `[과목] N주차` 형식)와
  3월 8일에 멈춘 빈 껍데기 **"수업 노트 정리"**(ds `ee6550a9…`). 풀텍스트 검색이 옛 빈 항목을 집어옴.
- 조치: 사용자가 구 DB 폐기. 시스템 프롬프트(`system_prompt_template.txt`)에 **Notion source routing**
  추가 — 개인 메모→"빠른 메모"(`18d0ae87…`), 강의→"강의 노트"(`33700100…`)를 `API-query-data-source`로
  직접 조회. 두 ds id는 메모리에도 기록([[otto-notion-data-sources]]).

**TTS가 "voice response" 낭독 + 폭주 — parse 폴백 버그**
- 원인: 강의 본문이 길어 최종 JSON 파싱 실패 → `parse_dual_response` 폴백이 `raw[:100]`(=`{"voice_response":…`)을
  그대로 TTS로 넘김. 100자 한국어 ≈ 12~25s라 "너무 길고", 필드명 낭독되고, 100자에서 잘림.
- 조치: ① 폴백을 `_decode_partial`로 voice 값만 구제→실패 시 안전 멘트(raw JSON 절대 미낭독),
  ② `validate_voice_length`가 130자 초과 시 실제 절단, ③ 프롬프트에 "강의 본문 통째 낭독 금지,
  voice는 2문장 이내 요약" 명시.

**rate limit 429 (30,000 ITPM) — 판단 및 대응 결정**
- 원인: 현재 **Tier 1 / Sonnet 4.x = 30,000 input tokens/분**. 연속 강의 질의 2턴에서 ① 툴 스키마
  26개(Notion 22 verbose) ② 강의 본문 tool_result(100블록)가 tool-use 루프마다 누적 재전송
  ③ 10턴 히스토리가 1분 안에 3만 토큰 초과.
- 확인 사실(공식 문서): **Sonnet 4.x는 `cache_read_input_tokens`가 ITPM에 카운트 안 됨**(†는 Haiku 3.5뿐).
  cache write·uncached input만 카운트. 현 프로바이더는 system에 cache_control → 렌더순 tools→system이라
  **툴+시스템은 함께 캐시됨**. 비용나는 곳은 **uncached messages(강의 본문·히스토리)**.
- **결정: 유료 티어 상향($40→Tier2, 450k ITPM) 대신 토큰 다이어트로 대응** (사용자 지시):
  - **B. Notion 툴 화이트리스트** 22→5 (`API-post-search`, `API-query-data-source`,
    `API-retrieve-a-data-source`, `API-get-block-children`, `API-retrieve-a-page`). config `allowed_tools`로 제어.
  - **C. tool_result 길이 캡** (`tool_use.max_result_chars`, 기본 6000자). 강의 100블록 폭주 차단.
  - **D. `history_turns` 10→6** — uncached 히스토리 꼬리 축소.
  - 선행: **요청별 [USAGE] 로깅**(provider) + orchestrator/provider 로그를 `otto_events.log`에 연결.
    cache_r이 0이면 캐시 미스, in이 크면 ITPM 위험 — 사후 진단 가능하게.

#### 2026-06-05 — E2E 타임로그 + 슬립오토 제거 + 분기 통합 (master로 일원화)

**E2E 타임로그 Discord 출력 (커밋 11f1667)**
- `bot.py` `TimingLog` 누적기: 턴별 타이밍을 기존처럼 `[TIMING]`으로 콘솔/`otto_events.log`에
  남기면서(원칙 8 유지), 턴 종료 시 Discord 채팅에 통합 코드블록으로 1회 게시(도배 방지).
  캡처/STT는 `_capture_and_transcribe`, LLM/TTS는 `_run_llm`에서 기록.

**슬립 오토 종료 키워드 제거 (커밋 11f1667)**
- `_SESSION_CLOSE_KEYWORDS`(슬립 오토/그만/종료해 등)와 체크 블록 삭제. 세션은 **무응답
  타임아웃으로만 종료**. 사용자 피드백: "잠깐 대답 안 하면 바로 끊겨서 종료어 필요 없음."
- 부수효과: 미해결로 남아있던 **"종료 키워드가 LLM 스킵 못 해 한 마디 응답 후 종료" 버그 동시 해소.**

**warm 발화끝→첫소리 재측정 — 기준 충족 (테스트 완료)**
- GPU warm 연속 5턴(`otto_events.log` 2026-06-05 15:42~15:43): 발화끝(STT시작)→첫 소리
  = STT + LLM 첫 voice 토큰 + TTS 첫음절.
- 첫 턴 ~5.3s, **warm 연속 턴 평균 ~3.4s** (2.98~3.97s). docs 목표(5~6s) **충족.**
- 병목은 **LLM 첫 토큰 ~1.9s**(전체의 ~55%). STT(~0.6s)·TTS 첫음절(~0.35s)은 이미 최적.

**분기 통합 — master로 일원화 (커밋 진행 중)**
- 상황: 노트북이 `master`에서 Phase 6(1fa927a)을 작업·push, 데스크탑은 `feat/tts-latency-ws-overlap`에서
  GPU+TTS 작업. 두 갈래가 `1270302`에서 분기돼 서로의 작업을 갖지 않음.
- 결정: **master로 통합, 이후 master에서 작업.** `feat`를 master에 머지.
- 충돌 해소: `bot.py`는 Phase 6의 통합 라우터 `run_voice_first`(voice-first + tool/filler) 채택 —
  voice_response가 짧게 강제돼 토큰 overlap 실이득이 작으므로 스트리밍 경로(`run_voice_streaming`/
  `speak_streaming`)는 **코드로 보존하되 bot은 미사용**. `pyproject.toml`은 양쪽 의존성 union.
  `.gitignore`는 Phase 6의 인코딩 수정본 채택(+`/env`).

상세 내역: `Documentations(Claude)/daily/2026-06-05-car-assistant.md`

---

#### 2026-06-03 — GPU 데스크탑 이식 + TTS 지연 최적화 (④ 플래그 + ⑥ WS overlap)

**GPU 이식 (커밋 3af7eee)**

데스크탑 RTX 5070 Ti(Blackwell, sm_120)로 이식. clone + `uv sync` + config cuda 전환은
사용자가 선행. 남은 블로커를 해결:

| 문제 | 원인 | 해결 |
|------|------|------|
| `cublas64_12.dll not found`로 STT 추론 실패 | Windows에 CUDA 런타임 DLL이 PATH에 없음 | `nvidia-cublas-cu12 / cudnn-cu12 / cuda-runtime-cu12`(12.9, Blackwell 지원) pip 추가 |
| add_dll_directory만으론 "cannot be loaded" | cublas가 의존하는 cudart64_12.dll 부재 | cuda-runtime 패키지 추가 + PATH/add_dll_directory 등록을 `core/cuda_setup.py`로 모듈화 |
| 첫 추론 23s | sm_120 PTX JIT 컴파일(1회성) | CUDA ComputeCache에 캐시됨 → warm 0.31~0.75s |

- `core/cuda_setup.py`: nvidia 네임스페이스 패키지(`__path__`)의 cublas/cudnn/runtime/nvrtc
  bin을 PATH + `os.add_dll_directory`에 등록. `stt.py`가 `faster_whisper` import 전 호출.
  Windows 아니거나 미설치 시 no-op(노트북 CPU·Linux 안전).
- 신규 기기 자산: `silero_vad.onnx`(vad.py가 GitHub에서 자동 다운로드, 8kHz 모델),
  openwakeword base 모델(melspectrogram/embedding — `download_models()` 1회).
- **실측**: STT warm 0.75s (CPU 11~13s 대비 ~15배). E2E 1턴 GPU 검증 통과(otto_events.log):
  캡처 3.8s → STT 0.75s → LLM voice 2.82s → TTS 첫음절 1.11s → 발화끝→첫소리 ~5.2s
  (CPU ~26s 대비). docs 목표(STT 1~2s / 첫소리 5~6s) 달성.

**TTS 지연 최적화 (커밋 05faf6a)** — 모델 품질 불변(Sonnet 유지: Phase 6 tool-use 신뢰성).

- ④ `optimize_streaming_latency=3` + ffmpeg `-f mp3`(probe 생략)·`-analyzeduration 0`·
  `-fflags nobuffer`. 라이브 실측 첫 MP3 청크 0.41s. `speak()`의 ffmpeg 브릿지를
  `_play_mp3_stream` 헬퍼로 추출(HTTP/WS 공용).
- ⑥ WebSocket overlap: `ElevenLabsTTS.stream_ws`(stream-input WS, 텍스트 청크 즉시 송신),
  `orchestrator.run_voice_streaming`(스트리밍 중 voice_response 부분 디코딩 — streaming
  JSON string 파서: `_find_value_end` + `_decode_partial`), `bot._run_llm`이 asyncio.Queue로
  voice 토큰을 `speak_streaming`에 흘림. 첫 voice 토큰 즉시 TTS 시작 → voice·text 생성과 병렬.
  *(2026-06-05 master 통합 시 bot은 voice-first 경로로 단일화 — 이 경로는 코드로만 보존.)*
- **트레이드오프(실측 확인)**: `chunk_length_schedule=[50]`(ElevenLabs 최소)이라 overlap 실이득은
  50자 초과 응답에서 큼(긴 응답: 첫 오디오가 전체 텍스트 피드 완료 전 도착 실증). 50자 미만
  짧은 응답은 HTTP와 대체로 동등(연결·ffmpeg 조기 준비 이득은 유지). 회귀 없음.

**검증 (tests/, 네트워크 격리 + 라이브)**
- `test_voice_streaming.py`: 파서 5케이스(normal/이스케이프/빈voice/코드펜스/유니코드) × chunk
  1·3·통짜 — voice_chunk 합·voice_end 1회·순서 전부 통과.
- `verify_tts_live.py`: 라이브 HTTP 0.41s / WS / WS→ffmpeg PCM 디코딩 / overlap 실증 통과.
- 기존 `tests/test_orchestrator.py`는 **스테일**(제거된 `SYSTEM_PROMPT` import, 옛 5-tier 인텐트
  라벨 참조 — Phase 4 3-tier 리팩터 잔재). 이번 작업 범위 아님. 추후 정리 필요.

---

#### 2026-06-02 — Phase 6 MCP/native 툴 통합 구현 (런타임 미검증)

Opus 4.8 설계 스펙(`Second Brain\plans\mcp-toasty-melody2.md`) 기반으로 Phase 6 코드 구조를 완성했다.
**단, 외부 서비스에 실제로 연결된 것은 없으며 import/syntax 수준 검증만 완료된 상태.**

| 구성 요소 | 내용 |
|----------|------|
| `core/orchestrator.py` | 전면 재작성 — `ToolHandle` 레지스트리로 MCP/native 툴 통합, `AsyncExitStack` 기반 MCP 생명주기 (`start()`/`aclose()`), tool-use 루프(`_tool_voice_first`, non-streaming)와 trivial 스트리밍 경로 분리 |
| `core/native_tools/calendar.py` | 신규 — Google Calendar read 실구현 (lecture_notes의 `google_credentials.json` 재사용, 첫 호출 시 OAuth 브라우저 인증 → `calendar_token.json` 저장) |
| `core/native_tools/vehicle.py` | 신규 — Hyundai Bluelink stub (mock 데이터: 연료/주행거리/주차위치) |
| `core/native_tools/kakao.py` | 신규 — KakaoMap 장소 검색 + 역지오코딩 (`KAKAO_REST_API_KEY` 없으면 stub) |
| `core/providers/anthropic.py` | `complete()` non-streaming 메서드 추가 (tool-use 루프용) |
| `core/providers/base.py` | `Message.content`: `str` → `Union[str, list[dict]]` (tool_use/tool_result 블록 지원) |
| `config.yaml` | `mcp_servers.notion` (stdio, npx), `tool_use.max_iterations=5`, `tool_timeout_s=15` |
| `bot.py` | `orchestrator.start()`/`aclose()` 연동, filler 단계 처리, `asyncio.run(_main())` 클린 셧다운 |
| `tools/chat_test.py` | `_tool_turn()` (tool-use 경로 테스트), `!tools` 커맨드 |
| `.env.example` | `NOTION_API_KEY`, `KAKAO_REST_API_KEY`, `HYUNDAI_CLIENT_ID/SECRET` 항목 추가 |
| `pyproject.toml` | `mcp>=1.27.2`, `google-auth-oauthlib`, `google-api-python-client` 추가 |

**주요 결정:**
- **ToolHandle 통합 레지스트리** — MCP 툴(Notion)과 native 툴(Calendar/Hyundai/Kakao)을 단일 dataclass로 통합. tool-use 루프는 kind 구분 없이 `_call_tool_safe()` 하나로 호출.
- **tool-use 경로는 non-streaming** — streaming 중에는 stop_reason을 알 수 없으므로 `provider.complete()`로 전체 응답 수신. trivial 인텐트/툴 없음 경로는 기존 voice-first 스트리밍 유지.
- **Brave Search P1 이연, vehicle/kakao 실연동은 키 확보 후로 이연** — interface-first stub으로 인터페이스만 확정.

상세 내역: `Documentations(Claude)/daily/2026-06-02-car-assistant.md`

#### 2026-05-28 — Phase 5 세련화 / 비정상 종료로 대화 유실 (git으로 복원)

> 이 항목은 비정상 종료로 날아간 3시간 세션을 git 히스토리 + otto_events.log로 역추적해 재구성한 것이다.

**ba2c264 커밋 (2026-05-28 00:02) — Phase 5 세련화**

otto_events.log를 보면 2026-05-27 23:36~23:39 테스트에서 발견된 문제들이 이 커밋에서 한꺼번에 해결됐다.

| 발견된 문제 | 원인 | 수정 |
|------------|------|------|
| Discord heartbeat가 끊기는 현상 | STT transcribe()가 faster-whisper generator를 메인 이벤트 루프에서 소비 → 루프 독점 | `core/stt.py`: generator 소비를 executor 안으로 이동. `bot.py`: `asyncio.sleep(0)` 양보 포인트 삽입 |
| 첫 번째 발화 후 다음 발화 캡처가 너무 일찍 끊김 | 세션 유지 시 tail_ms(1.5s) 동일 적용 → 말하기 전에 이미 타임아웃 | `first_turn` 파라미터 도입: 첫 턴 1.5s, 이후 턴 3.0s 침묵 타임아웃 |
| voice_response 완성 후 text_response 대기 시간 낭비 | `handle()`이 voice+text 모두 완성 후 TTS 시작 | `core/orchestrator.py`: `run_voice_first()` 추가 — voice_response 완성 즉시 TTS Task 시작, text_response는 병렬 생성 |
| 매 턴마다 시스템 프롬프트 전체를 전송 (비용 낭비) | 캐싱 미적용 | `core/providers/anthropic.py`: `cache_control: ephemeral` 적용 |
| wake word 감지/세션 종료 타이밍이 불명확 | 시각/청각 피드백 없음 | `core/tts.py`: `play_cue()` 추가. `Otto enter.mp3` (wake+다음 턴 직전), `Otto quit.mp3` (세션 종료 즉시) |
| tail_ms 너무 길어 응답 후 다음 입력까지 오래 기다림 | config: `tail_ms: 3000` | `config.yaml`: `tail_ms: 3000 → 1500` |

**ba2c264 이후 테스트 로그 분석 (00:02~00:09)**

```
00:05:39  STT: 36.54s — "그리고 지난번에만"   ← CPU 모드에서 긴 캡처(1.6s) 전사 36초
00:06:39  STT: 12.57s — "한글자막 by 한효정"  ← 배경 TV 소리가 전사됨 (오탐)
00:07:29  STT: 40.91s — "자막 제공 및 영상..."  ← 동일한 배경 오탐, STT 41초
00:08:23  캡처: 12.2s, STT: 17.74s            ← 긴 발화(브이로그 언급) 테스트
00:09:14  STT: 16.99s — "조용히 하라고 아"   ← 마지막 로그
```

**해석:**
- CPU 모드에서 STT가 12~41초로 너무 느려 실사용 불가 상태. 데스크탑 GPU 이식이 시급한 이유.
- 배경 음성(TV 등)이 wake word 이후 캡처 버퍼에 섞여 LLM까지 전달됨. MIN_SPEECH 가드는 있으나 짧은 배경음도 STT가 유효한 텍스트로 전사함.
- 00:09:19 세션 종료 후 비정상 종료 발생. 이후 추가 커밋 없음.

**유실된 작업 범위:**
- 코드: `tools/chat_test.py` --tts 플래그 (unstaged 상태로 보존됨 — 손실 없음)
- 코드 외: 00:09 이후 대화에서 논의했을 다음 계획·결정 사항 — 이 항목이 유일한 손실

**b97c596 커밋 (2026-05-28 01:25) — cue 재생 직렬화 + 구간 추출**

ba2c264 테스트에서 발견: enter cue와 발화 캡처 Task가 `create_task`로 동시 시작 → cue(0.9s) 재생 중 타임아웃(1.5s)이 이미 소모되어 실질 대기 0.6s밖에 안 남는 구조적 결함.

| 수정 내용 | 이전 | 이후 |
|----------|------|------|
| cue + 캡처 타이밍 | `create_task` 동시 시작 | `await play_cue()` 완료 후 `create_task(_capture)` 생성 |
| cue 파일 | `Otto enter.mp3` (6.82s 전체) | `cues/otto_enter.mp3` (0~0.905s 추출, ffmpeg trim+fade) |
| quit cue | `Otto quit.mp3` (9.27s 전체) | `cues/otto_quit.mp3` (2.938~4.603s 추출, 당시 오류 포함) |
| 세션 종료 cue 타이밍 | cue와 `wake_detector.resume()` 동시 | cue 완료 후 resume (cue 중 재감지 방지) |

**fcf8b2b 커밋 (2026-05-28 02:16) — quit cue 무음 버그 + STT hallucination 필터**

| 문제 | 원인 | 수정 |
|------|------|------|
| quit cue 무음 | `-ss -to` 옵션 조합이 해당 ffmpeg 버전에서 오작동 → 실제로는 무음 구간 추출됨 (volumedetect max -91 dB) | `ffprobe` 챕터 메타데이터 확인 → `atrim=start=2.905:end=6.538` 재추출 (max -11 dB 정상) |
| STT hallucination | Whisper known issue — 무음/배경소음 구간에 학습 데이터 문구 삽입 ("자막 제공 및..." 등) | `no_speech_threshold=0.6`, `condition_on_previous_text=False`, known 패턴 블랙리스트 필터 추가 |

**bd6ba91 커밋 (2026-05-28 02:23) — TTS 진짜 스트리밍**

기존 `speak()`는 ElevenLabs MP3 전부 수신 → ffmpeg 전체 디코딩 → Discord 재생 순서라 첫 소리까지 7~10초 소요. 근본적으로 재설계.

| 변경 | 이전 | 이후 |
|------|------|------|
| TTS 재생 방식 | 전체 수신 후 재생 | `_StreamingPCMAudio` 클래스 — ffmpeg 생산과 Discord 소비를 `queue.Queue`로 브릿지, 첫 PCM 청크 도착 즉시 `voice_client.play()` |
| TTS 첫음절 지연 | 7~10s | 0.72s (실측, ElevenLabs 요청 후 기준) |
| 스레드 경계 | — | Discord 오디오 스레드가 동기 환경 → `asyncio.Queue` 불가, `queue.Queue` 사용. `read()` 시 `queue.Empty`이면 무음 반환으로 재생 끊김 방지 |

현재 타이밍 프로파일 (CPU 노트북 실측):

| 단계 | 실측 |
|------|------|
| VAD tail | 1.5s |
| STT | 11.9s (GPU 이식 시 1~2s 예상) |
| LLM→voice_response | 2.8s |
| TTS 첫음절 | 0.72s |
| 말 멈춤→첫 소리 합계 | ~16s (GPU 후 ~5~6s 목표) |

---

#### 2026-05-27 — Phase 5 구현 (TTS + 세션 모드 + 효과음 설계)

**0c31a74 커밋 (15:16) — core/tts.py 신규 + 세션 모드**

*왜 세션 모드를 도입했나:*
기존 구조는 wake word → 발화 1회 → IDLE 복귀였다. 연속 대화를 하려면 매번 "크랭크 오토"를 불러야 해서 운전 중 사용성이 떨어졌다. wake word 1회로 세션을 열고 명시적 종료 또는 무응답으로 닫는 방식으로 전환.

| 추가된 것 | 이유 |
|----------|------|
| `_session_active: bool` 플래그 | IDLE 복귀 시점을 종료 키워드/무응답으로 제어하기 위함 |
| `_SESSION_CLOSE_KEYWORDS` ("슬립 오토", "sleep otto" 등) | 운전 중 자연스럽게 종료할 수 있는 명령어. STT 전사 레벨에서 처리해 LLM 호출 없이 바로 IDLE 복귀 |
| `had_transcript` 플래그 | 빈 transcript(오탐, 노이즈)일 때는 세션 유지하지 않고 IDLE 복귀 |
| `speak()` + `wake_detector.pause()/resume()` | TTS 재생 중 봇 자신의 음성이 wake word를 재트리거하는 에코 방지 |

*왜 `speak_local()`을 별도로 만들었나:*
Discord 봇 없이 터미널에서 TTS 품질을 검증하기 위해. ffmpeg→PCM→sounddevice로 로컬 스피커 출력. `tools/chat_test.py --tts` 플래그와 연동.

*chat_test.py --tts 플래그가 미커밋으로 남은 이유:*
같은 세션에서 작업했으나 커밋 시 staged에서 누락된 것으로 추정. 코드 자체는 working tree에 보존됨.

---

#### 2026-05-26 — Phase 4 구현 (LLM 텍스트 응답 파이프라인 + Hyundai/Map API 조사)

**45cf6c9 커밋 (14:34) — LLM 파이프라인 초기 구현**

*왜 providers 추상화를 만들었나:*
단일 Anthropic 호출로 하드코딩하면 오프라인 폴백(Ollama), 인텐트별 모델 라우팅(Haiku vs Sonnet)을 나중에 추가하기 어렵다. `LLMProvider` Protocol로 추상화해 인텐트 분류기가 프로바이더 구분 없이 동일하게 호출.

*왜 Patch 3 (`_LowLatencyJitterBuffer`)를 추가했나:*
기존 `HeapJitterBuffer`는 비순차 패킷이 maxsize(10개)까지 쌓여야 강제 팝 → ~200ms 블로킹. 패킷이 1-2개만 비순차여도 즉시 팝하도록 오버라이드. wake word 감지 지연 개선이 목적.

*왜 PacketDecoder flush 경고를 억제했나:*
발화가 끝날 때마다 Opus decoder가 내부 버퍼를 flush하면서 WARNING이 출력됨. 실제 오디오 손상이 아닌 정상 동작이므로 ERROR로 레벨 상향(실질적 억제).

*왜 `time.monotonic()` deadline 방식으로 교체했나:*
기존 `total_frames >= max_frames` 방식은 VAD 청크 크기(512 샘플)와 캡처 버퍼 청크 크기가 달라 프레임 수 계산이 부정확했음. wall-clock 기반 deadline이 더 신뢰도 높음.

**2a47dc7 커밋 (16:19) — dual-response 시스템 프롬프트 + chat_test.py**

*왜 JSON dual-response 포맷을 강제했나:*
LLM에게 voice_response와 text_response를 하나의 응답에서 동시에 요청하면 마크다운(`**`, `##`)이 voice에 섞이거나 두 응답의 길이 비율이 제멋대로가 됨. JSON 스키마 강제로 voice는 짧게(음성 최적화), text는 상세하게 구조화.

*왜 `parse_dual_response()`에 코드 펜스 스트립과 폴백을 넣었나:*
Claude가 JSON을 ` ```json ... ``` ` 코드 펜스로 감싸서 반환하는 경우가 있음. 파싱 실패 시 전체 텍스트를 voice_response로 처리하는 폴백으로 빈 응답 방지.

*왜 3-tier intent routing으로 단순화했나:*
매뉴얼의 `note.create`, `calendar.read`, `calendar.write`, `research`, `simple_qa` 5분류는 MCP 툴이 없는 Phase 4에서는 의미 없음. `default(Sonnet)`, `trivial(Haiku)`, `complex_reasoning(Opus)` 3분류로 단순화해 Phase 6에서 툴 기반 라우팅으로 교체 예정.

**Hyundai Bluelink API + 카카오맵/Tmap 조사 (docs/):**
- Phase 6.5 차량 데이터 연동을 위한 사전 조사
- Bluelink: 공식 개발자 포털 OAuth 2.0 경로 확인, 읽기 가능 API 카테고리 5종 파악
- 지도: 카카오맵이 전시 데모에 유리 (무료 한도, Python 예제 풍부). Tmap은 경로 탐색 정확도 우위.
- 결론: 역지오코딩·POI 검색=카카오맵, 자동차 경로=Tmap 역할 분담 권장

---

#### 2026-05-23 — Phase 2 완료 (디버깅) + Phase 3 STT 통합

**6d69776 커밋 (01:22) — Phase 2 완료 (크랭크 오토, openwakeword)**

세션 시작 시점에 `wake_word.py`가 openwakeword가 아닌 Whisper 기반으로 교체되어 있었음. 복구 후 두 가지 근본 원인을 발견:

| 버그 | 원인 | 수정 |
|------|------|------|
| 모든 프레임 점수 0.0 | `AudioFeatures.__call__()`은 int16 PCM을 받아야 하는데 float32 전달 → mel spectrogram이 오디오를 무음으로 해석 | PCM dtype float32 → int16 변경, 훈련 경로도 동일하게 통일 |
| 감지 불안정 | CONFIRM_FRAMES streak 메커니즘이 코드 복구 시 누락됨 | `_streak` 카운터 복원 |

임계값 튜닝: `CONFIRM_FRAMES=2, threshold=0.85` 최종 확정. 훈련 결과 recall 100%, specificity 97.6%.

**5e7c87a 커밋 (05:18) — Phase 3 STT 통합**

| 컴포넌트 | 내용 |
|---------|------|
| `core/vad.py` | ONNX Runtime 기반 SileroVAD. v2/v3/v4 API 동적 감지. **핵심: 해당 silero_vad.onnx는 8kHz 전용** — 16kHz 입력 시 모든 프레임 ~0.001로 무음 처리됨. `audioop.ratecv`로 16kHz→8kHz 다운샘플 후 입력. |
| `core/stt.py` | faster-whisper `WhisperModel` 래퍼. `run_in_executor`로 비동기 처리. |
| `bot.py` | `capture_queue` 분리: `pcm_queue`(전체 스트림)와 별개로 LISTENING 상태에서만 채워지는 캡처 전용 큐. 두 코루틴이 동일 큐 경쟁 소비하는 버그 수정. `MIN_SPEECH=5` 가드: wake word 꼬리 에코가 speech_started 조기 트리거하는 문제 방어. |

Phase 3 품질 검증 통과 (CPU 모드 한정). 단, STT 지연 최대 42s (28.5s 오디오 기준) → GPU 이식 시 해결 예정.

*왜 Phase 4를 GPU E2E 없이 진입했나:* CPU에서 large-v3 전사 지연이 42s에 달해 STT 기능 자체는 검증됐으나 실사용 품질은 GPU 이식 없이 확인 불가. GPU 이식보다 LLM 연결(Phase 4) 코드 작업을 먼저 진행하는 게 병렬 효율이 높다고 판단. Phase 4 단위 테스트는 스텁 + CLI로 마이크 없이 검증 가능.

**58c5f0a 커밋 (05:26) — 다음 세션 시작 지점 문서화**

---

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
