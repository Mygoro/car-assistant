# 크랭크 오토(car-assistant) 전시 인수인계 보고서

**작성일** 2026-06-07 · **전시 D-2** (2026-06-09) · **수신** 클로드 데스크탑(전시 플래닝 총괄)

> **프로젝트 정의** — Discord로 듣고, 홈 서버에서 돌고, 음성으로 답하는 차량용 핸즈프리 음성 AI 어시스턴트. 학기말 전시 데모와 본인 실사용을 동시 목표로 한다.

---

## 1. 한눈에 보는 현황 (Executive Summary)

- **P0 루프(Wake→STT→LLM→TTS)는 데모 가능 상태로 완성됐다.** 데스크탑 GPU(RTX 5070 Ti) 기준 warm 연속턴에서 발화끝→첫소리 **평균 ~3.4s**(목표 5~6s 충족), STT warm **0.75s**가 실측 로그(`otto_events.log`)로 뒷받침된다.
- **Phase 6(MCP/native 툴)·Phase 7(컨텍스트·페르소나)은 실대화 검증을 통과했다.** Calendar/Hyundai/KakaoMap/Places/Brave/Notion이 실API로 라이브 동작하며, 키·토큰 파일도 디스크에 실재한다.
- **위치 기능은 폰 능동 전송 방식 GPS 파이프라인이 구현·가동 중이다.** `core/location_server.py`가 폰용 `watchPosition` 페이지를 서빙하고 `POST /loc`로 좌표를 받아 `core/location.py`(set_current/get_current, 300s stale 가드)에 저장하며, `bot.py:200`이 부팅 시 위치 서버(port 8765)를 기동한다. kakao 툴이 좌표 미지정·"여기" 발화 시 `get_current()`로 폴백한다. **구조적 부재가 아니라**, 폰이 cloudflared https URL로 위치 공유 페이지를 켜두고 좌표를 보내야 동작하므로 **전시장에서 이 셋업이 안 되면 좌표 미수신으로 지명 폴백**된다는 것이 실제 한계다(지하/실내 정확도 포함).
- **결론: 데모는 가능하다. 단 "되는 발화"로 동선을 좁힌다는 전제 하에서다.** 넓은 범위(올해/연간) 캘린더 질의는 캘린더 출력 비대 미해결로 2~3회 재조회·지연을 유발하고, 멀티-tool 질의는 28초까지 늘어난 실측이 있다.
- **반드시 주의할 3대 운영 리스크**: ① **`--profile exhibition` 누락 시 개인정보 fail-open**(기본값 personal), ② **config.yaml이 `device:cuda`로 커밋**돼 노트북 CPU 폴백 시 STT 11~13s로 시연 불가, ③ **장소 환각이 차단 없이 그대로 발화**(grounding은 관측 로그뿐).
- **전시 문서 드리프트가 크다.** 운영 3문서(roadmap/booth/script)는 모두 옛 영어 wake word "hey OTTO"·옛 날짜(06-02)·mock 차량 전제로 작성돼 있고, 실제 구현은 한국어 "크랭크 오토"·실 Hyundai Bluelink다. **인쇄물·대본 갱신이 D-2 필수 조치**다.
- **데이터 안전성 핵심 사실**: 현재 시연 머신에 `core/memory.local.md`가 존재하지 않아, 어떤 프로파일로 띄워도 민감정보 주입 경로가 사실상 0이다(단 시연 전 누가 생성하면 다시 위험).
- **신규 식별 보안 리스크**: 위치 서버가 `0.0.0.0:8765`에 **무인증** 바인딩되어, cloudflared URL이 노출되면 외부에서 봇의 "현재 위치"를 임의 주입 가능하다(9절 M13 신규).

**데모 가능 여부 종합**: **GO (조건부)** — 운영 데스크탑 GPU + `--profile exhibition` + 좁은 범위 데모 스크립트 + 데모영상 폴백을 전제로 GO. 노트북 CPU 단독 운영은 NO-GO.

---

## 2. 프로젝트 정의 & 이중 목표

원문 정의는 *"A voice-activated AI assistant that listens through Discord, runs on your home server, and responds with speech — hands-free, in your car."*

| 목표 | 내용 | 현재 충족도 |
|------|------|-------------|
| **전시 데모** (2026-06-09) | 학기말 전시 부스에서 본인 시연 + 방문자 직접 호출로 음성 어시스턴트 시연 | P0 루프 완성, 단 운영·문서 정합성 작업 잔존 |
| **본인 실사용** | 차량 내 핸즈프리로 일정·차량 데이터·길찾기·메모 조회 | 실API 전 기능 라이브. 위치는 **폰 능동 전송 GPS 파이프라인 구현됨**(location_server + location + kakao get_current 폴백, bot 부팅 시 기동) — 단 폰 위치공유 페이지 상시 가동에 의존하며 지하/실내 정확도가 실제 제약 |

핵심 설계 결정: dual-response JSON(voice/text 분리), 3-tier 인텐트 라우팅(실질 Sonnet 통일), memory.md 컨텍스트 주입, Discord mobile 클라이언트 입력, wake word "크랭크 오토" 한국어 피벗, **봇 메모리·프롬프트에 사적/연애 맥락 전면 배제(기능적 맥락만)**.

---

## 3. Phase 0~8 완료 현황

| Phase | 내용 | 상태 | 비고 |
|---|---|---|---|
| **0** | Discord 봇 기초 (자동 접속, 재접속 watchdog) | ✅ 완료 | — |
| **1** | 오디오 수신·저장 (DAVE E2E 패치) | ✅ 완료 | WAV 디버그 검증. bot.py Patch 1~3로 안정화 |
| **2** | Wake Word 게이트 | ✅ 완료 | openwakeword, **크랭크 오토**(`crank_otto.onnx`), threshold 0.85, CONFIRM_FRAMES 1. "hey otto" 오탐으로 피벗(archive:527) |
| **3** | STT 통합 | ✅ 완료 | Silero VAD(내부 8kHz) + faster-whisper large-v3, capture_queue 분리, MIN_SPEECH 가드 |
| **4** | LLM 텍스트 응답 | ✅ 완료 | 3-tier 인텐트, Orchestrator, dual-response JSON, voice-first 스트리밍 |
| **5** | ElevenLabs TTS 스트리밍 | ✅ 완료 | `_StreamingPCMAudio`, Discord 송출, 세션 모드, 효과음 cue |
| **GPU 이식** | 데스크탑 RTX 5070 Ti | ✅ 완료 (06-03) | `core/cuda_setup.py`로 Blackwell DLL 해결. STT 0.75s |
| **6** | MCP/native 툴 통합 | ✅ 런타임 검증 완료 (06-06) | Notion stdio MCP + native 10종. Calendar/Hyundai/KakaoMap/web_search/Places 실연동 |
| **7** | 컨텍스트 오케스트레이션 & 페르소나 | ✅ 실대화 검증 통과 (06-07) | memory.md 주입 + 소스 라우팅 + 맥락 통합. **사적맥락 제외 확정** |
| **8** | 품질 하드닝 | ◐ 부분 완료 (06-07) | 데모 직결(grounding 관측·STT 2차보정·모호참조·회귀묶음)만 반영. **히스토리 압축은 전시 후로 보류** |

