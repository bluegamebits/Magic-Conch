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
        await self.player.join(ctx)
                       
    @commands.command()
    async def play(self, ctx, *, url):
        await self.player.play_song(ctx, url)

    @commands.command()
    async def pause(self, ctx):
        await self.player.pause(ctx)

    @commands.command()
    async def unpause(self, ctx):
        await self.player.unpause(ctx)

    @commands.command()
    async def stop(self, ctx):
        await self.player.stop(ctx)
        
    @commands.command()
    async def skip(self, ctx):
        await self.player.skip(ctx)

    @commands.command()
    async def volume(self, ctx, volume: int):
        await self.player.volume(ctx, volume)

    @commands.command()
    async def purge(self, ctx):
        await self.player.purge_queue(ctx)

    @commands.command()
    async def previous(self, ctx):
        await self.player.play_previous_song(ctx)

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Listens to bot messages and updates player.ctx
        Used only for testing purpouses
        """
        if not message.author.bot:  # Ignore non-bot messages
            return
        self.player.ctx =  await self.bot.get_context(message)

async def setup(bot):
    await bot.add_cog(PlayerCommands(bot))
    
