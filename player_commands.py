from discord.ext import commands

import Player
import translations

_ = translations.setup_i18n('es')

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
            await ctx.send(_("Audio playback paused."))
        else:
            await ctx.send(_("No audio is currently playing."))

    @commands.command()
    async def unpause(self, ctx):
        """Unpauses the currently playing audio"""
        vc = ctx.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await ctx.send(_("Audio playback resumed"))
        else:
            await ctx.send(_("Audio playback is not paused"))
    
    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        vc = ctx.voice_client
        if vc and vc.is_connected():
            await self.player.stop(ctx)
        else:
            await ctx.send(_("Not currently connected to a voice channel"))

    @commands.command()
    async def skip(self, ctx):
        """Skips the current song"""
        if ctx.voice_client.is_connected():
            await self.player.skip(ctx)
            await ctx.send(_("Skipped song"))
        else:
            await ctx.send(_("Not currently connected to a voice channel"))


    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send(_("Not currently connected to a voice channel"))

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(_("Volume changed to ") + volume + "%")

async def setup(bot):
    await bot.add_cog(PlayerCommands(bot))