---

## 4. 전체 파이프라인 구조

### E2E 데이터 흐름 다이어그램

```
[Discord 48kHz 스테레오 s16le]   (OWNER_USER_ID만 통과, audio_sink.py:42)
        │  audioop.ratecv (상태유지) + L/R 평균
        ▼
[16kHz 모노 int16]  ──call_soon_threadsafe──▶  asyncio 루프  (오디오 스레드 → 루프 브릿지)
        │  pcm_queue
        ▼
┌─ 상태머신 (bot.py:203-225) ──────────────────────────────┐
│  IDLE ──▶ Wake word 게이트 (wake_word.py, owwk int16 프레임)│
│           threshold 0.85, CONFIRM_FRAMES 1                 │
│  감지 시 → LISTENING, capture_queue 분리                   │
│  LISTENING/PROCESSING → capture_queue.put_nowait          │
└────────────────────────────────────────────────────────────┘
        │  16kHz int16 512샘플(32ms) 프레임
        ▼
[Silero VAD]  ★16kHz 입력을 내부 8kHz로 ratecv 다운샘플 후 추론 (vad.py:43-45)
        │  threshold 0.3, tail 1.5s(첫턴)/3.0s(이후), MIN_SPEECH 5
        ▼  캡처 버퍼 (np.concatenate)
[faster-whisper large-v3]  float32/32768, beam 5, vad_filter, no_speech 0.6
        │  initial_prompt = config 고유명사 + memory.md stt-hints 병합
        │  hallucination 2단 방어(no_speech_prob>0.6 폐기 + 블랙리스트)
        ▼  한국어 transcript
[Orchestrator.run_voice_first]  ── 통합 단일 라우터 ──
        │  classify_intent → provider 선택 → tool-use 루프(max 5 iter)
        │  dual-response JSON 스트리밍 파싱 → voice_response 닫히는 즉시 발화
        ▼  (stage, content): voice / text / filler
[ElevenLabs TTS]  stream_mp3(HTTP), eleven_flash_v2_5, optimize_latency 3
        │  MP3 bytes async gen
        ▼
[ffmpeg -f mp3 -nobuffer]  → 48kHz 스테레오 s16le, FRAME 3840(20ms)
        │  _StreamingPCMAudio: async push/finish ↔ queue.Queue(max 200) ↔ Discord read()
        │  재생 중 wake_detector.pause() (에코 방지)
        ▼
[Discord 음성 송출]

  [부가 입력] 폰 GPS:  폰 브라우저(cloudflared https) ─watchPosition→ POST /loc
              location_server(0.0.0.0:8765, bot.py:200) → location.set_current
              → kakao 툴이 get_current()로 "근처/여기" 좌표 폴백 (300s stale 가드)
```

### 단계별 입출력·파라미터·실측 (출처 보존)

| # | 단계 | 파일:라인 | 입력 | 출력 | 핵심 파라미터 | 함정 |
|---|------|-----------|------|------|---------------|------|
| 1 | Discord→다운샘플 | `audio_sink.py:41-58` | 48kHz 스테레오 s16le | 16kHz 모노 int16 | ratecv 상태유지 | OWNER만 통과(:42), L/R 평균(:49), 스레드 브릿지(:58) |
| 2 | 큐 분배(상태머신) | `bot.py:203-225` | pcm_queue 16kHz | wake or capture_queue | — | capture_queue 분리로 wake·캡처 경합 차단 |
| 3 | Wake 게이트 | `wake_word.py:43-71` | 16kHz int16 1280샘플 | bool | th 0.85, CONFIRM 1 | int16 그대로 predict, 감지 후 reset, run_in_executor |
| 4 | VAD 캡처 | `bot.py:240-296`,`vad.py:40-58` | 16kHz int16 512샘플 | 캡처 버퍼 | th 0.3, tail 1500, max 30s, MIN_SPEECH 5 | **내부 8kHz 다운샘플**, 첫턴 침묵 1.5s·이후 3.0s |
| 5 | STT | `stt.py:43-73` | 16kHz int16 mono | 한국어 str | large-v3, beam 5, no_speech 0.6, condition_on_prev False | 2단 환각 방어, initial_prompt 병합 |
| 6 | LLM | `bot.py:349-405`,`run_voice_first` | transcript | voice/text/filler 스트림 | — | trivial/툴없음→voice-first, 툴→루프+filler |
| 7 | TTS 생성 | `tts.py:28-49` | voice_response | MP3 async gen | optimize_latency 3, flash_v2_5, stability 0.5/sim 0.75 | bot은 stream_mp3(HTTP), WS 미사용 |
| 8 | MP3→PCM→송출 | `tts.py:138-206` | MP3 | 48kHz 스테레오 PCM | ffmpeg nobuffer, FRAME 3840 | queue.Queue(200) 언더런 시 무음, 재생 중 wake pause |
| + | 폰 GPS 수신 | `location_server.py:72-82`,`location.py:19-29` | 폰 watchPosition POST | (lon,lat) 현재좌표 | port 8765, stale 300s | **0.0.0.0 무인증 바인딩**, 폰 페이지 꺼지면 갱신 중단 |

### GPU vs CPU 실측 (★전시 운영 결정에 직결)

| 항목 | GPU (cuda/int8_float16) | CPU (cpu/int8) | 출처 |
|------|--------------------------|-----------------|------|
| STT warm | **0.75s** (cold 첫추론 ~23s PTX JIT 1회성) | 11~13s | archive:274,281; manual:703 |
| 발화끝→첫소리 (warm 연속턴) | **평균 ~3.4s** (2.98~3.97s), 첫턴 ~5.3s | ~26s | archive:244-248,282 |
| TTS 첫음절 | 0.72~1.11s | 동일(클라우드, 무관) | archive:282,395 |
| 멀티-tool 질의 (최악) | voice 17.3s, 총 28.75s (cal ×3 iter) | — | otto_events.log 06-07 |
| 병목 | **LLM 첫 토큰 ~1.9s(E2E ~55%)** | STT 압도적 | archive:248 |

**Blackwell DLL 해결**: `core/cuda_setup.py`가 `stt.py:8`에서 faster_whisper import 전에 호출돼 nvidia 패키지 bin을 PATH+`os.add_dll_directory`에 등록(:33-47). win32 아니거나 nvidia 패키지 없으면 no-op(노트북/Linux 안전).

> ⚠️ **현재 config.yaml은 `device: "cuda"`, `compute_type: "int8_float16"`로 커밋됨**(직접 확인, config.yaml:7-8). CLAUDE.md 본문은 "노트북 CPU 작업 중"으로 서술하나 커밋된 config는 이미 데스크탑 GPU 값. **노트북 폴백 시 반드시 cpu/int8로 되돌려야 함.**

### 안정성 패치 (bot.py 모듈 로드 시 적용)
- **Patch 1**(`:121-133`): 단일 손상 Opus 패킷이 라우터 스레드 전체를 죽임 → per-packet try/except.
- **Patch 2**(`:137-155`): discord-ext-voice-recv가 DAVE(E2E) 복호화 미적용 → opus 디코더 전 DAVE 레이어 제거.
- **Patch 3**(`:161-182`): HeapJitterBuffer maxsize=10이 ~200ms 블로킹 → `_FORCE_POP=2`, prefsize/prefill=0으로 즉시 팝.

