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
- **다음 작업**: Phase 6 — MCP 툴 통합 (Calendar/Notion 읽기) + Phase 6.5 차량 데이터 mock
- **개발 환경**: CPU-only 노트북 (GPU 이식 미완료 — 데스크탑 이식 필요)
- **전시 일정**: 2026-06-02 (D-5)

---

### ⚡ 다음 세션 시작 지점 (2026-05-28 이후)

**최우선 — GPU 이식 (밖에서는 불가, 데스크탑 복귀 시)**
`git clone` → `uv sync` → `.env` 복사 → `config.yaml` (`device: cuda`, `compute_type: int8_float16`) → `uv run bot.py` → "크랭크 오토" 테스트.
CPU에서 STT 11~13s → GPU 이식 시 1~2s 예상. 이식 없이는 실사용 불가.

**GPU 이식 후 — Phase 4+5 E2E 검증 필수 (현재 미검증)**
- Phase 4: Wake word → 발화 → Discord 채팅 채널 LLM 응답 게시 (마크다운 없음, 히스토리 동작)
- Phase 5: Wake word → 발화 → Discord 음성 채널 TTS 응답 (에코 방지, 세션 모드, cue 동작)
- E2E 검증 통과 후 Phase 6 진입.

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
