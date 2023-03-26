import asyncio
import os

import discord
from discord.ext import commands
import youtube_dl
import translations

_ = translations.setup_i18n('es')

# Suppress noise about console usage from errorss
youtube_dl.utils.bug_reports_message = lambda: ""

# Add all intents for bot
intents = discord.Intents.all()
intents.members = True

# Define bot variable and activity type
bot = commands.Bot(
    command_prefix=',',
    description=_("Magic conch bot"),
    intents=intents,
    activity = discord.Activity(type=discord.ActivityType.streaming, name='RIP Chabelo',)
)

async def setup_bot():
    await bot.load_extension("player_commands")
    await bot.load_extension("listener")
    await bot.load_extension("conch_voice")

async def main():
    """Load the 'youtube_player' extension, and start the bot using the Discord bot token from the 'Discord_bot_tokens' environment variable.

    Raises:
        KeyError: If the 'Discord_bot_tokens' environment variable is not set.
    """
    async with bot:
        await setup_bot() 
        await bot.start(os.environ['discord2_bot_tokens'])
        


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        # TODO Currently there could be a lot of downloaded .webm files saved to the local folder, below is a 
        # Short term solution until I fix streaming 

        # Removes any downloaded .webm and .mp3 files after program ends
        current_path = os.getcwd()
        for filename in os.listdir(current_path):
            if filename.endswith('.webm') or filename.endswith('.mp3') or filename.endswith('.m4a'):
                file_path = os.path.join(current_path, filename)
                os.remove(file_path)