---

## 5. 핵심 기능 & 툴 인벤토리

등록: `orchestrator.py:407~566` `_register_native(...)` + `config.yaml:37~50` Notion MCP. **Notion 1종(stdio MCP) + native 10종.**

| 툴 | 소스 (실/스텁) | 인증·토큰 | 제공 데이터 | 한계 |
|---|---|---|---|---|
| `get_vehicle_status` | **실** Hyundai Developers | `HYUNDAI_CLIENT_ID/SECRET`(.env) + `hyundai_token.json`(refresh 자동) | 주행가능거리(DTE)·누적주행거리(Odometer) | **연료%·GPS 미지원**(한국 공식 API 미제공, vehicle.py:6). 프롬프트 가드(:155-158) |
| `get_calendar_events` | **실** Google Calendar v3 | `google_credentials.json`+`calendar_token.json`(OAuth refresh) | 일정 조회(개인+공유, 공휴일 제외, 중복 제거, 캘린더당 maxResults 20) | **출력 비대 truncation 이슈**(아래 ⚠). 줄마다 `[cid::ev_id]` |
| `create_calendar_event` | **실** | 동상 | 일정 생성(primary, KST) | start 누락 시 에러 |
| `update_calendar_event` | **실** | 동상 | 일정 수정(`cid::eid` 분리로 공유 타겟) | event_id 선행 조회 필요 |
| `delete_calendar_event` | **실** | 동상 | 일정 삭제 | event_id 선행 조회 필요 |
| `search_nearby_places` | **실** Kakao Local keyword | `KAKAO_REST_API_KEY` | 장소명·도로명주소·거리 | **좌표 미지정 시 폰 GPS 자동 폴백**(`get_current`, kakao.py:58-62). 폰 위치공유 미가동/stale 시에만 지역명 의존. 키 없으면 stub |
| `get_directions` | **실** Kakao Mobility Navi + Local 지오코딩 | `KAKAO_REST_API_KEY`(지오) + `KAKAOMOBILITY_REST_API_KEY`(경로, 없으면 전자 폴백) | 소요시간·거리·통행료·**미래 교통량 예측** | **"여기/현재 위치"류 발화(`_HERE_WORDS`) 시 폰 GPS를 출발지로 직접 사용**(kakao.py:189-204), 좌표 미수신 시 "현재 위치를 아직 못 받았어요…" 안내 반환. 콘솔 "카카오내비" 사용설정 필요. 키 없으면 stub |
| `reverse_geocode` | **실** Kakao coord2address | `KAKAO_REST_API_KEY` | 좌표→한국어 주소 | **폰 GPS 좌표→주소 변환 가능**, 단 응답 경로상 직접 노출은 제한적(주로 좌표→지명 보조용) |
| `get_place_details` | **실** Google Places (New) Text Search | `GOOGLE_MAPS_API_KEY` | 영업시간(오늘 1줄)·평점·리뷰수·리뷰2건·가격대·전화·openNow | 무료 월 Contact 5,000/Atmosphere 1,000. **요일 전체→오늘 1줄 축소**(지연·토큰 절감) |
| `web_search` | **실** Brave Search | `BRAVE_API_KEY` | 웹 스니펫(제목·설명·도메인) | **보조용 격하**(스니펫만 줘 부정확). 무료 월 2,000, 429 안내 |
| Notion (5툴) | **실** MCP `@notionhq/notion-mcp-server`(npx stdio) | `NOTION_API_KEY`→`NOTION_TOKEN` | 빠른메모·강의노트 DB·페이지·블록 조회·검색 | **화이트리스트 5툴만**(22→5 축소): `API-post-search`, `API-query-data-source`, `API-retrieve-a-data-source`, `API-get-block-children`, `API-retrieve-a-page` |

> 📍 **위치 입력원 보강(코드 확인)**: 위 search_nearby_places·get_directions·reverse_geocode는 **봇 부팅 시 기동되는 폰 GPS 파이프라인**(location_server `0.0.0.0:8765` → location.set_current → get_current 폴백, 300s stale)에 의해 실제 현재 좌표를 받을 수 있다. 도입 커밋 `b748913 feat(gps)`로, manual:963의 "실주행 GPS 보류" 서술보다 **나중에 추가됐다**. 따라서 위치 한계는 "입력원 부재"가 아니라 "폰 위치공유 페이지 상시 가동 의존 + 지하/실내 정확도"다.

### 토큰 파일 실측 (2026-06-07 점검) — `core/native_tools/`
- `calendar_token.json` (736B, 18:35 갱신) — **존재**
- `google_credentials.json` (407B) — **존재** (강의노트 automation 재사용)
- `hyundai_token.json` (1,262B, 16:47 갱신) — **존재**, access/refresh/expires_at/car_id 포함
- KAKAO/GOOGLE_MAPS/BRAVE/HYUNDAI_CLIENT = **.env 환경변수**(미설정 시 stub/graceful 폴백)

> ⚠️ **Hyundai 토큰 상태**: 점검 시점 `expires_at=1780822040` vs 현재 `1780859975` → access_token이 약 **10.5시간 이미 만료**. 단 `_ensure_token()`(vehicle.py:45-71)이 만료 5분 전부터 refresh로 자동 갱신, refresh rotation도 저장(:68-69). **전시 전 1회 실호출로 갱신 성공·DTE/Odometer 응답 확인 권장.**

### Notion 데이터소스 라우팅 (system_prompt:124-145)
- **빠른 메모** → `data_source_id: 18d0ae87-66fa-81a4-bfa5-000b75b379b8`
- **강의 노트** → `data_source_id: 33700100-cc38-46a9-8b2d-cd4e35b96abb` (제목 `[과목] N주차`)
- **강의 본문 voice 통째 낭독 금지**(≤100자 요약 강제) — 과거 긴 본문이 JSON 파싱 실패·ITPM 폭주 유발한 이력 대응(archive:203-227)

---

## 6. LLM 오케스트레이션 동작

### 진입점·라우팅 (실제 배선)
봇이 실제 소비하는 단일 통합 라우터는 **`run_voice_first`**(`bot.py:361`). `run_voice_streaming`(⑥ overlap, voice_chunk 토큰 단위)은 **코드만 존재, 봇 미배선**(voice_response 짧아 overlap 실이득 작음 — CLAUDE.md 기술과 일치).

`run_voice_first`(orchestrator.py:622) 분기:
1. `_RESET_KEYWORDS`("리셋"/"초기화") → 히스토리 clear 후 즉시 반환
2. `classify_intent` → `_get_provider` → `_wants_full`
3. `trivial` 또는 `not self._tools` → `_stream_voice_first`(툴 없는 스트리밍)
4. 그 외 → `stream_final:true`이면 **`_tool_voice_streaming`(티어2)**, 예외 시 `_tool_voice_first`(complete 폴백)로 강등

### 인텐트 3-tier (키워드 휴리스틱, LLM 분류 아님)
- `trivial`: trivial_patterns 포함 **AND len(t)<15** → `claude-haiku-4-5`
- `complex_reasoning`: "깊이 생각/자세히 분석/꼼꼼히" → `claude-sonnet-4-6`
- `default`: 그 외 전부 → `claude-sonnet-4-6` (Opus→Sonnet 통일됨, 06-06)
- `offline_fallback: ollama/qwen2.5:14b`는 **테이블에만 존재, 자동 트리거 코드 없음**(수동/미래용, Ollama는 tools 미지원)

