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

### 목표

openwakeword가 들어오는 모든 PCM 청크를 검사하고, "hey otto"가 감지되면 이후 파이프라인을 활성화한다. TTS 송신 중에는 감지를 일시 정지한다.

### 구현 행동강령

**core/wake_word.py:**

```python
from pathlib import Path
import numpy as np
from openwakeword.model import Model

CHUNK_SAMPLES = 1280  # 80ms at 16kHz

class WakeWordDetector:
    def __init__(self, model_path: str, threshold: float = 0.5):
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Wake word model not found: {path}")
        self._model_name = path.stem
        self._model = Model(wakeword_models=[str(path)], inference_framework="onnx")
        self._threshold = threshold
        self._paused = False
        self._buffer = np.array([], dtype=np.int16)

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False
        self._buffer = np.array([], dtype=np.int16)

    def process(self, pcm_chunk: np.ndarray) -> bool:
        if self._paused:
            return False
        self._buffer = np.concatenate([self._buffer, pcm_chunk])
        while len(self._buffer) >= CHUNK_SAMPLES:
            frame = self._buffer[:CHUNK_SAMPLES]
            self._buffer = self._buffer[CHUNK_SAMPLES:]
            prediction = self._model.predict(frame)
            score = max(prediction.values(), default=0.0)
            if score >= self._threshold:
                self._model.reset()
                self._buffer = np.array([], dtype=np.int16)
                return True
        return False
```

**봇 메인 루프에서의 통합:**

오디오 큐에서 청크를 꺼내 WakeWordDetector에 넘기는 비동기 루프를 만든다. Wake word가 감지되면 `LISTENING` 상태로 전환해 이후 청크를 캡처 버퍼로 보낸다. 상태는 단순하게 유지한다:

```
IDLE → (wake word) → LISTENING → (VAD 종료) → PROCESSING → IDLE
```

PROCESSING 중에는 wake word 감지를 자동으로 일시 정지한다.

**openwakeword 커스텀 모델 학습 절차:**

1. "hey otto" 발화 샘플 10~20개 녹음 (WAV, 16kHz mono)
2. openwakeword training 스크립트 실행:
   ```bash
   python -m openwakeword.train --positive_reference_clips path/to/samples/ \
       --output_dir wake_word/ --model_name hey_otto
   ```
3. 생성된 `hey_otto.onnx`를 `wake_word/` 디렉토리에 저장
4. `config.yaml`의 `model_path: "wake_word/hey_otto.onnx"` 확인

### 품질 검증

- [ ] "hey otto"라고 말하면 봇 콘솔에 `WAKE WORD DETECTED` 로그가 출력된다
- [ ] Wake word 없이 일반 대화를 해도 콘솔에 감지 로그가 나오지 않는다
- [ ] 봇이 TTS를 송출하는 중(Phase 5 이후 검증)에는 봇 목소리로 wake word가 재트리거되지 않는다
- [ ] 봇이 6시간 이상 실행되어도 메모리 누수 없이 안정적으로 작동한다 (작업 관리자 또는 htop으로 확인)

### 임계값 조정 지침

`config.yaml`의 `threshold` 값:
- 0.3: 오탐 거의 없음, 명확한 발음만 감지
- 0.5: 권장 초기값
- 0.7: 민감하게 감지, 유사 발음에 오탐 가능

0.5로 시작하고 실제 사용 중 오탐 또는 미감지가 발생하면 조정한다.

---

## Phase 3 — STT 통합

### 목표

Wake word 이후 발화를 캡처하고, Silero VAD로 발화 종료를 감지하고, faster-whisper로 한국어 트랜스크립트를 생성하고, Discord 채팅 채널에 게시한다.

### 구현 행동강령

**core/vad.py:**

Silero VAD 모델을 ONNX Runtime으로 로드한다. Torch 없이 사용 가능한 것이 핵심이다.

