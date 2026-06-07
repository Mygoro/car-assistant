# 차량용 음성 AI 어시스턴트 — Claude Code 구현 매뉴얼

## 이 문서의 목적

이 문서는 Discord 봇 기반 차량용 음성 AI 어시스턴트를 단계별로 구현하는 행동 지침서다. 각 Phase는 독립적으로 완성되어야 하며, 다음 Phase로 넘어가기 전에 반드시 지정된 마일스톤을 만족해야 한다.

**구현하기 전에 이 문서 전체를 읽고 전체 아키텍처를 이해한 뒤 시작할 것.**

---

## 개발 환경 안내

현재 개발은 노트북(GPU 없음)에서 진행한다. faster-whisper는 CPU 모드(`device: "cpu"`, `compute_type: "int8"`)로 실행한다. CPU에서는 large-v3가 느리므로 개발 중 지연 측정은 의미 없고, 기능 동작 여부에만 집중한다.

> **⚠️ 데스크탑 이식 리마인더**
> 개발 완료 후 데스크탑(NVIDIA GPU 있음)으로 이식할 것.
> 이식 시 `config.yaml`에서 `device: "cpu"` → `"cuda"`, `compute_type: "int8"` → `"int8_float16"`으로 변경해야 STT 지연이 정상 수준으로 줄어든다.
> 이식 방법: `git clone` → `uv sync` → `.env` 작성 → config 수정 → `uv run bot.py`.

---

## 프로젝트 개요

### 시스템이 하는 일

사용자가 차에 타면 폰의 Discord 모바일 앱이 지정된 음성 채널에 자동 접속한다. 홈서버에서 돌아가는 Python Discord 봇이 같은 채널에서 사용자의 음성을 항시 수신한다. 봇은 한국어 wake word("야 클로드")를 감지할 때까지 오디오를 폐기한다. Wake word가 감지되면 이후 발화를 캡처하고, STT → LLM → TTS cascade 파이프라인을 통과시켜 Discord 음성 채널로 음성 응답을 돌려보낸다. 텍스트 응답은 같은 서버의 채팅 채널에 게시되어 영구 아카이브가 된다.

### 전체 데이터 흐름

```
폰 마이크
  → Discord 모바일 앱 (Opus 인코딩, Krisp 노이즈 억제)
  → Discord 서버 (외부 인프라)
  → 홈서버 Discord 봇 (음성 수신)
  → openwakeword 엔진 "hey otto" (항시 실행, CPU < 1%)
  → [wake word 감지 시] Silero VAD (발화 종료 감지)
  → faster-whisper STT (한국어 트랜스크립트)
  → 인텐트 분류기 (휴리스틱 우선)
  → LLM (Claude Sonnet 4.6, MCP 툴 포함)
  → ElevenLabs TTS Flash v2.5 (스트리밍)
  → Discord 음성 채널 송신 (ffmpeg → Opus)
  → Discord 채팅 채널 텍스트 게시 (아카이브)
  → JSONL 로컬 로그
```

### 핵심 제약 조건

- **wake word 이전에는 STT/LLM/TTS 어느 것도 호출하지 않는다.** Porcupine은 로컬에서 PCM을 처리하며 API 비용이 발생하지 않는다.
- **TTS 송신 중에는 wake word 감지를 일시 정지한다.** 봇 자신의 음성이 다시 트리거를 일으키는 에코 문제를 방지한다.
- **각 단계는 이전 단계 출력을 블로킹하지 않는다.** LLM 스트리밍 → TTS 스트리밍 → Discord 송신은 파이프라인으로 겹쳐서 실행한다.
- **아카이브 쓰기는 절대 오디오 경로를 블로킹하지 않는다.** `asyncio.create_task` fire-and-forget 패턴을 사용한다.
- **모든 민감한 값 (토큰, API 키)은 `.env` 파일에 저장한다.** 코드에 하드코딩하지 않는다.

---

## 환경 설정

### 요구 사항

- Python 3.11+
- `uv` 패키지 매니저 (기존 MCP 서버와 동일한 패턴)
- ffmpeg (시스템 PATH에 설치됨)
- 개발 중: CPU 모드로 실행 (GPU 없음)

### 프로젝트 구조

```
car-assistant/
├── pyproject.toml
├── .env                    # 절대 커밋하지 않음
├── .env.example            # 키 이름만 포함, 값은 비움
├── .gitignore
├── bot.py                  # 진입점
├── config.yaml             # 인텐트 라우팅, 파라미터
├── wake_word/
│   └── hey_claude_ko.ppn   # Picovoice Console에서 학습한 파일
├── fillers/                # 사전 녹음 필러 발화 MP3
│   ├── jamsiman.mp3
│   ├── hwagin_jung.mp3
│   └── chatgo_itda.mp3
├── core/
│   ├── audio_sink.py       # Discord 오디오 수신, Opus → PCM
│   ├── wake_word.py        # Porcupine 래퍼
│   ├── vad.py              # Silero VAD
│   ├── stt.py              # faster-whisper 래퍼
│   ├── orchestrator.py     # 인텐트 분류, LLM, MCP 툴 디스패치
│   ├── providers/
│   │   ├── base.py         # LLMProvider Protocol
│   │   ├── anthropic.py
│   │   ├── openai.py
│   │   └── ollama.py
│   ├── tts.py              # ElevenLabs 스트리밍 클라이언트
│   └── archive.py          # JSONL + Markdown 로그
└── archive/
    ├── sessions/           # YYYY-MM-DD.jsonl
    ├── daily/              # YYYY-MM-DD.md
    ├── artifacts/          # 생성된 산출물
    └── audio/              # 발화 opus 저장 (선택)
```

### pyproject.toml

```toml
[project]
name = "car-assistant"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "discord.py>=2.4.0",
    "discord-ext-voice-recv>=0.5.0",
    "pvporcupine>=4.0.0",
    "faster-whisper>=1.0.0",
    "onnxruntime>=1.18.0",
    "anthropic>=0.40.0",
    "openai>=1.50.0",
    "elevenlabs>=1.0.0",
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",
    "pyyaml>=6.0.0",
    "ulid-py>=1.1.0",
]
```

### .env.example

```
DISCORD_BOT_TOKEN=
DISCORD_GUILD_ID=
DISCORD_VOICE_CHANNEL_ID=
DISCORD_TEXT_CHANNEL_ID=
DISCORD_OWNER_USER_ID=
PICOVOICE_ACCESS_KEY=
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=
```

### config.yaml

