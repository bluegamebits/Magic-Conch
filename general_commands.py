from discord.ext import commands
import discord

import Player
from conch_voice import Voice
import translations

_ = translations.setup_i18n('es')

class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None 
        self.guildPlayer = {}
        self.guildVoice = {}
        self.image_generator = ImageGenerator(self.bot)

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

async def setup(bot):
    await bot.add_cog(GeneralCommands(bot))