```python
import numpy as np
import onnxruntime as ort
from pathlib import Path

class SileroVAD:
    """Silero VAD via ONNX Runtime (no PyTorch dependency)."""
    def __init__(self, threshold: float = 0.5):
        model_path = self._ensure_model()
        self.session = ort.InferenceSession(str(model_path))
        self.threshold = threshold
        self._h = np.zeros((2, 1, 64), dtype=np.float32)
        self._c = np.zeros((2, 1, 64), dtype=np.float32)
        self._sr = np.array(16000, dtype=np.int64)

    def _ensure_model(self) -> Path:
        path = Path("silero_vad.onnx")
        if not path.exists():
            import urllib.request
            urllib.request.urlretrieve(
                "https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx",
                path,
            )
        return path

    def is_speech(self, pcm_chunk: np.ndarray) -> bool:
        """chunk must be 512 samples (32ms) at 16kHz, float32 normalized to [-1, 1]."""
        audio = pcm_chunk.astype(np.float32) / 32768.0
        audio = audio[np.newaxis, :]
        out, self._h, self._c = self.session.run(
            None,
            {"input": audio, "sr": self._sr, "h": self._h, "c": self._c},
        )
        return float(out[0][0]) > self.threshold

    def reset(self):
        self._h = np.zeros((2, 1, 64), dtype=np.float32)
        self._c = np.zeros((2, 1, 64), dtype=np.float32)
```

**core/stt.py:**

```python
from faster_whisper import WhisperModel
import numpy as np

class STTEngine:
    def __init__(self, model_size: str, device: str, compute_type: str,
                 language: str, initial_prompt: str):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.language = language
        self.initial_prompt = initial_prompt

    async def transcribe(self, pcm_16k_mono: np.ndarray) -> str:
        """PCM int16 → Korean transcript string."""
        audio = pcm_16k_mono.astype(np.float32) / 32768.0
        import asyncio
        loop = asyncio.get_event_loop()
        segments, _ = await loop.run_in_executor(
            None,
            lambda: self.model.transcribe(
                audio,
                language=self.language,
                initial_prompt=self.initial_prompt,
                beam_size=5,
                vad_filter=True,
            ),
        )
        return "".join(seg.text for seg in segments).strip()
```

**발화 캡처 로직:**

Wake word 감지 → VAD 기반 발화 캡처. `tail_ms`는 config에서 읽는다 (기본값 4000ms):

```
LISTENING 상태 진입
  while True:
    chunk = audio_queue.get()
    capture_buffer.append(chunk)
    if vad.is_speech(chunk):
        silent_frames = 0
    else:
        silent_frames += 1

    if silent_frames >= tail_frames:  # tail_ms / 32ms = 4000 / 32 = 125 프레임
        break
    if len(capture_buffer) * 32ms >= max_duration_s * 1000:
        break

transcript = await stt.transcribe(concat(capture_buffer))
```

**Discord 채팅 채널 게시:**

STT 결과를 `🎤 {transcript}` 형식으로 채팅 채널에 즉시 게시한다. LLM 응답이 아직 없어도 트랜스크립트만 먼저 보낸다.

### 품질 검증

- [ ] Wake word 말하고 발화하면 채팅 채널에 트랜스크립트가 게시된다 (CPU 모드라 느릴 수 있음 — 기능 동작 여부만 확인)
- [ ] 발화 중간에 4초 이상 침묵하면 발화 종료로 판정된다
- [ ] 2–3초 침묵 후 말을 이어가면 같은 발화로 계속 캡처된다
- [ ] 30초 이상 말해도 max_duration_s 제한에서 자동으로 발화가 종료된다
- [ ] "오늘 기독교 강의 핵심 메모해줘" 같은 문장이 알아볼 수 있게 트랜스크립트된다
- [ ] `WhisperModel`이 봇 시작 시 한 번만 로드되고, 매 호출마다 재로드되지 않는다

### 흔한 실수

