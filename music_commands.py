from discord.ext import commands
import discord

import translations

_ = translations.setup_i18n('es')

class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.general_commands = bot.get_cog("GeneralCommands")

    @commands.command()
    async def play(self, ctx, *, url):
        player = await self.general_commands._get_guild_player(ctx)
        print(player)
        await player.play_song(ctx, url)

    @commands.command()
    async def pause(self, ctx):
        player = await self.general_commands._get_guild_player(ctx)
        await player.pause(ctx)

    @commands.command(aliases=['resume'])
    async def unpause(self, ctx):
        player = await self.general_commands._get_guild_player(ctx)
        await player.unpause(ctx)

    @commands.command()
    async def stop(self, ctx):
        player = await self.general_commands._get_guild_player(ctx)
        await player.stop(ctx)
        
    @commands.command()
    async def skip(self, ctx):
        player = await self.general_commands._get_guild_player(ctx)
        await player.skip(ctx)

    @commands.command()
    async def volume(self, ctx, volume: int):
        player = await self.general_commands._get_guild_player(ctx)
        await player.volume(ctx, volume)

    @commands.command()
    async def purge(self, ctx):
        player = await self.general_commands._get_guild_player(ctx)
        await player.purge_queue(ctx)

    @commands.command()
    async def previous(self, ctx):
        player = await self.general_commands._get_guild_player(ctx)
        await player.play_previous_song(ctx)
    
    @commands.command()
    async def autoplay(self, ctx, autoplay):
        player = await self.general_commands._get_guild_player(ctx)
        await player.set_autoplay(ctx, autoplay)

    @commands.command()
    async def queue(self, ctx):
        player = await self.general_commands._get_guild_player(ctx)
        await player.list_queue(ctx)

async def setup(bot):
    await bot.add_cog(MusicCommands(bot))
    
