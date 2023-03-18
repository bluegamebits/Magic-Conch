from discord.ext import commands

import Player

class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.player = Player.MusicPlayer(bot)
        

    @commands.command()
    async def join(self, ctx):
        """Joins a voice channel, if already in a voice channel it switches to the user's voice channel"""
        await self.player.join(ctx)

  
                       
    @commands.command()
    async def play(self, ctx, *, url):
        """Plays from a url (almost anything youtube_dl supports)"""
        await self.player.play_song(ctx, url)
        

        

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
            await self.player.stop()
        else:
            await ctx.send("Not currently connected to a voice channel")

    @commands.command()
    async def skip(self, ctx):
        """Stops and disconnects the bot from voice"""
        await self.player.skip()


    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Conectate a un canal de voz primero.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Volumen cambiado a {volume}%")

    # TODO Fix streaming, currently it doesn't work
   #@commands.command()
    #async def stream(self, ctx, *, url):
    #    """Streams from a url (same as yt, but doesn't predownload)"""

        #async with ctx.typing():
        #    try:
        #        player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, verbose=True)
        #    except Exception as e:
        #        print(f"Error creating player: {e}")
        #        return
        #    print(player)
        #    source = discord.FFmpegPCMAudio(player.url, executable='C:\\Custom path programs\\ffmpeg\\bin\\ffmpeg.exe', pipe=True, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
        #    ctx.voice_client.play(source, after=lambda e: print(f"Player error: {e}") if e else None)

        #await ctx.send(f"Now playing: {player.title}")

async def setup(bot):
    await bot.add_cog(PlayerCommands(bot))