- `WhisperModel`은 최초 1회만 초기화한다. `async def transcribe` 안에서 생성하지 않는다.
- `faster-whisper`는 동기 API다. 이벤트 루프를 블로킹하지 않으려면 반드시 `run_in_executor`로 감싼다.
- `vad_filter=True`를 faster-whisper에 전달하면 whisper 내부 VAD가 추가로 작동한다. Silero VAD와 이중으로 사용해도 문제없다.

---

## Phase 4 — LLM 텍스트 응답

### 목표

트랜스크립트를 LLM에 보내고 텍스트 응답을 받아 Discord 채팅 채널에 게시한다. 음성 출력은 이 Phase에서 없다. 프로바이더 추상화와 인텐트 분류기를 완성한다.

### 구현 행동강령

**core/providers/base.py:**

```python
from typing import Protocol, AsyncIterator
from dataclasses import dataclass

@dataclass
class Message:
    role: str  # "user" | "assistant" | "system"
    content: str

@dataclass
class Delta:
    text: str
    is_final: bool = False

class LLMProvider(Protocol):
    async def stream(
        self,
        messages: list[Message],
        tools: list[dict],
    ) -> AsyncIterator[Delta]: ...
```

**core/providers/anthropic.py:**

```python
import anthropic
from .base import Message, Delta

class AnthropicProvider:
    def __init__(self, api_key: str, model: str, max_tokens: int):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    async def stream(self, messages, tools):
        anthropic_messages = [
            {"role": m.role, "content": m.content}
            for m in messages if m.role != "system"
        ]
        system = next((m.content for m in messages if m.role == "system"), None)

        async with self.client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=anthropic_messages,
            tools=tools if tools else [],
        ) as stream:
            async for text in stream.text_stream:
                yield Delta(text=text)
            yield Delta(text="", is_final=True)
```

**시스템 프롬프트:**

