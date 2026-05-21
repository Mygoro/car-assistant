import asyncio
import logging
import os

import davey as _davey
import discord
import discord.opus
from discord.ext import commands, tasks
from discord.ext import voice_recv
from discord.ext.voice_recv.opus import PacketDecoder
from discord.ext.voice_recv.router import PacketRouter
from dotenv import load_dotenv

from core.audio_sink import CarAudioSink

load_dotenv()

log = logging.getLogger(__name__)

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

bot = commands.Bot(command_prefix="!", intents=intents)
voice_client: voice_recv.VoiceRecvClient | None = None
pcm_queue: asyncio.Queue = asyncio.Queue()


@bot.event
async def on_ready():
    print(f"Bot ready: {bot.user}")
    voice_watchdog.start()


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