### dual-response JSON & voice-first 원리
시스템 프롬프트(`system_prompt_template.txt:9-28`)가 **모든 응답을 `{"voice_response":..., "text_response":...}` JSON으로만** 강제. voice는 1~2문장(50~100자), text는 durable record. 무의미 발화는 두 필드 모두 `""`.

- voice-first: 스트림 중 `_VOICE_START_RE`로 voice 값 시작점 탐지 → `_find_value_end`로 이스케이프 안 된 닫는 따옴표 탐지 → 닫히는 즉시 `_decode_partial` → `validate_voice_length` → `yield "voice"`. **긴 text_response 생성을 안 기다리고 TTS 시작.**
- **3단 파싱 안전망**(`parse_dual_response`:172): ① 코드펜스 제거+`{`~`}` 추출 후 json.loads → ② 실패 시 voice 값만 추출+잘린 prefix 복구(raw JSON 절대 TTS 안 흘림) → ③ voice도 못 건지면 `_SAFE_VOICE_FALLBACK` 음성 + 깨진 원문은 채팅만
- **길이 컷**: `_VOICE_MAX_CHARS=200`, `_FULL_KEYWORDS`("전부/길게/자세히" 등) 명시 시 `1200`. 종결부호(cut≥40)에서 절단. 커밋 `234fd2d`에서 "하나도" 단독 제거(부정문 오탐 방지)

### tool-use 루프 & 지연 (★핵심 병목)
- `range(self._max_iterations)`(config 5). `stop_reason=="tool_use"`면 블록 누적+실행+result append 후 continue.
- **지연 주범 = iteration 왕복**: 06-07 정량 진단 — "tool 호출 자체는 전체의 3% 미만, **82~94%가 최종 답변 토큰 생성 구간**"(2026-06-07-car-assistant.md:21). 커밋 `ac7101c`: "iteration 왕복(각 ~3~9s)이 첫소리 바닥을 잡음".
- 대응: ① 출력 축약(`7883f2f`), ② 티어2 스트리밍(`9dbff78`, 긴 답변 첫소리 **45~52% 단축**), ③ 프롬프트 round-trip 축소(`ac7101c`, 4→3 iteration). **근본원인(캘린더 거대 event_id 6000자 캡 truncation→재조회)은 미해결**.

### 프로바이더 계층 (캐싱)
`AnthropicProvider`의 `_build_kwargs`(anthropic.py:43)가 시스템 프롬프트에 `cache_control:{"type":"ephemeral"}`(:53) — 5분 캐시. **Sonnet은 cache_read가 ITPM에 미카운트** → cache_r 클수록 rate limit 여유.

### 전시 직전 크래시 2종 수정 (06-07)
1. **parsed_output 400**(`ca5decf`): 티어2에서 모델이 tool 호출 앞 텍스트 뱉을 때 `get_final_message()`가 text 블록에 `parsed_output` 부가 → `model_dump()` 통째 재전송 → 400 → 폴백 재실행(더 느림). **`_serialize_assistant_blocks`(:261)로 허용 필드만 재전송**. tests/test_tool_streaming.py 5종 통과.
2. **캘린더 SSL 하드 크래시**(`9388a38`): `asyncio.gather` 병렬화가 캘린더 전역 싱글톤 `_service`(공유 googleapiclient)를 두 스레드 동시 접근 → `[SSL: RECORD_LAYER_FAILURE]` → **try/except로도 못 잡는 C레벨 크래시**(에러 로그 없이 프로세스 종료). 병렬 이득 ~1s로 미미 → **순차 await 복원**(:799-807, 876-884). 동시성 재도입 절대 금지.

### grounding 관측 (차단 아님)
`_log_place_grounding`(:241)+`_extract_place_names`(:222): 장소 tool 결과의 place_name을 응답이 인용했는지 **관측만**, 차단 안 함. 환각 패턴 가시화용.

---

## 7. 테스트 데이터 & 검증 자산

### 회귀 케이스 분포 (`tests/regression_cases.yaml` — 실측 238케이스·18카테고리)
| 카테고리 | 수 | 검증 |
|---|---|---|
| calendar_read | 18 | expect_tools |
| calendar_write | 14 | ⚠ 실 캘린더 생성 |
| calendar_update_delete | 10 | ⚠ 실 캘린더 수정/삭제(멀티턴 4) |
| vehicle | 18 | 연료%/GPS 가드 6 |
| directions_now | 18 | expect_tools |
| directions_future | 12 | departure_time는 notes만(코드 미검증) |
| place_search | 18 | expect_tools |
| place_details | 14 | forbid search_nearby 다수 |
| notion | 14 | forbid web_search만 |
| web_search | 12 | expect_tools |
| composite | 16 | 2~3 tool 시퀀스 |
| context_multiturn | 16 | 마지막 턴만 |
| stt_correction | 12 | **notes만 — 자동판정 불가** |
| trivial | 12 | expect_intent |
| edge | 14 | 빈입력/필러/영어/거절/complex |
| format | 10 | **notes만 — 자동판정 불가** |
| hallucination_guard | 10 | **notes만 — 자동판정 불가** |
| **합계** | **238** | |

**구조적 한계**: stt_correction·format·hallucination_guard(**총 32건**)는 expect_tools/must_include 없어 **러너 자동 판정 불가** → 사람이 응답을 읽어야 함. 검증의 중심은 "어떤 tool 불렸나/금지 tool 안 불렸나 + 인텐트 + voice 길이 상한"이고 내용 단언(must_include)은 거의 없음. **회귀 통과 ≠ 품질 보증.**

### utterances.md (전시 큐시트, 미커밋)
회귀 238케이스에서 발화만 추출한 사람용 낭독 목록. 18 한글 섹션, `발화 (기대 동작)` 형식, 멀티턴은 `→`. **부스 시연 큐시트로 바로 사용 가능.** 단 git status `?? tests/utterances.md`(**미커밋 — 커밋 권고**). "동작하면 안 되는/모른다고 답해야 하는" 발화(연료%/GPS 미제공, 환각방지 10, 안전거절 2)도 섞여 있어, **"되는 발화"와 "가드 발화"를 구분해 동선 설계 필요.**

### 러너 (`tools/run_regression.py`)
- 기본 = **dry-run, LLM 미호출**(케이스 수·카테고리·id 중복 검사만, 비용 0)
- `--run`이어야 실 `run_voice_first` 호출. `--category`/`--limit`로 부분 실행
- 케이스 독립성: 매 케이스 `_history.clear()`, tool은 `_call_tool_safe` monkeypatch 추적, 멀티턴은 마지막 턴만 검증
- ⚠ **전량 `--run`은 `_call_tool_safe`를 그대로 통과 → calendar_write(14)/update_delete(10)이 실제 구글 캘린더를 생성/삭제**. 외부 API 비용+실데이터 오염 위험. → **읽기·라우팅 위주 카테고리만 `--category`로 표본 실행 권장**(calendar_read, vehicle, directions_now, place_search, web_search, context_multiturn)