```yaml
wake_word:
  model_path: "wake_word/hey_claude_ko.ppn"
  sensitivity: 0.5          # 0.0–1.0, 높을수록 민감 (오탐 증가)

stt:
  model_size: "large-v3"
  device: "cpu"             # 개발 중 CPU. 데스크탑 이식 시 "cuda"로 변경
  compute_type: "int8"      # 개발 중 CPU. 데스크탑 이식 시 "int8_float16"으로 변경
  language: "ko"
  initial_prompt: "디지툴, AI Agents, 연세대학교, LearnUs, Notion, Krita, MCP"

vad:
  threshold: 0.5
  tail_ms: 4000             # 4초 무음 감지 후 발화 종료 판정
  max_duration_s: 30        # 최대 캡처 길이

llm:
  default_provider: "anthropic"
  default_model: "claude-sonnet-4-6"
  max_tokens: 1000
  history_turns: 10

intent_routing:
  "note.create": "anthropic/claude-sonnet-4-6"
  "calendar.read": "anthropic/claude-haiku-4-5-20251001"
  "calendar.write": "anthropic/claude-sonnet-4-6"
  "research": "anthropic/claude-sonnet-4-6"
  "simple_qa": "anthropic/claude-haiku-4-5-20251001"
  "offline_fallback": "ollama/qwen2.5:14b"

tts:
  provider: "elevenlabs"
  model: "eleven_flash_v2_5"
  chunk_size: 1024

filler_threshold_ms: 800    # 이 이상 걸릴 것으로 예상되는 툴은 필러 먼저 송출
```

---

## Phase 0 — Discord 봇 기초

### 목표

봇이 시작 시 Discord 서버의 지정된 음성 채널에 자동 접속하고, 연결이 끊어졌을 때 자동으로 재접속한다.

### 구현 행동강령

**bot.py 구조:**

```python
import asyncio
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os

load_dotenv()

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
voice_client: discord.VoiceClient | None = None

@bot.event
async def on_ready():
    print(f"Bot ready: {bot.user}")
    voice_watchdog.start()

@tasks.loop(seconds=30)
async def voice_watchdog():
    guild = bot.get_guild(int(os.environ["DISCORD_GUILD_ID"]))
    channel = guild.get_channel(int(os.environ["DISCORD_VOICE_CHANNEL_ID"]))
    global voice_client
    if not voice_client or not voice_client.is_connected():
        voice_client = await channel.connect()
        print(f"Connected to voice channel: {channel.name}")

bot.run(os.environ["DISCORD_BOT_TOKEN"])
```

### 품질 검증

다음을 모두 확인한 뒤에만 Phase 1로 진행한다:

- [ ] 봇이 시작 시 음성 채널에 자동 접속한다
- [ ] Discord Developer Portal에서 봇을 수동으로 kick하면 30초 이내에 자동 재접속한다
- [ ] 봇이 구동 중인 상태에서 홈서버 인터넷이 잠깐 끊겼다 복구되면 재접속한다
- [ ] 폰의 Discord 모바일 앱에서 같은 음성 채널에 접속했을 때 봇 아이콘이 채널 멤버 목록에 보인다

### 흔한 실수

- Bot Token과 Application ID를 혼동하지 않는다. `.env`에 들어가는 것은 Bot Token이다.
- Discord Developer Portal → Bot → Privileged Gateway Intents에서 `Voice State` 인텐트를 활성화해야 한다.
- 봇을 서버에 초대할 때 OAuth2 URL에 `bot` + `applications.commands` scope와 `Connect`, `Speak`, `Use Voice Activity` 권한을 포함해야 한다.

---

## Phase 1 — 오디오 수신 및 저장

### 목표

봇이 음성 채널에서 본인 user_id의 오디오만 수신하고, Opus를 PCM 16kHz mono로 변환하여 큐에 쌓는다. 디버깅 목적으로 수신된 오디오를 WAV 파일로 저장한다.

### 구현 행동강령

**core/audio_sink.py:**

`discord-ext-voice-recv`의 `AudioSink`를 상속해 구현한다. 핵심 제약:

- `write(user, data)` 메서드는 동기 컨텍스트에서 호출된다. 이 안에서 `asyncio.run()` 또는 블로킹 I/O를 직접 호출하지 않는다.
- 오디오 청크를 `asyncio.Queue`에 넣는 방식으로 비동기 파이프라인에 전달한다. `loop.call_soon_threadsafe(queue.put_nowait, chunk)`를 사용한다.
- Opus → PCM 변환은 ffmpeg async subprocess로 처리한다. Discord가 전달하는 오디오는 Opus 48kHz stereo이며, Porcupine과 faster-whisper는 PCM 16kHz mono를 요구한다.

ffmpeg 변환 명령:
```
ffmpeg -f s16le -ar 48000 -ac 2 -i pipe:0
       -f s16le -ar 16000 -ac 1 pipe:1
```

**user_id 필터링:**

```python
OWNER_USER_ID = int(os.environ["DISCORD_OWNER_USER_ID"])

def write(self, user, data):
    if user is None or user.id != OWNER_USER_ID:
        return
    # 이하 처리
```

**WAV 디버깅 저장 (이 Phase에서만, 이후 제거):**

수신된 PCM 청크를 누적해서 5초마다 `debug_audio_{timestamp}.wav`로 저장한다. 저장 경로는 `archive/audio/debug/`.

### 품질 검증

- [ ] 폰에서 10초간 말한 뒤, `archive/audio/debug/`에 WAV 파일이 생성된다
- [ ] 생성된 WAV 파일을 PC에서 재생했을 때 본인 음성이 들린다 (잡음이 있어도 무관, 대화 내용이 들려야 함)
- [ ] 봇 콘솔에 `AUDIO_RECEIVED: {n_bytes} bytes` 로그가 초당 수십 회 출력된다

### 흔한 실수

- `discord-ext-voice-recv`는 `voice_client`에 `listen(sink)`를 호출해 등록한다. `connect()` 후 즉시 호출해야 한다.
- ffmpeg subprocess가 비정상 종료하면 조용히 실패한다. stderr를 로깅하고 프로세스가 죽으면 재시작하는 watchdog을 둔다.
- PCM 데이터는 bytes 타입이다. numpy array로 변환할 때 `np.frombuffer(data, dtype=np.int16)`을 사용한다.

---

## Phase 2 — Wake Word 게이트

> **구현 완료 (2026-05-23). 아래는 실제 구현 기준.**

### 목표

openwakeword가 들어오는 모든 PCM 청크를 검사하고, "크랭크 오토"가 감지되면 이후 파이프라인을 활성화한다. TTS 송신 중에는 감지를 일시 정지한다.

### wake word 선정 경위

처음에는 "hey otto"로 시작했으나 "헤이", "오토" 모두 한국어 일상 발화에서 흔한 단어여서 오탐이 심각했다. 15개 단일 화자 샘플로는 구성 음절과 전체 문장을 구별하는 결정 경계 학습이 불가능했다. threshold 0.90까지 상향해도 개선 미미. → **"크랭크 오토"로 피벗**: "크랭크"는 일상 대화에서 거의 사용되지 않고, 엔진 크랭킹 연상이 차량 AI 콘셉트와 부합.

### 구현 — core/wake_word.py

```python
from pathlib import Path
import numpy as np
from openwakeword.model import Model

CHUNK_SAMPLES = 1280   # 80ms at 16kHz
_CONFIRM_FRAMES = 1    # 연속 N 프레임 threshold 초과 시 감지 확정

class WakeWordDetector:
    def __init__(self, model_path: str, threshold: float = 0.85):
        self._model = Model(wakeword_models=[str(model_path)], inference_framework="onnx")
        self._threshold = threshold
        self._paused = False
        self._buffer = np.array([], dtype=np.int16)
        self._streak = 0

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False
        self._buffer = np.array([], dtype=np.int16)
        self._streak = 0

    def process(self, pcm_chunk: np.ndarray) -> bool:
        """pcm_chunk: int16 PCM (16kHz mono)"""
        if self._paused:
            return False
        self._buffer = np.concatenate([self._buffer, pcm_chunk])
        while len(self._buffer) >= CHUNK_SAMPLES:
            frame = self._buffer[:CHUNK_SAMPLES]
            self._buffer = self._buffer[CHUNK_SAMPLES:]
            prediction = self._model.predict(frame)
            score = max(prediction.values(), default=0.0)
            if score >= self._threshold:
                self._streak += 1
                if self._streak >= _CONFIRM_FRAMES:
                    self._model.reset()
                    self._buffer = np.array([], dtype=np.int16)
                    self._streak = 0
                    return True
            else:
                self._streak = 0
        return False
```

