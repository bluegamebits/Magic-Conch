import asyncio
import os

import discord
from discord.ext import commands
import youtube_dl
import translations

# Add all intents for bot
intents = discord.Intents.all()
intents.members = True

# Define bot variable and activity type
bot = commands.Bot(
    command_prefix=',',
    description="Magic conch tester",
    intents=intents,
    #activity = discord.Activity(type=discord.ActivityType.listening, name='',)
)

async def setup_bot():
    pass

async def send_test_message(channel_id, message):
    print(channel_id)

    await bot.wait_until_ready() 
    channel = bot.get_channel(channel_id)
    if channel:
        return await channel.send(message)
    else:
        raise ValueError("Invalid channel ID")
        


if __name__ == "__main__":
    try:
        pass
    finally:
        # TODO Currently there could be a lot of downloaded .webm files saved to the local folder, below is a 
        # Short term solution until I fix streaming 

        # Removes any downloaded .webm and .mp3 files after program ends
        pass