### 단위/통합 테스트 3종
- **test_orchestrator.py** — **스테일 확정**: `SYSTEM_PROMPT` import 부재, 옛 5-tier 라벨(`note.create`/`calendar.read`), 부재 메서드(`handle`/`stream_handle`/`reset`) 참조. **pytest 전체 수집이 이 파일 때문에 import 단계에서 실패** → 삭제 또는 현행 API 재작성 권고
- **test_voice_streaming.py** — 현행 일치. 스트리밍 JSON 파서 정확성을 네트워크 없이 검증(chunk 1/3/통짜 동일 결과, 이스케이프·빈 voice·코드펜스·BMP 경계). **부분 토큰 경계에서 voice 안 깨짐 + voice가 text보다 먼저** 보장
- **test_tool_streaming.py** — 현행 일치. 티어2 루프(voice<text 순서, 멀티 iteration filler·tool, parsed_output 제거로 400 방지)를 **실 API 없이 결정적** 검증
- **verify_tts_live.py** — **실 ElevenLabs 호출**. HTTP/WS 첫청크 지연, MP3→ffmpeg→PCM 디코딩, overlap 실증. API 키·비용 필요(데모 직전 1회 sanity 적합)

### 실측 타이밍 근거 — `otto_events.log` (496KB, 06-07 18:38)
CLAUDE.md 원칙 8번 진단 1차 자료. `[TIMING]` 마커:
- 06-03 GPU 첫 측정: STT 0.75s, LLM→voice 2.82s, TTS 첫음절 1.11s, 총 10.58s
- 06-05 warm(15:41:42): STT **0.37s**, voice 첫토큰 1.77s, TTS 첫음절 **0.33s**, 총 **4.10s** → "warm ~3.4s·총 4~10s" 직접 뒷받침
- 06-07 멀티-tool(cal ×3): voice 17.31s·총 **28.75s** → **멀티-tool 발화 체감 느림 주의**

> 주의: 로그가 한글을 cp949류로 깨져 저장(모지바케)하나 TIMING/USAGE 영문·숫자는 판독 가능. 인코딩 UTF-8 고정 권고.

---

## 8. 전시 운영 계획

### 운영 3문서 (모두 옛 기준 — 드리프트)
| 문서 | 역할 | 작성/전시기준일 |
|---|---|---|
| `roadmap.md` | 마스터 설계(목표·Phase·리스크·절단순서) | 2026-05-22 / **06-02** |
| `booth-plan.md` | 부스배치·장비·포스터·운영리듬·트러블표·동의문 | 동일 |
| `demo-script.md` | 시연 대본(메인/스트레치/안전) | 동일 |

충돌 시 roadmap 우선(roadmap §0).

### 부스 구성 (booth-plan.md:1-31)
- 1인 테이블 + 노트북 1 + 콘센트 1, 약 6시간
- **핵심 아키텍처 전제**(:6-7): 봇은 **집 GPU 데스크탑 원격 구동**, 부스 노트북은 Discord **클라이언트(출력 전용)**. → 가장 큰 단일 리스크(집 데스크탑·강의실 Wi-Fi 6시간 무중단)
- 배치: 중앙 노트북(데모영상 루프/트랜스크립트), 유선 파워드 스피커(공용 출력), 폰 거치대(Discord 모바일 입력+Krisp), 안내카드, 동의문
- 입출력 분리: 노트북 마이크 비활성(이중 캡처 방지) · 폰 스피커 끔(에코 방지)
- **위치 데모를 켤 경우** 추가 셋업: 입력폰(또는 별도 폰)에서 cloudflared https URL로 위치 공유 페이지를 열어 화면 켜둔 채 유지(꺼지면 좌표 갱신 중단). **GPS를 안 쓸 거면 위치 공유 페이지 미배포로 노출 차단**(M13 참조).

### 시연 방식 3안 (demo-script.md)
1. **메인 — 본인 시연**(3~4분 루프): Step1 스케줄 조회(P0, Calendar+Notion, 8~15s) → Step2 차량(P0, "기름 얼마"; ⚠ **대본은 mock 42%/320km 전제이나 코드는 실 Bluelink만**) → Step3 멀티턴 추론(일정+연료→주유 시점) → Step4 차내 캠(P1, 여건 시; 안 되면 녹화)
2. **스트레치 — 방문자 직접 호출**: exhibition 프로파일 전제(쓰기 off·세션 히스토리 리셋 — ⚠ **코드 미구현**). openwakeword 화자독립. 진짜 병목은 STT(소음+낯선 발음) → "또박또박" 안내, 실패 시 본인 대행
3. **안전 — 영상 폴백**: 2~3분 데모영상 무한루프(자막, 로컬저장→인터넷 불필요). 장애 시 **10초 내 영상 후퇴**. "폴백은 실패가 아니라 설계된 경로"

### 제약·동의
- **Wake word**: 문서 전반 영어 "hey OTTO"(roadmap:68, demo-script 전 스텝)이나 **실제는 한국어 "크랭크 오토"**(config.yaml:1-3, `crank_otto.onnx` 존재). 피벗 사유 = hey otto 오탐(archive:527). → **모든 인쇄물·대본 일괄 교체 필요**
- **음성데이터 비저장**: 저장 안 함·응답 직후 폐기, 외부 AI(Anthropic/ElevenLabs) 텍스트 전송, 진행 시 동의 간주(동의문 + 구두 안내). 학과 가이드라인 부합 여부 **확인필요**(booth-plan:144)
- **차량 지하주차/캠**: 사전 녹화 주행영상이 기본, 라이브는 best-effort
- **위치 좌표**: 폰 GPS는 메모리(`location._state`)에만 보관·stale 300s 후 무효, 저장 없음. 단 위치 공유를 켤 경우 **무인증 수신 서버 노출**이 별도 리스크(M13).

### P0/P1/P2 매핑 (roadmap vs 구현)
| 우선 | 기능 | 계획 | 구현 상태 |
|---|---|---|---|
| **P0** | Wake→STT→Claude→TTS | 라이브 | ✅ 완료. warm ~3.4s |
| **P0** | 차량 데이터 | **mock 라이브**+Bluelink | ⚠ **드리프트**: 실 Hyundai만 구현, **MockVehicle 부재**. demo-script "42%/320km mock" 코드 불일치 |
| **P0** | 스케줄 조회/추천 | 라이브 | ✅ 완료 |
| P1 | 차량 브리핑 | 시간 남으면 | 미구현 |
| P1 | 차내 캠 라이브 | 녹화 주력 | 라이브 미검증, 녹화 폴백 의존 |
| P1 | 방문자 호출 모드 | exhibition 프로파일 | ⚠ **부분 드리프트**(아래) |
| P2 | 음악/유튜브 | 데모영상만 | 미구현 |
| P2 | 위치기반 검색 | 데모영상만 | ✅ **초과달성** — KakaoMap·Places 실구현 + **폰 GPS 실시간 좌표 폴백**(location_server)까지 라이브 가능 |