**중요: openwakeword는 int16 PCM을 입력받아야 한다.** float32([-1, 1]) 전달 시 mel spectrogram이 오디오를 무음으로 해석, 점수 0.0 고착.

### 커스텀 모델 학습 (`tools/train_wake_word.py`)

자체 MLP 학습 스크립트. openwakeword `AudioFeatures.__call__(int16)` 스트리밍 경로로 임베딩 추출 후 MLP 학습 → ONNX 내보내기. 긍정 샘플은 `tools/generate_tts_samples.py`로 ElevenLabs 다화자 TTS 생성.

```
uv run tools/generate_tts_samples.py   # positive 샘플 생성
!record positive                        # Discord 명령어로 실음성 추가 녹음
uv run tools/train_wake_word.py        # 학습 → wake_word/crank_otto.onnx
```

### 확정 설정값

```yaml
wake_word:
  model_path: "wake_word/crank_otto.onnx"
  threshold: 0.85     # CONFIRM_FRAMES=1 조합으로 안정적
```

### 품질 검증 결과 (완료)

- [x] "크랭크 오토"라고 말하면 봇 콘솔에 `WAKE WORD DETECTED` 로그 출력
- [x] Wake word 없이 일반 대화해도 미감지
- [x] TTS 송출 중 재트리거 없음 (`pause()/resume()` 작동 확인)

---

## Phase 3 — STT 통합

> **구현 완료 (2026-05-23). 아래는 실제 구현 기준.**

### 목표

Wake word 이후 발화를 캡처하고, Silero VAD로 발화 종료를 감지하고, faster-whisper로 한국어 트랜스크립트를 생성하고, Discord 채팅 채널에 게시한다.

### core/vad.py — 핵심 주의사항

**해당 silero_vad.onnx 모델은 8kHz 전용이다.** 16kHz 입력 시 모든 프레임이 ~0.001로 나와 무음 처리됨. 파이프라인 나머지는 16kHz 유지하고, VAD 내부에서만 다운샘플링.

```python
import audioop
import numpy as np
import onnxruntime as ort

class SileroVAD:
    def __init__(self, threshold: float = 0.3):
        self.session = ort.InferenceSession("silero_vad.onnx")
        self.threshold = threshold
        self._h = np.zeros((2, 1, 128), dtype=np.float32)  # v4: (2,1,128) 고정
        self._c = np.zeros((2, 1, 128), dtype=np.float32)
        self._sr = np.array(8000, dtype=np.int64)

    def is_speech(self, pcm_16k_chunk: np.ndarray) -> bool:
        """입력: int16 PCM 16kHz. 내부에서 8kHz로 다운샘플 후 모델 입력."""
        pcm_bytes = pcm_16k_chunk.tobytes()
        downsampled, _ = audioop.ratecv(pcm_bytes, 2, 1, 16000, 8000, None)
        audio = np.frombuffer(downsampled, dtype=np.int16).astype(np.float32) / 32768.0
        audio = audio[np.newaxis, :]
        out, self._h, self._c = self.session.run(
            None, {"input": audio, "sr": self._sr, "h": self._h, "c": self._c}
        )
        return float(out[0][0]) > self.threshold

    def reset(self):
        self._h = np.zeros((2, 1, 128), dtype=np.float32)
        self._c = np.zeros((2, 1, 128), dtype=np.float32)
```

### core/stt.py — hallucination 필터 포함

```python
from faster_whisper import WhisperModel
import numpy as np

_HALLUCINATION_BLACKLIST = [
    "자막 제공 및 광고를 포함하고 있습니다",
    "MBC 뉴스",  # 필요 시 확장
]

class STTEngine:
    def __init__(self, model_size, device, compute_type, language, initial_prompt):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.language = language
        self.initial_prompt = initial_prompt

    async def transcribe(self, pcm_16k_mono: np.ndarray) -> str:
        audio = pcm_16k_mono.astype(np.float32) / 32768.0
        import asyncio
        loop = asyncio.get_event_loop()

        def _run():
            segs, _ = self.model.transcribe(
                audio,
                language=self.language,
                initial_prompt=self.initial_prompt,
                beam_size=5,
                vad_filter=True,
                no_speech_threshold=0.6,           # 무음 세그먼트 자동 폐기
                condition_on_previous_text=False,  # 이전 컨텍스트 hallucination 전파 방지
            )
            return list(segs)

        segments = await loop.run_in_executor(None, _run)
        text = "".join(seg.text for seg in segments).strip()

        for pattern in _HALLUCINATION_BLACKLIST:
            if pattern in text:
                return ""
        return text
```

### 발화 캡처 아키텍처 — capture_queue 분리

`pcm_queue`(전체 오디오 스트림)와 `capture_queue`(LISTENING 상태 전용)를 분리. 두 코루틴이 동일 큐를 경쟁 소비하면 청크가 번갈아 분배되어 VAD가 불연속 오디오를 받는 문제 방지.

```
audio_processor():
    chunk = await pcm_queue.get()
    wake_detector.process(chunk)          # 항상 실행
    if state == LISTENING:
        capture_queue.put_nowait(chunk)   # 캡처 큐로만 라우팅

_capture_and_transcribe():
    MIN_SPEECH = 5   # 연속 5프레임(160ms) 이상 speech 판정 시에만 발화 시작으로 인정
    speech_started = False
    pre_speech_buffer = deque(maxlen=pre_speech_limit)
    capture_buffer = []
    silent_frames = 0

    while True:
        chunk = await capture_queue.get()
        is_speech = vad.is_speech(chunk)

        if not speech_started:
            pre_speech_buffer.append(chunk)
            if is_speech:
                speech_count += 1
                if speech_count >= MIN_SPEECH:
                    speech_started = True
                    capture_buffer = list(pre_speech_buffer)
        else:
            capture_buffer.append(chunk)
            if not is_speech:
                silent_frames += 1
            else:
                silent_frames = 0

            if silent_frames >= tail_frames or elapsed >= max_duration_s:
                break

    transcript = await stt.transcribe(np.concatenate(capture_buffer))
```

### 확정 설정값

```yaml
vad:
  threshold: 0.3      # Discord 압축 오디오에서 낮은 임계값 필요
  tail_ms: 1500       # Phase 5에서 단축 (3000 → 1500). 세션 모드에서 첫 턴 1.5s, 이후 3.0s 동적
  max_duration_s: 30
```

### 품질 검증 결과 (완료, CPU 한정)

