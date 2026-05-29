# car-assistant 데스크탑 이식 — Claude Code 에이전트 프롬프트

데스크탑의 Claude Code에 아래 내용을 그대로 붙여넣어 이식 작업을 시작한다.

---

# car-assistant 데스크탑 이식 작업

## 프로젝트 개요

Discord 봇 기반 차량용 음성 AI 어시스턴트. Phase 0~5 완료(wake word → STT → LLM → TTS, E2E 검증됨). 현재 노트북 CPU에서 STT가 11~13s 소요되어 실사용 불가. 데스크탑 NVIDIA GPU로 이식하면 1~2s로 단축 가능.

## 이 세션의 목표

1. git clone → uv sync → .env 작성 → config.yaml GPU 설정
2. `uv run bot.py` 정상 기동 확인
3. "크랭크 오토" wake word → STT → LLM → TTS 전 구간 E2E 검증
4. `otto_events.log`에서 STT 지연 1~2s 이내 확인

## 사전 준비 확인 (작업 시작 전 직접 체크)

- [ ] NVIDIA GPU 드라이버 설치됨 (`nvidia-smi` 동작 확인)
- [ ] CUDA 버전 확인 (11.8 이상 권장)
- [ ] `uv` 설치됨 (`uv --version` 확인, 없으면 `pip install uv`)
- [ ] `ffmpeg` 설치됨 (`ffmpeg -version` 확인, 없으면 winget/choco로 설치)
- [ ] `.env` 값 준비됨 (노트북의 `.env` 파일 내용 미리 복사해둘 것)

## 설치 절차

### 1. 클론 및 의존성 설치

```bash
git clone https://github.com/Mygoro/car-assistant.git
cd car-assistant
uv sync
```

### 2. .env 파일 작성

프로젝트 루트에 `.env` 파일을 생성하고 아래 키를 채워 넣는다.
값은 노트북의 `.env`에서 복사.

```
DISCORD_BOT_TOKEN=
DISCORD_GUILD_ID=
DISCORD_VOICE_CHANNEL_ID=
DISCORD_TEXT_CHANNEL_ID=
DISCORD_OWNER_USER_ID=
ANTHROPIC_API_KEY=
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=
```

PICOVOICE_ACCESS_KEY, OPENAI_API_KEY는 현재 미사용이므로 비워도 됨.

### 3. config.yaml GPU 설정 변경

`config.yaml`에서 정확히 두 줄만 수정:

```yaml
stt:
  device: "cuda"                # "cpu" → "cuda"
  compute_type: "int8_float16"  # "int8" → "int8_float16"
```

다른 줄은 건드리지 않는다.

### 4. 봇 실행

```bash
uv run bot.py
```

또는 `run.bat` 더블클릭.

## 검증 체크리스트

- [ ] 봇 시작 로그에 `cuda` 및 `int8_float16` 표시됨
- [ ] Discord 음성 채널 자동 접속됨
- [ ] "크랭크 오토" 발화 → `otto_events.log`에 `WAKE WORD DETECTED` 로그
- [ ] STT 지연 측정: `otto_events.log`에서 `[TIMING] STT` 값이 1~3s 이내
- [ ] Discord 채팅 채널에 LLM 응답 게시됨
- [ ] Discord 음성 채널에서 TTS 음성 출력됨
- [ ] 세션 모드: "크랭크 오토" → 연속 대화 → "슬립 오토" → IDLE 복귀

## 문제 발생 시

| 증상 | 원인 | 해결 |
|------|------|------|
| `silero_vad.onnx` 다운로드 실패 | 네트워크 또는 권한 | https://github.com/snakers4/silero-vad 에서 수동 다운로드 후 프로젝트 루트에 배치 |
| CUDA out of memory | GPU 메모리 부족 | `config.yaml`에서 `compute_type: "int8"` 으로 변경 |
| ffmpeg not found | PATH 미등록 | ffmpeg PATH 추가 또는 재설치 |
| Discord heartbeat 끊김 | STT 블로킹 | 이미 수정됨 (`run_in_executor`). 로그 확인 후 재현되면 보고 |

## 검증 완료 후 다음 작업

Phase 6 MCP 툴 통합 (Calendar read, Notion read).
`docs/implementation-manual.md` Phase 6 섹션 참고.
MCP 인프라 구축 필요: `uv add mcp`.