### ⚠ exhibition 프로파일: 설계 vs 실제 (중대 드리프트)
| 설계(roadmap:67-76) | 실제 구현 |
|---|---|
| `vehicle_backend: mock` | **미구현** — 실 Bluelink만 |
| `memory_file: 축약본` | ✅ 구현(다른 방식) — `OTTO_PROFILE=exhibition`이면 memory.local.md 미로드 + `[개인전용]` 줄 제거 |
| `write_intents_enabled: false` | **명시적 게이트 없음** — 단 allowed_tools가 읽기전용 Notion 5툴만이라 우회 차단 효과 |
| `history_reset_each_session: true` | **미구현**(grep 무매치) |
| `response_style: concise` | **미구현** — 단 voice는 구조적으로 항상 짧게 강제 |

→ **실제 `--profile exhibition`은 "민감 메모리 차단" 한 가지만 수행**(bot.py:537 배너 "전시 모드 — 민감정보 차단"). demo-script:55의 "쓰기 off+히스토리 리셋" 서술은 **현재 코드와 불일치** → **방문자 모드는 본인 발화 대행으로 한정하거나 세션 격리 직접 검증 후 운영.**

---

## 9. 리스크 레지스터 (전 영역 통합, severity 정렬, 중복 병합)

### 🔴 HIGH

| # | 리스크 | mitigation |
|---|--------|------------|
| H1 | **`--profile exhibition` 미적용 fail-open** — 기본값 personal(bot.py:529). config.yaml에 active_profile 키 없어 운영자 의존. 시연 머신에 memory.local.md 있으면 개인정보 노출 | 전시 기동 명령에 `OTTO_PROFILE=exhibition` 또는 `--profile exhibition` 강제. 부팅 배너 육안 확인을 체크리스트화. 시연 전 `memory.local.md` 부재 `ls` 확인(**현재 부재**) |
| H2 | **config.yaml `device:cuda` 커밋** — 노트북 CPU 폴백 시 STT 11~13s로 시연 불가. 전환 잊으면 무응답으로 보임 | **전시는 반드시 데스크탑 GPU 운영.** 노트북 폴백 시 `device:cpu`/`int8` 전환 체크리스트화(cuda_setup은 CPU no-op이라 충돌 없음) |
| H3 | **wake word 인쇄물/대본이 영어 "hey OTTO"** vs 실제 "크랭크 오토" — 방문자가 따라 부르면 wake 미감지 시연 실패 | 포스터·동의문·예시카드·demo-script "hey OTTO"→"크랭크 오토" 일괄 교체 후 재인쇄. 예시질문도 "크랭크 오토, …"로 통일 |
| H4 | **차량 시연 mock 전제 불일치** — demo-script "42%/320km mock"이나 코드는 실 Bluelink만. 지하주차·토큰만료·네트워크 시 비결정/실패 | 리허설에서 실 Bluelink 응답 실측·녹화. 실패 대비 사전녹화 영상 폴백. 또는 D-2 내 exhibition 프로파일에 간이 mock 추가 |
| H5 | **장소 환각 그대로 발화** — grounding이 관측 로그(`_log_place_grounding`)뿐, 차단 안 함. 전시장선 운영자가 [GROUND] 실시간 확인 불가 | 시연 질의를 **검증된 장소·일정으로 한정**(데모 스크립트 고정). 낯선 맛집 영업시간 등 위험 질의 회피. 여유 시 핵심 시나리오에만 최소 차단 적용 |
| H6 | **다중 봇 인스턴스 동시 실행**(archive:196) — 재기동 시 이전 프로세스 미종료 → 수신 분할 빈 transcript, GPU 경합 0.75s→15s, CUE 중복 | 기동 스크립트에 기존 python kill 선행 또는 단일 인스턴스 락. **운영 체크리스트 1번** |
| H7 | **공유 SSL 클라이언트 C레벨 하드 크래시**(`9388a38`) — try/except 무력, 봇 전체 종료 | **동시성(gather) 재도입 절대 금지**(순차 복원됨). 자동 재시작 watchdog 작동 확인. 불안정 시 `stream_final:false` 강등 |
| H8 | **집 데스크탑 원격 구동 6시간 무중단 실패** — 강의실 Wi-Fi/데스크탑 다운 시 전시 전체 중단 | 폰 핫스팟 폴백, 원격 재시작 경로 사전 점검, 데모영상 로컬저장. roadmap §5 "데스크탑 부스 반입" 대안 검토 |
| H9 | **회귀 전량 `--run`이 실 캘린더 write/delete** — calendar_write(14)/update_delete(10)이 실제 구글 캘린더 변경 | 데모 직전엔 읽기·라우팅 카테고리만 `--category` 표본 실행. write/delete는 테스트 캘린더 분리 |
| H10 | **Hyundai 토큰 만료** — 점검 시점 access_token 10.5h 만료. refresh_token까지 무효면 차량조회 [Vehicle error](P0) | **전시 전 get_vehicle_status 1회 실호출**로 자동갱신·DTE/Odometer 확인. 실패 시 tools/hyundai_auth.py 재발급 |

### 🟡 MEDIUM

| # | 리스크 | mitigation |
|---|--------|------------|
| M1 | **rate limit 429** — Tier 1 Sonnet 30,000 ITPM. 방문자 연속 툴 질의 몰리면 1분 내 초과. 유료 상향 안 함 | 본인 시연 위주, 방문자 간격. [USAGE] cache_r·in 모니터. 토큰 다이어트(툴5·6000캡·히스토리6) 유지. 즉석 $40 Tier2 결제수단 준비 |
| M2 | **캘린더 넓은범위 질의 지연·잘림** — event_id 비대(calendar.py:145)로 6000자 캡 truncation → 2~3 iteration 재조회. "올해 일정" 느리거나 부정확 | 시연을 좁은 범위(오늘/이번주)로 한정. 여유 시 read 줄 `[cid::id]`→`[id]` 슬림화(진단 완료, ~30분 작업) |
| M3 | **exhibition 프로파일 방문자 격리 미구현** — history_reset·write_intents 게이팅 코드 부재. 방문자 발화가 본인 세션에 누적/의도치 않은 쓰기 가능 | 운영 전 (1) allowed_tools 읽기전용 확인(충족), (2) 멀티유저 세션 격리 실검증, (3) 미흡 시 방문자 시연 본인 대행 한정 |
| M4 | **숫자 한글 풀어쓰기·주소 억제는 프롬프트 지시뿐**(코드 강제 아님) — 모델이 "450km" 그대로 출력 시 TTS 어색, 전체 주소 낭독 가능 | 리허설에서 DTE·장소 추천 질의 반복해 숫자/주소 낭독 회귀 점검. run_regression으로 voice 길이/형식 1회 |
| M5 | **`_FULL_KEYWORDS`("자세히"/"전부") 발화 시 상한 1200자 완화** — voice 길어져 TTS 수십 초 낭독, 시연 흐름 끊김 | 부스 안내로 짧은 질의 유도. 리허설에서 1200자 도달 시 실 TTS 시간 측정, 과하면 `_VOICE_MAX_CHARS_FULL` 하향 |
| M6 | **현대 차량 외부 장애/서버 500** — 실 API 의존(mock 미사용) | 전시 전날 1회 실호출. mock_vehicle 경로(설계 보존) 폴백 부활 검토. 데모영상 폴백 |
| M7 | **STT 환각·오탐**(archive:381) — 전시장 소음·배경음성이 캡처에 섞여 무의미/학습문구 환각 | no_speech_threshold 0.6·블랙리스트 동작 확인. 부스 마이크 사전 리허설. threshold 0.85 유지 |
| M8 | **test_orchestrator.py 스테일** — pytest 전체 수집이 import 단계 실패 | 삭제 또는 현행 API(run_voice_first/classify_intent) 재작성. 당장은 voice_streaming·tool_streaming 파일 단위 실행 |
| M9 | **stt_correction/format/hallucination_guard 32건 자동판정 불가** — 회귀 통과가 이 영역 품질 미보증 | 핵심 가드에 must_not_include("연료"/"%"/JSON 토큰) 추가 또는 사람이 utterances.md 해당 섹션 수동 검수 |
| M10 | **LLM 첫 토큰 ~1.9s = E2E ~55% 병목** — 네트워크/rate limit 변동 시 첫소리 지연 체감↑ | filler(잠시만/확인 중) 이미 구현(bot.py:379-386). tool 경로 티어1·2로 45~52%↓ |
| M11 | **전시일 06-09 변경, 준비물 마감은 옛 6/1 기준** — 영상 로컬저장·인쇄물·6시간 리허설 완료 여부 미확인 | 즉시 체크리스트로 완료 여부 확인, 미완은 06-08까지 마감 |
| M12 | **전시장 소음 STT가 방문자 시연 진짜 병목** | 헤드셋(소음격리)+Krisp, "또박또박" 안내카드, 실패 시 본인 대행 |
| M13 | **위치 서버 무인증 노출** — `location_server.py:79`가 `0.0.0.0:8765`에 인증 없이 바인딩. cloudflared https URL이 노출되면 외부에서 `POST /loc`로 봇의 "현재 위치"를 임의 주입 가능 → "근처/여기" 질의 오작동/오안내. 전시장 공용 Wi-Fi에서 더 위험 | **GPS 미사용 시 위치 공유 페이지 미배포(URL 미생성)로 노출 차단** — 서버는 떠 있어도 좌표 주입 입구가 외부에 안 알려지면 영향 없음. 사용 시 cloudflared **URL 비공개·임시 터널만** 쓰고 데모 직후 종료. (옵션) `/loc`에 간이 토큰 헤더 검사 추가 |