- [x] Wake word → 발화 → 채팅 채널 트랜스크립트 게시
- [x] 3s 침묵 → 발화 종료 판정
- [x] 30s max_duration 자동 종료
- [x] 긴 복잡한 텍스트 정확도 통과 (한국어 게임 카드 텍스트)
- [ ] GPU 환경 E2E 검증 미완료 (CPU에서 42s 소요 → GPU 이식 후 재확인)

---

## Phase 4 — LLM 텍스트 응답

> **구현 완료 (2026-05-26). 아래는 실제 구현 기준.**

### 목표

트랜스크립트를 LLM에 보내고 텍스트 응답을 받아 Discord 채팅 채널에 게시한다.

### dual-response JSON 포맷

LLM은 단일 응답에서 `voice_response`(TTS용, 50~100자, 마크다운 금지)와 `text_response`(Discord 채팅용, 길이 무제한, 마크다운 허용)를 동시에 반환한다. 시스템 프롬프트는 `core/system_prompt_template.txt`에 저장하고 `{MEMORY_MD_INJECTION_POINT}`로 `core/memory.md` 내용을 주입.

```json
{
  "voice_response": "오늘 오후 2시에 AI Agents 수업 있어요.",
  "text_response": "## 오늘 일정\n- 14:00 AI Agents 강의 (공학관 201호)\n- 노션 글쓰기 과제 마감 오늘"
}
```

### 인텐트 분류 — 3-tier

```python
def classify_intent(transcript: str) -> str:
    t = transcript.strip()
    if any(p in t for p in ["몇 시", "지금 시각", "안녕", "하이", "고마워"]) and len(t) < 15:
        return "trivial"          # → Haiku
    if any(kw in t for kw in ["깊이 생각", "자세히 분석", "꼼꼼히"]):
        return "complex_reasoning"  # → Opus
    return "default"              # → Sonnet
```

5-tier(`note.create / calendar.read / calendar.write / research / simple_qa`)는 MCP 툴이 없는 단계에서 의미 없어 3-tier로 단순화. Phase 6에서 툴 기반 라우팅으로 확장 예정.

### voice-first 스트리밍 — Orchestrator.run_voice_first()

`voice_response` 완성 즉시 TTS Task를 시작하고, `text_response`는 병렬로 계속 생성. 전체 응답 완료를 기다릴 필요 없음.

```python
async def run_voice_first(self, transcript: str):
    # voice_response 완성 즉시 yield ("voice", text)
    # text_response 완성 후 yield ("text", text)
```

### 시스템 프롬프트 캐싱

`core/providers/anthropic.py`에서 시스템 프롬프트에 `cache_control: {"type": "ephemeral"}` 적용. 매 턴 프롬프트 전체 재전송 비용 절감.

### 확정 설정값

```yaml
llm:
  default_model: "claude-sonnet-4-6"
  max_tokens: 1000
  history_turns: 10

intent_routing:
  "default": "anthropic/claude-sonnet-4-6"
  "trivial": "anthropic/claude-haiku-4-5"
  "complex_reasoning": "anthropic/claude-opus-4-7"
  "offline_fallback": "ollama/qwen2.5:14b"
```

### 품질 검증 결과

- [x] `chat_test.py` CLI로 dual-response JSON 정상 파싱 확인 (6개 시나리오)
- [x] 응답에 마크다운 형식 없음
- [x] 히스토리 동작 확인 (스텁 기반 단위 테스트 18개 통과)
- [x] Wake word → STT → LLM E2E 검증 완료 (2026-05-27 실 테스트)

---

## Phase 5 — TTS 음성 출력

> **구현 완료 (2026-05-27~28). 아래는 실제 구현 기준.**

### 목표

LLM 텍스트 응답을 ElevenLabs로 스트리밍 변환하고 Discord 음성 채널로 송출한다.

### TTS 진짜 스트리밍 — _StreamingPCMAudio

ElevenLabs MP3 전체 수신 후 재생하면 첫 소리까지 7~10s 소요. `_StreamingPCMAudio` 클래스로 ffmpeg PCM 생산(async)과 Discord 오디오 스레드 소비를 `queue.Queue`로 브릿지. 첫 PCM 청크 도착 즉시 `voice_client.play()` 호출.

```python
import queue
import discord

class _StreamingPCMAudio(discord.AudioSource):
    def __init__(self):
        self._q: queue.Queue[bytes | None] = queue.Queue()

    def push(self, data: bytes):
        self._q.put(data)

    def finish(self):
        self._q.put(None)  # sentinel

    def read(self) -> bytes:
        try:
            chunk = self._q.get(timeout=0.02)
            if chunk is None:
                return b""
            return chunk
        except queue.Empty:
            return b"\x00" * 3840  # 무음 반환으로 재생 끊김 방지

    def is_opus(self) -> bool:
        return False
```

`speak()` 내부에서 `_feed_mp3` Task(ElevenLabs→ffmpeg stdin)와 `_read_pcm` Task(ffmpeg stdout→source.push)를 병렬 실행. 첫 청크 도착 즉시 `voice_client.play(source)` 호출.

**실측 타이밍 (CPU 노트북 기준):**
- TTS 첫음절: 0.72s (ElevenLabs 요청 후)
- LLM→voice_response: 2.8s
- 말 멈춤→첫 소리: ~16s (GPU 이식 후 ~5~6s 목표)

### 세션 모드

wake word 1회로 세션을 열고 여러 턴 연속 대화 후 명시적 종료 또는 무응답으로 닫는다.

```
IDLE → (wake word) → [enter cue] → LISTENING(첫 턴 1.5s tail)
  → (발화) → STT → LLM → TTS → [enter cue] → LISTENING(이후 턴 3.0s tail)
  → ("슬립 오토" or 무응답 3s) → [quit cue] → IDLE
```

종료 키워드: `"슬립 오토"`, `"sleep otto"` — STT 결과 문자열 매칭으로 LLM 호출 없이 즉시 처리.

### 효과음 cue 시스템

```
cues/otto_enter.mp3  # Otto enter.mp3에서 0~0.905s 추출 (ffmpeg atrim+afade)
cues/otto_quit.mp3   # Otto quit.mp3에서 ch1 2.905~6.538s 추출 (ffprobe 챕터 기준)
```

**재생 순서 (직렬화):**
```python
await play_cue(CUE_ENTER)           # cue 완료 후
asyncio.create_task(_capture(...))  # 캡처 시작 (동시 아님)
```
cue와 캡처를 동시에 `create_task`로 시작하면 cue 재생 중 tail 타임아웃이 소모된다.

### 필러 발화 (`play_filler()`)

구현 완료, 호출 위치 미연결. Phase 6 MCP 툴 연동 시 연결 예정.

```python
FILLER_MAP = {
    "searching": "fillers/chatgo_itda.mp3",
    "confirming": "fillers/hwagin_jung.mp3",
    "default": "fillers/jamsiman.mp3",
}
```

`fillers/` 폴더 현재 비어있음 → `uv run tools/generate_tts_samples.py` 실행 필요.

### 확정 설정값

```yaml
tts:
  provider: "elevenlabs"
  model: "eleven_flash_v2_5"
  chunk_size: 1024

vad:
  tail_ms: 1500   # 첫 턴. 이후 턴은 bot.py에서 3000ms로 동적 전환
```

### 품질 검증 결과

