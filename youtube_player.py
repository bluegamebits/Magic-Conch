from discord.ext import commands
import asyncio

import youtube_dl
import discord
import google_voice
from requests import get
 

ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # Bind to ipv4 since ipv6 addresses cause issues at certain times
    'geo_bypass': True,# add geo-bypass option,

}

ffmpeg_options = {"options": "-vn"}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, verbose=False):
        loop = loop or asyncio.get_event_loop()
        
        # serches for video if not a link and chooses the first result, if it is a link it just passes it to youtube-dl to download

        # TODO: Implement choosing between multiple search results
        try:
            await get(url)
        except:
            data = await loop.run_in_executor(
                None, lambda: ytdl.extract_info(f"ytsearch:{url}", download=True)['entries'][0]
            )
        
        else:
            data = await loop.run_in_executor(
                None, lambda: ytdl.extract_info(url, download=True)
            )

        if "entries" in data:
            # Takes the first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
class voicespeak(commands.FlagConverter, prefix='zz', delimiter=''):
    make: str

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def join(self, ctx):
        """Joins a voice channel, if already in a voice channel it switches to the user's voice channel"""
        
        print(self.bot.user)

        voice_channel = ctx.author.voice.channel
        
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(voice_channel)

        await voice_channel.connect()

    async def get_source(self, url):
        """Retrieves source from url or search"""
        for i in range(10):
            try:
                source = await YTDLSource.from_url(url, loop=self.bot.loop, verbose=True)
                return source
            except Exception as e:
                print(f"Failed to download video: {e}")
                print(f"Retrying... (attempt {i+1}/10)")
                await asyncio.sleep(1)
        return None
    
    async def play_music(self, ctx, source):
        """Plays the given source in the voice channel"""
        vc = await self.join(ctx)
        vc = ctx.voice_client
        vc.play(
            source, after=lambda e: print(f"Player error: {e}") if e else None
        )
        await ctx.send(f"Now playing: {source.title}"
                       )
    @commands.command()
    async def play(self, ctx, *, url):
        """Plays from a url (almost anything youtube_dl supports)"""

        async with ctx.typing():
            source = await self.get_source(url)

            if source:
                await self.play_music(ctx, source)
            else:
                await ctx.send("Failed to retrieve music.")

    @commands.command()
    async def pause(self, ctx):
        """Pauses the current audio playback"""
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("Audio playback paused.")
        else:
            await ctx.send("No audio is currently playing.")

    @commands.command()
    async def unpause(self, ctx):
        """Unpauses the currently playing audio"""
        vc = ctx.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await ctx.send("Audio playback resumed")
        else:
            await ctx.send("Audio playback is not paused")
    
    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        vc = ctx.voice_client
        if vc and vc.is_connected():
            await vc.disconnect()
            await ctx.send("Disconnected from voice channel")
        else:
            await ctx.send("Not currently connected to a voice channel")

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Conectate a un canal de voz primero.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Volumen cambiado a {volume}%")

    # TODO Fix streaming, currently it doesn't work
    @commands.command()
    async def stream(self, ctx, *, url):
        """Streams from a url (same as yt, but doesn't predownload)"""

        async with ctx.typing():
            try:
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, verbose=True)
            except Exception as e:
                print(f"Error creating player: {e}")
                return
            print(player)
            source = discord.FFmpegPCMAudio(player.url, executable='C:\\Custom path programs\\ffmpeg\\bin\\ffmpeg.exe', pipe=True, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
            ctx.voice_client.play(source, after=lambda e: print(f"Player error: {e}") if e else None)

        await ctx.send(f"Now playing: {player.title}")

async def setup(bot):
    await bot.add_cog(Music(bot))