### 🟢 LOW

| # | 리스크 | mitigation |
|---|--------|------------|
| L1 | warm 의존성 — GPU cold 첫추론 ~23s(PTX JIT) | 부스 오픈 전 더미 발화 1회 warm-up |
| L2 | `_StreamingPCMAudio` queue 언더런 시 무음 → 끊김(stutter) | ffmpeg nobuffer+첫청크 대기로 완화. 끊김 시 네트워크 점검 |
| L3 | **폰 GPS 의존** — 위치공유 페이지 미가동/좌표 stale(>300s) 시 "근처" 질의가 지명 폴백(search_nearby)되거나 "현재 위치를 아직 못 받았어요…" 반환(get_directions). 입력원 부재가 아니라 **셋업 상시 가동 의존**이 본질 | 전시장 셋업에 폰 위치공유 페이지 가동을 **포함**하거나, GPS 미사용 전제로 **지명 포함 발화**("강남역 근처 주유소")로 동선 고정. 부팅 시 `location.status()`로 has_fix/fresh 확인을 체크리스트에 추가 |
| L4 | Kakao 길찾기 콘솔 사용설정·별도 키 의존, Brave/Places 월 한도 429 | 전시 전 get_directions·get_place_details 1회 실호출 확인 |
| L5 | stt-hints가 memory.md HTML 주석 안에 있어 편집 중 주석 깨면 STT 보정 조용히 사라짐 | memory.md 편집 후 STT initial_prompt에 과목명 포함 부팅 로그 확인 |
| L6 | otto_events.log 한글 모지바케(cp949) | 로깅 핸들러 UTF-8 고정. 진단은 TIMING/USAGE 영문 마커 위주 |
| L7 | utterances.md 미커밋(분실 위험) | 커밋해 인수인계 자료 포함 |
| L8 | 티어2 예외 시 complete 폴백 — voice 미방출이면 턴 중복 비용 | 불안정 시 `stream_final:false` 즉시 강등(안전장치 존재) |
| L9 | classify_intent 키워드+길이(<15) 휴리스틱 — trivial 오분류 시 tool 필요 발화가 툴 없는 경로로 빠져 답 못 함 | 데모 발화 사전 점검으로 충분 |
| L10 | 회귀 묶음 전시 직전 1회 미실행 | 전날 핵심 시나리오 부분집합 run_regression(test_orchestrator 제외) |

---

## 10. 미해결·보류 항목

### A. 전시 전 처리 가능 (D-2 판단 필요)
| 항목 | 작업량 | 영향 | 출처 |
|---|---|---|---|
| **인쇄물·대본 wake word 교체** ("hey OTTO"→"크랭크 오토") + 날짜(06-02→06-09) | 인쇄물 갱신 | 방문자 혼선 직접 차단 | booth-plan, demo-script 전반 |
| **캘린더 출력 슬림화** (`calendar.py:145` `[cid::ev_id]`→`[id]`, 이메일 제거 + truncation 예외) | ~30분 코드 | 일정 데모 품질·지연 직결 | archive:34-41 |
| **utterances.md 커밋** | 즉시 | 큐시트 버전관리 | git status |
| **Hyundai 토큰 실호출 확인** (자동갱신 검증) | 즉시 | P0 차량 기능 | vehicle.py:45-71 |
| **exhibition 간이 mock_vehicle 부활** (선택) | 설계 보존됨 | 차량 데모 결정성 | manual:967 |
| **회귀 표본 실행** (읽기·라우팅 카테고리) | 비용 일부 | tool 라우팅 회귀 감지 | manual:948 |
| **방문자 세션 격리 실검증 또는 본인 대행 한정 결정** | 검증/정책 | 방문자 모드 안전성 | roadmap:67-76 |
| **위치 데모 셋업 결정** — 폰 위치공유 페이지(cloudflared) 가동 포함 여부. 안 쓰면 미배포로 무인증 노출 차단(M13) | 정책/셋업 | "근처/여기" 동작 가부 + 보안 | location_server.py, kakao.py |

### B. 전시 후로 미룬 항목 (의식적 보류)
| 항목 | 사유 | 출처 |
|---|---|---|
| **히스토리 요약 압축** | 방문자별 짧은 대화라 영향 작다 판단(장시간 본인 연속 시 재발 여지) | manual:942, `398a522` |
| **grounding 자동 차단(옵션 B/C)** | "전시 후 데이터 보고 결정" | manual:944 |
| **set_demo_location**(세션 고정 좌표 명령) **만** 미구현 | **실주행 GPS는 폰 능동 전송(location_server) 방식으로 이미 구현 완료**(커밋 `b748913`, manual:963의 보류 서술보다 나중). 전시 고정위치를 코드로 박는 set_demo_location 명령만 안 만들었음 — 폰 위치공유 또는 지명 query로 대체 가능 | 현행 코드: location_server.py / location.py / kakao.py (manual:963은 설계 시점 보류 기록) |
| **카카오 추가 툴**(get_region/address_to_coord) | 실 GPS 시 재검토 | manual |
| **TTS 지연 최적화(④ffmpeg/⑥WS overlap)** | 코드 보존, voice 짧아 실이득 작아 미활용 | manual |
| **play_filler 호출 위치 / wake word 추가 모델** | 미결정 / 마이크 환경 필요 | manual |
| **test_orchestrator.py 정리** | 스테일, 우회 중(파일 단위 실행) | archive:303 |