- [x] `speak_local()`로 로컬 스피커 TTS 출력 확인
- [x] TTS 첫음절 0.72s (스트리밍 구현 후 실측)
- [x] quit cue 무음 버그 수정 (챕터 메타데이터 기반 재추출)
- [x] Discord 음성 채널 E2E 검증 완료 (2026-05-27 실 테스트)
- [x] 에코 방지 실제 동작 확인 (재트리거 없음)
- [x] 세션 모드 완료: wake → 연속 대화 → "슬립 오토" → IDLE 복귀
- [x] GPU 환경 재검증 (2026-06-03, RTX 5070 Ti) — STT 0.75s, 발화끝→첫소리 ~5.2s (CPU ~26s)

### GPU 이식 (Windows / Blackwell) — cuda_setup

faster-whisper(CTranslate2)는 Windows에서 cublas64_12.dll / cudnn64_9.dll / cudart64_12.dll을
런타임 LoadLibrary로 찾는데 시스템 PATH에 없어 추론이 실패한다. `core/cuda_setup.py`가
nvidia pip 패키지(`nvidia-cublas-cu12`, `nvidia-cudnn-cu12`, `nvidia-cuda-runtime-cu12`)의
bin 경로를 PATH + `os.add_dll_directory`에 등록한다. `stt.py`가 `faster_whisper` import 전에
`cuda_setup.setup()`을 호출한다(Windows 아니거나 미설치 시 no-op).

신규 기기 셋업 시 1회 자동 조달: `silero_vad.onnx`(vad.py 자동 다운로드),
openwakeword base 모델(`uv run python -c "import openwakeword.utils as u; u.download_models()"`).

### TTS 지연 최적화 (2026-06-03)

**④ 첫 바이트 단축:**
- ElevenLabs stream URL에 `?optimize_streaming_latency=3`
- ffmpeg: `-f mp3`(포맷 탐지 probe 생략) + `-analyzeduration 0` + `-probesize 32` + `-fflags nobuffer`
- `speak()`의 ffmpeg→PCM→Discord 브릿지를 `_play_mp3_stream` 헬퍼로 추출(HTTP/WS 공용)

**⑥ WebSocket overlap (LLM↔TTS 병렬):**
- `ElevenLabsTTS.stream_ws(text_aiter)` — stream-input WS. 텍스트 청크를 받는 즉시 송신하고
  생성되는 MP3를 yield. `speak_streaming()`이 `_play_mp3_stream`으로 재생.
- `Orchestrator.run_voice_streaming()` — 스트리밍 중 voice_response 값을 부분 디코딩해 토큰
  단위로 방출(`voice_chunk`/`voice_end`/`text`). `_find_value_end`(이스케이프 인지 닫는 따옴표
  탐색) + `_decode_partial`(끝에서 잘라 파싱 가능한 최대 prefix).
- `bot._run_llm` — asyncio.Queue로 voice 토큰을 `speak_streaming`에 흘림. 첫 voice 토큰 즉시
  TTS 시작.
- 한계: `chunk_length_schedule=[50]`(최소)이라 overlap 실이득은 50자 초과 응답에서 크다.
  짧은 응답은 HTTP와 대체로 동등(회귀 없음).

검증: `tests/test_voice_streaming.py`(파서 단위) + `tests/verify_tts_live.py`(라이브).

---

## Phase 6 — MCP 툴 통합

### 목표

기존 MCP 서버(Notion, Google Calendar, Google Drive, Gmail, Brave Search)를 봇에서 호출한다. 툴 호출 전 필러 발화를 송출한다. 툴 결과를 아카이브에 기록한다.

### 구현 행동강령

**MCP 클라이언트 패턴:**

봇은 MCP 클라이언트로 작동한다. Anthropic API에 `mcp_servers` 파라미터를 직접 전달하지 않는다. 대신 봇이 직접 MCP 서버 프로세스를 띄우고 stdio로 통신하며, 툴 호출 결과를 봇이 받아서 Claude에게 tool_result로 돌려준다. 이 방식이 아카이브 훅 삽입과 필러 발화 제어를 가능하게 한다.

