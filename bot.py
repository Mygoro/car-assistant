import asyncio
import enum
import logging
import os
import wave
from pathlib import Path

import davey as _davey
import discord
import discord.opus
import numpy as np
import yaml
from discord.ext import commands, tasks
from discord.ext import voice_recv
from discord.ext.voice_recv.opus import PacketDecoder
from discord.ext.voice_recv.router import PacketRouter
from dotenv import load_dotenv

from core.audio_sink import CarAudioSink
from core.wake_word import WakeWordDetector

load_dotenv()

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

with open("config.yaml", encoding="utf-8") as _f:
    _cfg = yaml.safe_load(_f)

wake_detector: WakeWordDetector = WakeWordDetector(
    model_path=_cfg["wake_word"]["model_path"],
    threshold=_cfg["wake_word"]["threshold"],
)


class BotState(enum.Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"


_state = BotState.IDLE

# 녹음 모드 상태 (학습 데이터 수집용)
_recording = False
_rec_chunks: list[np.ndarray] = []

# Patch 1: discord-ext-voice-recv's _do_run has no per-packet error handling;
# one bad opus packet kills the entire router thread.
def _resilient_do_run(self):
    while not self._end_thread.is_set():
        self.waiter.wait()
        with self._lock:
            for decoder in self.waiter.items:
                try:
                    data = decoder.pop_data()
                    if data is not None:
                        self.sink.write(data.source, data)
                except discord.opus.OpusError as e:
                    log.debug("Skipping corrupted opus packet (ssrc=%s): %s", getattr(decoder, 'ssrc', '?'), e)

PacketRouter._do_run = _resilient_do_run

# Patch 2: discord-ext-voice-recv doesn't apply DAVE (E2E) decryption after
# transport decryption. Strip the DAVE layer before handing data to the opus decoder.
_orig_decode_packet = PacketDecoder._decode_packet

def _dave_decode_packet(self, packet):
    if bool(packet):  # skip FakePacket (FEC)
        vc = self.sink.voice_client
        if vc is not None:
            dave_session = getattr(vc._connection, 'dave_session', None)
            if dave_session is not None and dave_session.ready:
                user_id = self._cached_id or vc._get_id_from_ssrc(self.ssrc) or 0
                if user_id and not dave_session.can_passthrough(user_id):
                    try:
                        packet.decrypted_data = dave_session.decrypt(
                            user_id, _davey.MediaType.audio, bytes(packet.decrypted_data)
                        )
                    except Exception as e:
                        log.debug("DAVE decrypt failed ssrc=%s user=%s: %s", self.ssrc, user_id, e)
    return _orig_decode_packet(self, packet)

PacketDecoder._decode_packet = _dave_decode_packet

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.message_content = True  # prefix 명령어 수신에 필요 (Developer Portal에서도 활성화 필요)

bot = commands.Bot(command_prefix="!", intents=intents)
voice_client: voice_recv.VoiceRecvClient | None = None
pcm_queue: asyncio.Queue = asyncio.Queue()


@bot.event
async def on_ready():
    print(f"Bot ready: {bot.user}")
    voice_watchdog.start()
    asyncio.create_task(audio_processor())


async def audio_processor():
    global _state
    log.info("audio_processor started")
    while True:
        try:
            chunk = await pcm_queue.get()

            if _recording:
                _rec_chunks.append(chunk.copy())

            if _state == BotState.IDLE:
                if await wake_detector.process(chunk):
                    log.info("WAKE WORD DETECTED")
                    _state = BotState.LISTENING
                    asyncio.create_task(_notify_wake_word())
                    # Phase 3 will replace this stub with VAD + STT capture
                    asyncio.create_task(_listening_stub())
            elif _state == BotState.LISTENING:
                pass  # Phase 3: VAD + capture buffer will be added here
        except Exception:
            log.exception("audio_processor error")


async def _notify_wake_word():
    ch_id = os.environ.get("DISCORD_TEXT_CHANNEL_ID")
    if not ch_id:
        return
    ch = bot.get_channel(int(ch_id))
    if ch:
        await ch.send("[WAKE WORD] 크랭크 오토 감지됨")


async def _listening_stub():
    """Phase 2 stub: return to IDLE after 2s so repeated detections are testable."""
    global _state
    await asyncio.sleep(2.0)
    if _state == BotState.LISTENING:
        _state = BotState.IDLE


@bot.command(name="record")
async def cmd_record(ctx, sample_type: str = ""):
    """학습 데이터 녹음. 사용법: !record positive | !record negative | !record status"""
    global _recording, _rec_chunks

    if sample_type == "status":
        pos_c = len(list(Path("wake_word/training_data/positive").glob("*.wav")))
        neg_c = len(list(Path("wake_word/training_data/negative").glob("*.wav")))
        lines = [
            "📊 **샘플 현황**",
            f"positive: **{pos_c}개** {'✅' if pos_c >= 15 else f'(목표 15개)'}",
            f"negative: **{neg_c}개** {'✅' if neg_c >= 15 else f'(목표 15개)'}",
        ]
        if pos_c >= 15 and neg_c >= 15:
            lines.append("\n✅ 학습 준비 완료 — `uv run tools/train_wake_word.py`")
        await ctx.send("\n".join(lines))
        return

    if sample_type not in ("positive", "negative"):
        await ctx.send(
            "**wake word 녹음 명령어**\n"
            "`!record positive` — 3초: 「크랭크 오토」 발화\n"
            "`!record negative` — 3초: 다른 말 or 소음\n"
            "`!record status` — 샘플 수 확인"
        )
        return

    if _recording:
        await ctx.send("⚠️ 이미 녹음 중입니다.")
        return

    dur = 3 if sample_type == "positive" else 3
    prompt = "지금 「크랭크 오토」라고 말하세요" if sample_type == "positive" else "다른 말 또는 주변 소음을 내세요 (크랭크 오토 제외)"

    _rec_chunks = []
    _recording = True
    msg = await ctx.send(f"🔴 **{sample_type}** 녹음 중 ({dur}초)… {prompt}")

    await asyncio.sleep(dur)
    _recording = False

    if not _rec_chunks:
        await msg.edit(content="⚠️ 오디오가 수신되지 않았습니다. 음성 채널에 접속되어 있는지 확인하세요.")
        return

    audio = np.concatenate(_rec_chunks)
    target_dir = Path(f"wake_word/training_data/{sample_type}")
    target_dir.mkdir(parents=True, exist_ok=True)
    idx = len(sorted(target_dir.glob("*.wav")))
    path = target_dir / f"sample_{idx:03d}.wav"

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(audio.tobytes())

    pos_c = len(list(Path("wake_word/training_data/positive").glob("*.wav")))
    neg_c = len(list(Path("wake_word/training_data/negative").glob("*.wav")))
    await msg.edit(content=(
        f"✅ **{path.name}** 저장됨 ({len(audio) / 16000:.1f}초)\n"
        f"누계 — positive: **{pos_c}개** / negative: **{neg_c}개**"
    ))


@tasks.loop(seconds=30)
async def voice_watchdog():
    global voice_client
    guild = bot.get_guild(int(os.environ["DISCORD_GUILD_ID"]))
    if guild is None:
        print("Guild not found — check DISCORD_GUILD_ID")
        return
    channel = guild.get_channel(int(os.environ["DISCORD_VOICE_CHANNEL_ID"]))
    if channel is None:
        print("Voice channel not found — check DISCORD_VOICE_CHANNEL_ID")
        return

    # Sync reference if discord.py already has an active connection
    existing = discord.utils.get(bot.voice_clients, guild=guild)
    if existing and existing.is_connected():
        voice_client = existing
        return

    try:
        voice_client = await channel.connect(cls=voice_recv.VoiceRecvClient)
        loop = asyncio.get_event_loop()
        sink = CarAudioSink(loop, pcm_queue)
        voice_client.listen(sink)
        print(f"Connected to voice channel: {channel.name}")
    except discord.errors.ClientException:
        # Race: discord.py connected internally between our check and connect()
        voice_client = discord.utils.get(bot.voice_clients, guild=guild)
    except Exception as e:
        print(f"Voice watchdog error: {e}")


@voice_watchdog.before_loop
async def before_voice_watchdog():
    # Wait for any Discord session-resume voice reconnections to settle
    await asyncio.sleep(5)


@voice_watchdog.error
async def voice_watchdog_error(error):
    print(f"Voice watchdog unhandled error: {error}")


bot.run(os.environ["DISCORD_BOT_TOKEN"])