---

## 11. 클로드 데스크탑을 위한 전시 플래닝 권고

### 당일 준비물 체크리스트
**장비**(booth-plan.md:36-44)
- [ ] 파워드 스피커(유선) — 공용 출력
- [ ] 헤드셋(마이크 포함) + 일회용 커버 — 방문자 입력
- [ ] 폰 거치대 — 입력폰 고정
- [ ] 멀티탭 — 콘센트 1개 분배
- [ ] 케이블 여분(오디오·충전)
- [ ] 보조배터리(차내캠 라이브 시도 시만)

**인쇄물** — ⚠ **전부 wake word·날짜 갱신 후 재출력**
- [ ] 포스터 A1(제목/동기/데이터흐름/기술스택/QR/음성미저장) — "크랭크 오토" 반영
- [ ] 동의 안내문(외부 API 전송 문구 학과 가이드 부합 확인)
- [ ] 방문자 예시카드 — "크랭크 오토, …" 형식 통일

**소프트/운영**
- [ ] **봇 기동 = `OTTO_PROFILE=exhibition` 강제** + 배너로 "전시 모드" 육안 확인
- [ ] **운영 데스크탑 GPU 확인**(config `device:cuda` 유지; 노트북이면 cpu/int8 전환)
- [ ] 봇 기동 전 **기존 python 프로세스 kill**(다중 인스턴스 방지)
- [ ] **부스 오픈 전 더미 발화 1회 warm-up**
- [ ] **Hyundai/Calendar 각 1회 실호출**로 토큰·연결 확인
- [ ] **위치 데모 켤 경우**: 폰에서 cloudflared https URL 위치 공유 페이지 열어 "✅ 위치 전송 중" 확인 + 부팅 로그 `location.status()` has_fix/fresh 확인. **안 켤 경우**: URL 미생성으로 무인증 노출 차단(M13)
- [ ] 데모영상 노트북 **로컬 저장**(인터넷 불필요)
- [ ] 폰 핫스팟 Wi-Fi 폴백 + 원격 재시작 경로
- [ ] 차내 캠 사전 녹화분(지하 통신 폴백)
- [ ] $40 Tier2 결제수단(429 비상 상향용)

### 권장 데모 흐름
1. **"되는 발화" 우선 동선**: 일정(오늘/이번주) → 차량 DTE → 일정+연료 멀티턴 추천 → 장소 검색 → 길찾기. **넓은 범위(올해/연간) 캘린더·낯선 맛집 영업시간은 회피.**
   - **위치 의존 발화**("근처 주유소", "여기서 OO까지")는 폰 위치공유를 켜둔 경우에만 좌표 기준으로 정확. **셋업이 불확실하면 지명 포함 발화**("강남역 근처 주유소")로 동선을 고정해 GPS 미수신 시에도 결정적으로 동작하게 한다.
2. **방문자 호출**: 화자독립 wake로 가능하나, 세션 격리 미구현이므로 **본인 발화 대행을 기본**으로. 직접 호출은 "또박또박" 안내 + 실패 시 즉시 본인 복구.
3. **멀티-tool 질의(28s 실측)는 시연 메인에서 제외** 또는 filler로 체감 완화.

### 폴백 트리
```
이상 발생
 ├─ wake 미감지 → "크랭크 오토" 재안내 / 본인 발화 복구
 ├─ STT 오인식(소음) → 또박또박 재발화 / 본인 대행
 ├─ 위치 미수신("근처/여기" 안내 멘트) → 폰 위치공유 페이지 재확인 / 지명 포함 발화로 전환
 ├─ 차량 응답 실패(토큰·지하) → 사전녹화 영상 폴백
 ├─ 봇 다운(크래시·SSL) → watchdog 자동재시작 / python kill 후 재기동
 ├─ rate limit 429 → 방문자 간격 ↑ / Tier2 상향 / 본인 시연만
 ├─ 데스크탑·Wi-Fi 두절 → 폰 핫스팟 → 그래도 안 되면
 └─ [모든 장애 공통] 10초 내 데모영상 무한루프 모드 후퇴 (설계된 경로)
```

### 의사결정이 필요한 Open Questions (전시 총괄 판단)
1. **운영 기기 확정** — 데스크탑 GPU(권장) vs 노트북 CPU? 후자면 config cpu/int8 전환 + STT 11~13s 감수. 두 기기 config 동기화/전환 절차가 명문화돼 있는가?
2. **캘린더 슬림화를 전시 전 적용할지** — ~30분 코드. 일정 데모를 넓은 범위로 보여줄 계획이 있는가?
3. **차량을 실 Bluelink 라이브로 갈지, mock 부활시킬지** — 외부 장애 시 데모 결정성 vs demo-script mock 전제 정합.
4. **방문자 모드를 실제로 켤지** — 세션 격리·쓰기차단 미구현. 켠다면 검증 필수, 아니면 본인 대행 한정.
5. **회귀 전량 --run 1회 돌릴 비용·시간 여유** — 없으면 데모 스크립트 경로만 선별 실행(write/delete 제외).
6. **rate limit Tier** — 전시 시점도 Tier1(30k ITPM)인가? 방문자 동시 호출 한도 정책 필요.
7. **동의문 외부 API 전송 문구** — 학과 가이드라인 부합 최종 확인됐는가?(booth-plan:144)
8. **준비물 실제 완료 여부** — 06-09로 변경 후 데모영상 로컬저장·인쇄물·6시간 리허설이 완료됐는가?(옛 6/1 마감)
9. **`config.yaml`에 `active_profile` 키 부재** — 전시 기동 시 OTTO_PROFILE 강제 메커니즘(run.bat/스크립트 고정 vs 수동)이 정립돼 있는가? fail-open 방지.
10. **위치(GPS) 데모를 켤지** — 켜면 "근처/여기" 좌표 기반 동작 가능하나 폰 위치공유 페이지 상시 가동 필요 + 무인증 수신 서버(M13) 노출 관리 필요. 안 켜면 지명 발화로 동선 고정 + 위치 공유 페이지 미배포로 노출 차단.

---

**핵심 결론**: 기술 파이프라인은 데모 가능 수준으로 완성됐다(GPU warm ~3.4s). 위치 기능도 폰 능동 전송 GPS 파이프라인까지 실구현돼 있어 "구조적 부재"는 사실이 아니다 — 남은 것은 셋업·보안 관리(폰 위치공유 가동 여부, 무인증 서버 노출 차단)다. 남은 일은 **코드가 아니라 운영 정합성** — `--profile exhibition` 강제·GPU 운영 고정·인쇄물 wake word 교체·좁은 범위 데모 동선·외부 토큰 사전 확인·위치 데모 켜기/끄기 결정·데모영상 폴백 확보다. 이것들을 D-1까지 닫으면 안정적 GO.

---
*이 보고서는 7개 영역 병렬 분석 → 종합 → 적대적 검증 → 최종화 과정으로 작성됨 (2026-06-07).*