FastMCP 클라이언트 모드를 사용:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def call_tool(server_command: list[str], tool_name: str, arguments: dict):
    server_params = StdioServerParameters(
        command=server_command[0], args=server_command[1:]
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result
```

실제 구현에서는 서버를 매 툴 호출마다 새로 시작하지 않고 장기 실행 세션을 유지한다. 서버별 `ClientSession`을 봇 시작 시 초기화하고 전역으로 유지한다.

**툴 호출 흐름:**

```
LLM 응답에 tool_use 블록이 포함됨
  → 필러 발화 송출 (예상 시간 > filler_threshold_ms)
  → MCP 서버에 툴 호출
  → 결과를 tool_result 메시지로 LLM에 재전달
  → LLM이 최종 응답 생성
  → TTS → 음성 송출
  → 아카이브에 툴 호출 기록
```

**MCP 서버 설정 (config.yaml 추가):**

```yaml
mcp_servers:
  notion:
    command: ["uv", "run", "--directory", "/path/to/notion-mcp", "server.py"]
  google_calendar:
    command: ["node", "/path/to/calendar-mcp/index.js"]
  brave_search:
    command: ["npx", "-y", "@modelcontextprotocol/server-brave-search"]
    env:
      BRAVE_API_KEY: "${BRAVE_API_KEY}"
```

### 품질 검증

- [ ] "내일 일정 알려줘"라고 말하면 Google Calendar에서 실제 일정을 읽어 답한다
- [ ] "메모해줘 — [내용]"이라고 말하면 Notion에 실제 페이지가 생성된다
- [ ] 툴 호출 전 필러 발화가 먼저 재생된다
- [ ] 툴 호출이 실패하면 봇이 에러를 음성으로 알린다 ("캘린더 연결에 문제가 생겼어요")
- [ ] 툴 호출 결과가 JSONL 로그에 기록된다

---

## Phase 6.5 — 차량 데이터 (신규)

> **설계 완료 (exhibition/roadmap.md). 미구현.**

### 목표

차량 상태(연료, 주행거리, 위치)를 조회해 음성으로 답한다. mock이 기본 경로, Bluelink 실연동은 best-effort.

### core/vehicle.py

```python
from typing import Protocol

class VehicleBackend(Protocol):
    async def get_status(self) -> dict:
        """{"fuel_pct": 42, "range_km": 320, "location": "연세대학교 인근", "odometer_km": 38200}"""
        ...

class MockVehicle:
    """config.yaml에서 값 주입. 데모 결정성 확보."""
    def __init__(self, cfg: dict):
        self._data = cfg.get("mock_vehicle", {})

    async def get_status(self) -> dict:
        return self._data

class BluelinkVehicle:
    """공식 Hyundai Developers Portal OAuth 2.0 경로."""
    # docs/hyundai-api-survey.md 참조
    # 가용 API: status_dte(잔여 주행거리), 운행정보, 주행거리, 차량상태
    # 비공식 라이브러리(hyundai_kia_connect_api)는 한국 Region 미지원(Issue #701)
    # → 공식 포털 REST API 직접 호출
```

### config.yaml 추가

```yaml
active_profile: personal   # --profile 인자로 덮어쓰기

profiles:
  personal:
    vehicle_backend: "bluelink"
  exhibition:
    vehicle_backend: "mock"

mock_vehicle:
  fuel_pct: 42
  range_km: 320
  location: "연세대학교 인근"
  odometer_km: 38200
```

### 지도 API (카카오맵 + Tmap)

GPS 좌표 → 자연어 주소 변환, 주변 주유소 검색에 사용. docs/map-api-survey.md 참조.

```python
# 역지오코딩: GPS → 주소
GET https://dapi.kakao.com/v2/local/geo/coord2address.json
  headers: {"Authorization": f"KakaoAK {REST_API_KEY}"}
  params: {"x": lon, "y": lat}

# 주변 주유소 검색
GET https://dapi.kakao.com/v2/local/search/category.json
  params: {"category_group_code": "OL7", "x": lon, "y": lat, "radius": 5000}
```

### 오케스트레이터 연동

`get_vehicle_status`를 Claude 툴로 등록. 인텐트 분류기에 `vehicle.query` 추가:
키워드: `기름`, `연료`, `주유`, `위치`, `어디`, `주행거리`, `킬로`.

### 품질 검증 (목표)

- [ ] "기름 얼마나 남았어?" → mock: "현재 연료 42%, 약 320km 주행 가능"
- [ ] exhibition 프로파일에서 mock 응답이 config 값과 일치
- [ ] personal 프로파일에서 Bluelink 실데이터 조회 (best-effort)

---

## Phase 7 — 컨텍스트 오케스트레이션 & 페르소나 (신규)

> **배경**: 원래 매뉴얼엔 없던 단계. Phase 6 E2E에서 "기능은 되는데, 일반적인 답만
> 하고 맥락이 없다"는 한계가 드러나 신설했다. 예: 차량 잔여 주행거리가 곧 주유해야 할
> 수준인데도 주유소 5개를 나열만 할 뿐 무엇을 왜 추천하는지 특화된 판단이 없었다(구
> 이슈 5). 또 사용자 정보(차량·자주 가는 곳·말투)를 매
> 세션 다시 알려줘야 했다. 이 단계는 **새 코드보다 컨텍스트·프롬프트 설계**가 핵심이다.

### 목표

봇이 매번 묻지 않아도 사용자를 알고, 질문이 오면 **어떤 소스를 어떤 순서로 쓸지
스스로 판단**해 맥락 있는 답을 내도록 한다. 메인 오케스트레이션 프롬프트를 설계한다.

### 구성 요소

1. **`core/memory.md` 확장 — 상시 주입되는 사용자 컨텍스트**
   - 사용자 프로필: 차량(아반떼), 자주 가는 목적지, 반복 맥락(통학 동선 등),
     선호. 매 세션 다시 입력하지 않게 한다. **사적·인간관계 맥락은 넣지 않는다(기능적만).**
   - 페르소나·어투: 답변 톤, 호칭, 길이 감각. 예상 FAQ와 모범 답변 어투 교정.
2. **소스 라우팅 판단원칙 — 프롬프트에 명문화**
   - 개인정보·일정·메모 → 노션 / Google Calendar
   - 장소 위치·거리·길찾기 → 카카오(search_nearby_places, get_directions)
   - 영업시간·평점·리뷰·가격 → Google Places(get_place_details)
   - 일반·최신 정보 → web_search(Brave), 의도당 1~2회
   - 차량 상태 → Hyundai(get_vehicle_status)
   - **복합 질의는 순서대로 조합**하고, 무엇을 먼저 볼지 판단 기준을 명시한다.
3. **맥락 통합(구 이슈 5)** — 앞선 도구 결과를 후속 검색·추천에 반영.
   복합 맥락(예: 곧 주유 필요 + 식사) → 장소 추천 시 동선·소요시간 고려. 단순 나열이
   아니라 "그중 무엇을 왜 추천하는지"를 답하게 한다. 주관적 근거(분위기 등)는 툴 결과로
   뒷받침하고, 없으면 단정하지 않는다.

### 품질 검증 — **완료 (2026-06-07, 실대화 로그 검증)**

- [x] 사용자 차량·소속·자주 가는 곳을 다시 알려주지 않아도 답에 반영된다 (로그: 아반떼 인지 등)
- [x] 같은 질문에 소스 선택이 일관된다(영업시간은 Places, 위치는 카카오 등)
- [x] 복합 질의("기름 넣고 밥 먹게 근처 추천")에서 차량+장소+상세를 순서대로 조합한다
- [x] 멀티턴 carry-over("거기 영업시간?")가 직전 장소를 유지한다
- [~] 여러 후보를 나열하지 않고 무엇을 왜 추천하는지 판단한다 — 로그상 구조(평점·리뷰 수집,
  인용 비율↓)는 확인. 응답 문구 레벨의 빡센 검증은 Phase 8 품질 하드닝으로 이월.
- **범위 조정**: 데이트·사적/인간관계 맥락 특화 추천은 의도적으로 제외(전시용·사용자 요청).
  [[no-personal-context-in-assistant]]

---

## Phase 8 — 품질 하드닝 (신규)

> **배경**: Phase 7까지 기능과 맥락이 어느 정도 갖춰지면, 그때 품질을 **빡세게 다시
> 돌리는** 단계. 에이닷 개발기에서 지적됐지만 아직 프롬프트 1차 방어에 그친 항목들을
> 코드 레벨로 끌어올리고, 전체 시나리오를 회귀 검증한다. "되네"가 아니라 "안 깨지네"를
> 기준으로 한다.

### 처리 항목 (에이닷 잔여 과제 + 누적 품질 부채)

> **현황(2026-06-07)**: 데모 직결 항목(2·3·4·5)은 반영 완료. 1(히스토리 압축)만 미완이며
> 전시는 방문자별 짧은 대화라 영향이 작아 **전시 후로 보류**. 이번 세션엔 추가로 JSON parse
> 견고화(prose 흡수), voice 길이 컷 해제("전부/길게" 시 구어체로 전부)도 반영됐다.

1. **히스토리 요약 압축** — ⏸ **전시 후.** 긴 세션 토큰·환각 대비. 전시 짧은 대화엔 불필요.
2. **tool 결과 코드 검증층** — ✅ grounding **관측 로그**(`[GROUND]`, 옵션 A) 반영. 차단이
   아닌 가시화(오탐이 데모를 망치는 것 방지). 자동 차단(B/C)은 전시 후 데이터 보고 결정.
3. **STT 2차 보정** — ✅ `memory.md`의 `stt-hints` 고유명사를 Whisper `initial_prompt`에 병합.
4. **모호한 발화의 맥락 명확화** — ✅ 프롬프트 `Ambiguous reference` 규칙(직전 맥락 해소).
5. **회귀 테스트 + 품질 기준** — ✅ 238 케이스(`tests/regression_cases.yaml`) + 러너
   (`tools/run_regression.py`). 전체 `--run`은 비용 커 전시 직전 1회 권장.

### 품질 검증

- [~] 긴 세션(20+ 턴) 토큰 폭주 방지 — 히스토리 압축 미구현(전시 후)
- [x] API에 없는 장소를 답하면 `[GROUND]` 로그로 가시화(차단은 아님)
- [x] 자주 쓰는 고유명사가 STT 단계에서 인식되도록 주입
- [x] 핵심 시나리오 회귀 묶음 구축(전시 직전 전체 실행 1회 권장)

---

## 보류 항목 (Deferred — 환경·우선순위로 미룬 것)

> 다음 단계로 넘기며 명시적으로 미뤄둔 것들. 잊지 않기 위한 목록.

- **실주행 GPS** — 폰이 좌표를 능동 전송해야 함(브라우저 Geolocation 페이지 + HTTPS
  터널). 전시는 고정 위치라 불필요. 실사용 단계에서 별도 진행.
- **`set_demo_location`** — "현재 위치를 강남역으로" 식 세션 기본 좌표. 지명을 query에
  넣으면 좌표 없이도 검색되므로 필수 아님.
- **카카오 추가 툴** — `get_region`(좌표→행정구역), `address_to_coord`, 카테고리 검색.
  실 GPS가 생기면 재검토.
- **mock_vehicle / profiles** — Phase 6.5에 설계했으나 Hyundai 실연동으로 갔다. 전시
  결정성이 필요하면 mock 경로를 되살린다.
- **TTS 지연 최적화(④ ffmpeg / ⑥ WebSocket overlap)** — 코드는 보존돼 있으나
  voice-first 경로에서 voice_response가 짧아 실이득이 작아 미활용.
- **`play_filler` 호출 위치** — 툴 호출 대기 중 필러 발화. 연결 위치 미결정.
- **wake word 추가 모델** — 대체 호출어 학습(마이크 환경 필요).

---

## 부록 A — 운영 아카이브 (구 Phase 7, otto_events.log로 실질 구현)

> **상태**: 원래 "Phase 7 — 아카이브"로 계획했으나, 실제로는 `otto_events.log` 파일
> 핸들러 + Discord 텍스트 채널 게시로 핵심이 이미 구현됐다. 아래는 원 설계 기록(참고용).
> 새 로드맵의 Phase 7/8은 위로 이동했다.

### 목표

모든 턴을 JSONL로 기록하고 Discord 채팅 채널에도 게시한다. 야간 Markdown 요약을 생성한다.

### 구현 행동강령

**core/archive.py:**

아카이브 라이터는 별도 asyncio Task로 실행된다. 오디오 파이프라인과 같은 이벤트 루프에서 돌지만, 쓰기 작업은 큐를 통해 비동기로 처리한다.

```python
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

class ArchiveWriter:
    def __init__(self, base_path: str = "archive"):
        self.base = Path(base_path)
        self._queue: asyncio.Queue = asyncio.Queue()
        self._task: asyncio.Task | None = None

    def start(self):
        self._task = asyncio.create_task(self._writer_loop())

    async def log(self, record: dict):
        await self._queue.put(record)  # non-blocking

    async def _writer_loop(self):
        while True:
            record = await self._queue.get()
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            path = self.base / "sessions" / f"{date_str}.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
```

**JSONL 스키마:**

```json
{
  "timestamp": "2026-05-11T14:32:18+09:00",
  "interaction_id": "01HX2R...",
  "session_id": "drive-20260511-1430",
  "context": {
    "discord_channel_id": "1234567890",
    "discord_message_id": "9876543210"
  },
  "user_input": {
    "transcript": "오늘 기독교 강의 핵심 메모해줘",
    "stt_latency_ms": 380
  },
  "intent": {
    "label": "note.create",
    "router": "heuristic"
  },
  "llm": {
    "provider": "anthropic",
    "model": "claude-sonnet-4-6",
    "input_tokens": 1820,
    "output_tokens": 142,
    "ttft_ms": 620
  },
  "tools_called": [
    {
      "name": "notion-create-pages",
      "duration_ms": 750,
      "ok": true
    }
  ],
  "response": {
    "text": "노션에 기록했어요.",
    "tts_characters": 9,
    "tts_ttfb_ms": 310
  },
  "totals": {
    "voice_to_voice_ms": 1990,
    "estimated_cost_usd": 0.0044
  }
}
```

**일일 요약 (야간 task):**

```python
from discord.ext import tasks
import datetime

@tasks.loop(time=datetime.time(hour=3, minute=0))
async def daily_summary():
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    jsonl_path = Path(f"archive/sessions/{yesterday}.jsonl")
    if not jsonl_path.exists():
        return
    records = [json.loads(l) for l in jsonl_path.read_text().splitlines() if l.strip()]
    prompt = (
        f"다음은 {yesterday}의 음성 어시스턴트 대화 로그입니다. "
        f"주요 활동, 생성된 노트, 처리된 일정을 중심으로 마크다운 형식의 일일 요약을 작성해주세요.\n\n"
        f"{json.dumps(records, ensure_ascii=False)}"
    )
    # Claude에게 요약 요청 후 archive/daily/{yesterday}.md에 저장
```

### 품질 검증

- [ ] 하루치 대화가 `archive/sessions/YYYY-MM-DD.jsonl`에 한 줄씩 기록된다
- [ ] 각 JSONL 줄이 valid JSON이다 (`python -m json.tool`로 확인)
- [ ] 봇이 말하는 중에 아카이브 쓰기가 음성 출력을 지연시키지 않는다
- [ ] 다음날 새벽 3시에 전날 Markdown 요약이 생성된다

---

## 부록 B — 폴백·안정화 (구 Phase 8, 부분 반영)

> **상태**: 원래 "Phase 8 — 폴백 및 안정화"로 계획. 오프라인 폴백은 `intent_routing`의
> `offline_fallback`(ollama)으로 일부 반영됐고, 에러 알림은 각 툴의 예외 처리로 부분
> 구현됐다. 상시 과제로 남긴다. 새 로드맵의 Phase 8(품질 하드닝)은 위로 이동했다.

### 목표

인터넷이 없을 때 로컬 Qwen으로 폴백하고, 에러 상황에서 봇이 조용히 죽지 않고 사용자에게 알린다.

### 구현 행동강령

**오프라인 감지:**

```python
async def check_online() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.get("https://api.anthropic.com")
        return True
    except Exception:
        return False
```

LLM 호출 실패 시 자동으로 Ollama로 전환한다:

```python
async def call_llm_with_fallback(messages, tools, intent):
    provider = get_provider_for_intent(intent)
    try:
        return await provider.stream(messages, tools)
    except Exception as e:
        import logging
        logging.warning(f"Primary LLM failed: {e}, falling back to Ollama")
        await play_filler(voice_client, "default")
        return await ollama_provider.stream(messages, [])  # 툴 없이 폴백
```

**에러 처리 원칙:**

- 모든 에러는 catch하고, 봇이 죽지 않게 한다
- 사용자가 인지해야 하는 에러는 음성으로 알린다 ("연결이 불안정해서 로컬 모드로 전환했어요")
- 디버깅용 에러는 Discord 채팅 채널에 `⚠️ ERROR: {message}` 형식으로 게시한다
- 봇 자체가 재시작 없이 복구 가능한 에러는 로깅만 하고 계속 진행한다

**Ollama 설치 및 Qwen 2.5 설정:**

```bash
# Ollama 설치
curl -fsSL https://ollama.ai/install.sh | sh

# Qwen 2.5 14B 다운로드 (약 9GB)
ollama pull qwen2.5:14b

# 서비스 시작 확인
ollama serve
```

```python
# core/providers/ollama.py
import httpx
import json
from .base import Delta

class OllamaProvider:
    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    async def stream(self, messages, tools):
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json={
                "model": self.model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "stream": True,
            }) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if content := data.get("message", {}).get("content", ""):
                            yield Delta(text=content)
                        if data.get("done"):
                            yield Delta(text="", is_final=True)