```python
SYSTEM_PROMPT = """
당신은 사용자를 보조하는 음성 AI 어시스턴트입니다.

사용자 컨텍스트:
- 연세대학교 재학생, DigiTools/AI Agents 수강 중
- 한국어로 주로 소통하며 영어 전문 용어도 사용
- 주요 도구: Notion, Google Calendar, Claude Code, ElevenLabs, Krita MCP

응답 지침:
- 응답은 음성으로 전달된다
- 마크다운 형식(##, **, ```)을 사용하지 않는다
- 목록은 자연스러운 문장으로 표현한다
- 불필요한 서두와 반복을 생략한다
- 필요한 정보는 생략하지 않고 정확하게 전달한다
""".strip()
```

**인텐트 분류기:**

휴리스틱 우선, LLM 위임 두 번째:

```python
def classify_intent(transcript: str) -> str:
    t = transcript.strip()
    if any(kw in t for kw in ["기록", "메모", "노트", "저장"]):
        return "note.create"
    if any(kw in t for kw in ["일정", "캘린더", "약속", "몇 시", "언제"]):
        if any(kw in t for kw in ["추가", "등록", "넣어", "잡아"]):
            return "calendar.write"
        return "calendar.read"
    if any(kw in t for kw in ["찾아", "검색", "알아봐", "뭐야", "뭔지"]):
        return "research"
    return "simple_qa"
```

**대화 히스토리 관리:**

최근 10턴을 메모리에 유지한다. 10턴을 초과하면 오래된 턴을 제거한다. 사용자가 "새로 시작해" 또는 "리셋"이라고 말하면 히스토리를 비운다.

### 품질 검증

- [ ] Wake word → 발화 → 채팅 채널에 LLM 텍스트 응답이 게시된다
- [ ] 응답이 마크다운 형식을 포함하지 않는다 (`**`, `##`, ` ``` ` 없음)
- [ ] 간단한 질문에는 짧게, 설명이 필요한 질문에는 충분히 길게 응답한다
- [ ] 연속된 대화에서 앞 발화의 컨텍스트를 기억한다 (히스토리 동작 확인)
- [ ] "리셋"이라고 말하면 히스토리가 비워진다

---

## Phase 5 — TTS 음성 출력

### 목표

LLM 텍스트 응답을 ElevenLabs로 스트리밍 변환하고 Discord 음성 채널로 송출한다. LLM 생성과 TTS 변환과 Discord 송신이 파이프라인으로 겹쳐서 실행된다.

### 구현 행동강령

**core/tts.py:**

```python
import httpx
from typing import AsyncIterator

class ElevenLabsTTS:
    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: str, voice_id: str, model: str):
        self.api_key = api_key
        self.voice_id = voice_id
        self.model = model

    async def stream_mp3(self, text: str) -> AsyncIterator[bytes]:
        """Stream MP3 bytes for given text."""
        url = f"{self.BASE_URL}/text-to-speech/{self.voice_id}/stream"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        body = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=headers, json=body) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=1024):
                    yield chunk
```

**Discord 음성 송신 파이프라인:**

ElevenLabs는 MP3를 반환한다. Discord는 PCM 48kHz stereo를 요구한다. ffmpeg async subprocess를 파이프라인으로 연결한다:

```python
import asyncio
import io
import discord

async def speak(voice_client: discord.VoiceClient, mp3_stream):
    ffmpeg_proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-i", "pipe:0",
        "-f", "s16le", "-ar", "48000", "-ac", "2",
        "-loglevel", "quiet",
        "pipe:1",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )

    async def feed_input():
        async for chunk in mp3_stream:
            ffmpeg_proc.stdin.write(chunk)
        ffmpeg_proc.stdin.close()

    async def read_output():
        pcm_buffer = b""
        while True:
            chunk = await ffmpeg_proc.stdout.read(3840)
            if not chunk:
                break
            pcm_buffer += chunk
        return pcm_buffer

    feed_task = asyncio.create_task(feed_input())
    pcm_data = await read_output()
    await feed_task

    source = discord.PCMAudio(io.BytesIO(pcm_data))
    voice_client.play(source)
    while voice_client.is_playing():
        await asyncio.sleep(0.1)
```

**스트리밍 TTS → LLM 연동:**

LLM 스트림에서 텍스트가 누적되면 문장 단위로 TTS에 보낸다. 문장 구분자: `。`, `.`, `!`, `?`, `\n`. 10자 미만 조각은 다음 조각과 합쳐서 보낸다.

**TTS 중 wake word 일시 정지:**

```python
wake_word_detector.pause()
voice_client.play(source)
while voice_client.is_playing():
    await asyncio.sleep(0.1)
wake_word_detector.resume()
```

**필러 발화:**

툴 호출이 예상될 때 미리 생성된 MP3를 재생한다:

```python
FILLER_MAP = {
    "searching": "fillers/chatgo_itda.mp3",
    "confirming": "fillers/hwagin_jung.mp3",
    "default": "fillers/jamsiman.mp3",
}

async def play_filler(voice_client, filler_key: str = "default"):
    path = FILLER_MAP.get(filler_key, FILLER_MAP["default"])
    source = discord.FFmpegPCMAudio(path)
    voice_client.play(source)
    while voice_client.is_playing():
        await asyncio.sleep(0.05)
```

필러 MP3는 ElevenLabs로 한 번 생성해서 파일로 저장해 둔다. 이후 API 호출 없이 재사용.

### 품질 검증

- [ ] Wake word → 발화 → 봇이 음성으로 답한다
- [ ] 봇이 말하는 중에 wake word를 말해도 재트리거되지 않는다
- [ ] 봇이 말을 끝내면 wake word 감지가 재개된다
- [ ] 응답이 끊기거나 부자연스럽게 잘리지 않는다

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

## Phase 7 — 아카이브

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

## Phase 8 — 폴백 및 안정화

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
