from discord.ext import commands

import Player
from conch_voice import Voice
import translations

_ = translations.setup_i18n('es')

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.guildPlayer = {}
        self.guildVoice = {}
        print("Created Player commands class")

    async def _get_guild_player(self, ctx):
        ctx_guild = ctx.guild.id
        guild = self.guildPlayer.get(ctx_guild)
        if guild:
            return guild
        else:
            self.guildPlayer[ctx_guild] =  Player.MusicPlayer(self.bot)
            return self.guildPlayer.get(ctx_guild)
        
    async def _get_guild_voice(self, ctx):
        ctx_guild = ctx.guild.id
        guild = self.guildVoice.get(ctx_guild)
        if guild:
            return guild
        else:
            self.guildVoice[ctx_guild] = Voice(self.bot)
            return self.guildVoice.get(ctx_guild)
        
    @commands.command()
    async def join(self, ctx):
        player = await self._get_guild_player(ctx)
        await player.join(ctx)
                       
    @commands.command()
    async def play(self, ctx, *, url):
        player = await self._get_guild_player(ctx)
        await player.play_song(ctx, url)

    @commands.command()
    async def pause(self, ctx):
        player = await self._get_guild_player(ctx)
        await player.pause(ctx)

    @commands.command()
    async def unpause(self, ctx):
        player = await self._get_guild_player(ctx)
        await player.unpause(ctx)

    @commands.command()
    async def stop(self, ctx):
        player = await self._get_guild_player(ctx)
        await player.stop(ctx)
        
    @commands.command()
    async def skip(self, ctx):
        player = await self._get_guild_player(ctx)
        await player.skip(ctx)

    @commands.command()
    async def volume(self, ctx, volume: int):
        player = await self._get_guild_player(ctx)
        await player.volume(ctx, volume)

    @commands.command()
    async def purge(self, ctx):
        player = await self._get_guild_player(ctx)
        await player.purge_queue(ctx)

    @commands.command()
    async def previous(self, ctx):
        player = await self._get_guild_player(ctx)
        await player.play_previous_song(ctx)
    
    @commands.command()
    async def autoplay(self, ctx, autoplay):
        player = await self._get_guild_player(ctx)
        await player.set_autoplay(ctx, autoplay)

    @commands.command()
    async def queue(self, ctx):
        player = await self._get_guild_player(ctx)
        await player.list_queue(ctx)

    @commands.command()
    async def say(self, ctx, *, query):
        voice = await self._get_guild_voice(ctx)
        await voice.say(ctx, query)

    @commands.command()
    async def ask(self, ctx, *, query):
        voice = await self._get_guild_voice(ctx)
        await voice.ask(ctx, query)
        



    #@commands.Cog.listener()
    #async def on_message(self, message):
        """
        Listens to bot messages and updates player.ctx
        Used only for testing purpouses
        """
    #    if not message.author.bot:  # Ignore non-bot messages
    #        return
    #    self.player.ctx =  await self.bot.get_context(message)

async def setup(bot):
    await bot.add_cog(Commands(bot))
    