```

### 품질 검증

- [ ] 홈서버 인터넷 플러그를 뽑으면 다음 턴에 "로컬 모드로 전환했어요" 음성이 나온다
- [ ] 인터넷이 복구되면 다음 턴에 자동으로 Claude로 복귀한다
- [ ] ElevenLabs 오류 시 Discord 채팅에 `⚠️ TTS 오류` 메시지가 게시된다
- [ ] 어떤 에러가 발생해도 봇 프로세스 자체가 종료되지 않는다

---

## 장기 메모리 관리

### 개념

Anthropic API는 무상태(stateless)다. 봇을 재시작하면 이전 대화를 모른다. claude.ai 앱의 메모리 기능은 API에 노출되지 않으므로 봇에서 직접 사용할 수 없다.

대신 `memory.md` 파일을 시스템 프롬프트에 매 호출마다 주입하는 방식으로 동일한 효과를 만든다. 봇의 장기 기억은 세 층으로 구성된다:

```
Layer 1 — memory.md
  "나는 누구, 진행 중인 것들, 선호"
  항상 로드됨, 매 대화에 주입
  → 음성으로 업데이트 가능

Layer 2 — JSONL 아카이브 (음성 대화 기록)
  "언제 무슨 말 했고 무슨 툴 썼고"
  키워드 트리거 시 검색해서 주입
  → "저번에 X 관련 얘기했던 거 찾아줘"

Layer 3 — Notion (생성된 산출물)
  "실제로 만들어진 메모, 정리된 내용"
  이미 MCP로 연결됨
  → "X 관련 노션 페이지 찾아줘"
```

### memory.md 구조

```markdown
# 사용자 컨텍스트

## 기본 정보
- 연세대학교 재학생, DigiTools/AI Agents 수강 중
- 한국어 기본, 코드/문서는 영어
- 효율 우선, 과도한 설명 생략 선호

## 진행 중인 프로젝트
- car-assistant Discord 봇 개발 (현재 Phase X)
- LearnUs-Notion 자동화 파이프라인 (진행 중)
- Krita MCP 서버 (Qt 스레드 문제 미해결)

## 결정된 사항
- 글쓰기 과제: AI 윤리 주제로 5월 중 작성 예정
- ...

## 다음에 이어할 작업
- ...
```

### 봇에서의 주입

```python
from pathlib import Path

def load_memory() -> str:
    path = Path("memory.md")
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""

SYSTEM_PROMPT = f"""
당신은 사용자를 보조하는 음성 AI 어시스턴트입니다.

## 사용자 메모리
{load_memory()}

## 응답 지침
...
"""
```

### 음성으로 memory.md 업데이트

"메모리에 추가해줘 — [내용]"이라는 발화가 들어오면 봇이 직접 `memory.md`를 수정한다. 인텐트 분류기에 `memory.update` 항목을 추가하고, 파일시스템 MCP 또는 직접 파일 쓰기로 구현한다.

```python
# classify_intent에 추가
if any(kw in t for kw in ["메모리에 추가", "기억해줘", "저장해둬"]):
    return "memory.update"
```

### 주기적 업데이트 — claude.ai 활용

claude.ai에서 나눈 대화의 중요 내용을 주기적으로 추출해 `memory.md`에 반영한다.

**절차:**

1. Google Calendar 또는 폰 알림에 "memory.md 업데이트" 리마인더를 주 1회 설정한다 (예: 매주 일요일 저녁)
2. claude.ai에서 아래 추출 프롬프트를 실행한다
3. 출력 결과를 검토한 뒤 `memory.md`에 붙여넣는다
4. 봇이 다음 대화부터 반영한다

**추출 프롬프트 (claude.ai Project Instructions에 저장해 재사용):**

```
최근 대화에서 다음 항목에 해당하는 내용을 추출해줘:
- 진행 중이거나 새로 시작한 프로젝트
- 결정된 사항 (주제, 방향, 선택지)
- 다음에 이어할 작업
- 선호나 패턴으로 기록할 만한 것

기존 memory.md와 중복되는 내용은 제외하고,
추가/수정/삭제 형태로 diff만 출력해줘.
```

**업데이트 주기:**

- 기본: 주 1회
- 큰 프로젝트가 마무리되거나 중요한 결정이 생겼을 때 수시로
- memory.md가 지나치게 길어지면 오래된 항목을 정리한다 (컨텍스트 낭비 방지)

### 구현 시점

Phase 6 (MCP 툴 통합) 완료 후 추가한다. 파일시스템 MCP가 이미 연결되어 있으므로 추가 인프라 없이 구현 가능하다.

---

## 전역 구현 원칙

### 반드시 지키는 것

1. **Phase 순서를 지킨다.** 마일스톤 검증을 통과하기 전에 다음 Phase 코드를 쓰지 않는다.
2. **한 번에 하나만 바꾼다.** 문제가 생겼을 때 어디서 생겼는지 알 수 있도록 변경을 작게 유지한다.
3. **오디오 파이프라인을 절대 블로킹하지 않는다.** 파일 I/O, 네트워크 호출, 무거운 연산은 모두 `asyncio.create_task` 또는 `run_in_executor`로 감싼다.
4. **에러 메시지를 삼키지 않는다.** `except Exception: pass`는 사용하지 않는다. 항상 로깅하고, 사용자가 알아야 할 것은 알린다.
5. **모델 인스턴스는 봇 시작 시 한 번만 생성한다.** Porcupine, Silero VAD, WhisperModel, LLMProvider, ElevenLabsTTS 모두 전역 인스턴스로 유지한다.
6. **Phase 1의 WAV 디버그 저장 코드는 Phase 2 완료 후 제거한다.**

### 코드 설명 요청 시

각 Phase 시작 시 "이 Phase에서 무엇을 만들 것인지, 어떤 파일을 어떤 순서로 작성할 것인지"를 먼저 설명한 뒤 코드를 작성한다.

### 테스트 방법

각 Phase의 품질 검증 항목은 실제로 폰의 Discord 앱에서 음성으로 테스트한다. 단위 테스트로 대체하지 않는다 — 이 시스템의 버그 대부분은 오디오 타이밍, 네트워크 끊김, 실제 음성 인식 품질에서 나오기 때문이다.

---

## 시작 방법

이 문서를 읽었으면 다음 순서로 시작한다:

1. Discord Developer Portal에서 봇 토큰을 발급받는다
2. 개인용 Discord 서버를 만들고 음성 채널과 텍스트 채널을 각각 하나씩 생성한다
3. `uv init car-assistant` → `pyproject.toml` 작성 → `uv sync`
4. `.env` 파일 작성 (`.env.example` 참조)
5. Phase 0 구현 시작

**Phase 0 마일스톤을 만족하기 전까지는 Phase 1 코드를 한 줄도 쓰지 않는다.**
