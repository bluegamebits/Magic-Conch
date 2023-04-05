
import pytest
import asyncio
import pytest_asyncio
import os
from unittest.mock import AsyncMock, MagicMock
from unittest import mock
from discord.ext.commands import Context
import discord
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import main


import bot_test
from discord import TextChannel
import Player
from discord.ext import commands

import translations
_ = translations.setup_i18n('es')

TEST_CHANNEL_ID = 1088963044916346972
TEST_GUILD_ID = 888655154889502790
TEST_VC_ID = 888655154889502794

async def wait_until_ready(bot):
    """Wait until the bot is ready."""
    await bot.wait_until_ready()

@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope='session', autouse=True)
async def bots_setup():

    
    # Setup code
    print("Setting up magic conch")
    await main.setup_bot()
    await bot_test.setup_bot()
    # Start the bot discord2_bot_tokens
    main_bot = asyncio.create_task(main.bot.start(os.environ['discord2_bot_tokens']))
    tester_bot = asyncio.create_task(bot_test.bot.start(os.environ['discord3_bot_tokens']))

    

    await asyncio.gather(wait_until_ready(main.bot), wait_until_ready(bot_test.bot))
    #main.bot.add_listener(main.bot.get_cog('PlayerCommands').custom_on_message, 'on_message')

    yield

    print("Tearing down.")

    try:
        await main.bot.close()
        await bot_test.bot.close()
        await main_bot
        await tester_bot
    except Exception as e:
        pass

async def wait_for_message(channel, timeout=5):
    def check(msg):
        return msg.channel == channel and msg.author == main.bot.user

    try:
        message = await main.bot.wait_for('message', check=check, timeout=timeout)
        return message
    except asyncio.TimeoutError:
        return None
    
async def wait_for_song_to_start(vc, timeout):
    seconds = 0
    try:
        while not (vc.is_playing() or vc is None):
            await asyncio.sleep(1)
            if(seconds>timeout):
                break
            seconds += 1
        if not (vc.is_playing()):
            print("ERROR, VC TIMEOUT")
    except Exception as e:
        print(e)
async def _cleanup_vc(player_commands_cog, test_vc, ctx):

    #if(ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):

    await player_commands_cog.stop(ctx)
    await test_vc.voice_disconnect()
    await test_vc.disconnect()
    await asyncio.sleep(2)

async def join_bots_to_vc():
    """
    Joins the bots to the voice channel
    
    Returns: ctx, test_vc and player_commands_cog
    """
    guild = bot_test.bot.get_guild(TEST_GUILD_ID)
    voice_channel = guild.get_channel(TEST_VC_ID)
    test_vc = await voice_channel.connect()
    text_channel: TextChannel = guild.text_channels[2]
    player = main.bot.get_cog('PlayerCommands').player
    
    await text_channel.send(',join')
    await asyncio.sleep(2)
    ctx = player.ctx
    print("Before cog join")
    await player.join(ctx)
    print("after cog join") 
    return ctx, test_vc, player
@pytest.mark.asyncio
async def test_song_types(bots_setup):
    # Search term
    guild = bot_test.bot.get_guild(TEST_GUILD_ID)
    text_channel: TextChannel = guild.text_channels[2]
    ctx, test_vc, player = await join_bots_to_vc()
    print("Testing video search term")
    song_loop = asyncio.create_task(player.play_song(ctx, "The Legend of Zelda: Breath of the Wild - Theme (SoundTrack)"))
    vc = ctx.voice_client
    await wait_for_song_to_start(vc, 10)
    assert vc.is_playing()
    await asyncio.sleep(2)
    await player.skip(ctx)
    
   
    print("Testing single video watch link")
    song_loop = asyncio.create_task(player.play_song(ctx, "https://www.youtube.com/watch?v=cPWBG6_jn4Y"))
    vc = ctx.voice_client
    await wait_for_song_to_start(vc, 10)
    assert vc.is_playing()
    await asyncio.sleep(2)
    await player.skip(ctx)
    
    print("Testing playlist watch link")
    song_loop = asyncio.create_task(player.play_song(ctx, "https://www.youtube.com/watch?v=xGi23M_5lXg&list=PLh4Eme5gACZEAazTK1vSZn3DCYJLQ4YHH"))
    vc = ctx.voice_client
    await wait_for_song_to_start(vc, 100)
    assert vc.is_playing()
    await asyncio.sleep(2)
    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    queue_size = await player.purge_queue(ctx)
    response_msg = await response_msg
    assert response_msg.content == f"{queue_size} songs have been removed from the queue."
    
    print("Testing playlist playlist link")
    song_loop = asyncio.create_task(player.play_song(ctx, "https://www.youtube.com/playlist?list=PLh4Eme5gACZEAazTK1vSZn3DCYJLQ4YHH"))
    vc = ctx.voice_client
    await wait_for_song_to_start(vc, 10)
    assert vc.is_playing()
    await asyncio.sleep(2)
    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    queue_size = await player.purge_queue(ctx)
    response_msg = await response_msg
    assert response_msg.content == f"{queue_size} songs have been removed from the queue."
    
    # TODO: Fix streaming youtube links
    #print("Testing stream link")
    #song_loop = asyncio.create_task(player.play_song(ctx, "https://www.youtube.com/watch?v=jfKfPfyJRdk"))
    #vc = ctx.voice_client
    #await wait_for_song_to_start(vc, 10)
    #assert vc.is_playing()
    #await asyncio.sleep(2)
    #await player.skip(ctx)

    await _cleanup_vc(player, test_vc, ctx)


@pytest.mark.asyncio
async def test_commands_while_song_playing(bots_setup):
    guild = bot_test.bot.get_guild(TEST_GUILD_ID)
    text_channel: TextChannel = guild.text_channels[2]
    ctx, test_vc, player = await join_bots_to_vc()
    
    await player.play_song(ctx, "Neon Genesis Evangelion — FLY ME TO THE MOON — CLAIRE (ED Ending Full NGE OST Soundtrack Lyrics")
    vc = ctx.voice_client
    
    await wait_for_song_to_start(vc, 10)
        
    assert vc.is_playing()

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.join(ctx) 
    response_msg = await response_msg
    assert response_msg == None

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.stop(ctx) 
    response_msg = await response_msg
    assert response_msg == None
    assert main.bot.user.id not in [member.id for member in test_vc.channel.members]

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.play_song(ctx, "Zelda botw theme") 
    response_msg = await response_msg
    vc = ctx.voice_client
    await wait_for_song_to_start(vc, 10)
    assert vc.is_playing()

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.pause(ctx) 
    response_msg = await response_msg
    assert response_msg.content == (_("Audio playback paused."))
    assert vc.is_paused()

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.unpause(ctx) 
    response_msg = await response_msg
    assert response_msg.content == _("Audio playback resumed")
    await wait_for_song_to_start(vc, 10)
    assert not vc.is_paused()

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.volume(ctx, 200) 
    response_msg = await response_msg
    assert response_msg.content == _("Volume changed to ") + "200%"

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.skip(ctx) 
    response_msg = await response_msg
    assert response_msg.content == _("Skipped song")

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.stop(ctx) 
    response_msg = await response_msg
    assert response_msg is None
    assert not vc.is_playing()
    assert main.bot.user.id not in [member.id for member in test_vc.channel.members]

    await _cleanup_vc(player, test_vc, ctx)

@pytest.mark.asyncio
async def test_add_songs(bots_setup):
    guild = bot_test.bot.get_guild(TEST_GUILD_ID)
    text_channel: TextChannel = guild.text_channels[2]
    ctx, test_vc, player = await join_bots_to_vc()

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=10))
    await player.play_song(ctx, "Neon Genesis Evangelion — FLY ME TO THE MOON — CLAIRE (ED Ending Full NGE OST Soundtrack Lyrics")
    response_msg = await response_msg
    assert response_msg.embeds[0].title == _("Now playing")
    assert response_msg.embeds[0].description ==  "[Neon Genesis Evangelion — FLY ME TO THE MOON — CLAIRE (ED Ending Full NGE OST Soundtrack Lyrics)](https://www.youtube.com/watch?v=Ixi0sUpLVRc) [<@1089295072782188585>]"
    
    vc = ctx.voice_client
    
    await wait_for_song_to_start(vc, 10)
        
    assert vc.is_playing()

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=10))
    await player.play_song(ctx, "Re:ZERO - Starting Life in Another World - Opening | Redo")
    response_msg = await response_msg
    assert response_msg.embeds[0].description == _("Queued ") + "[Re:ZERO - Starting Life in Another World - Opening | Redo](https://www.youtube.com/watch?v=0Vwwr3VGsYg) [<@1089295072782188585>]"
    
    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=10))
    await player.play_song(ctx, "Rick and Morty Theme Song [HD]")
    response_msg = await response_msg
    print(response_msg.embeds[0].description)
    assert response_msg.embeds[0].description == _("Queued ") + "[Rick and Morty Theme Song [HD]](https://www.youtube.com/watch?v=wh10k2LPZiI) [<@1089295072782188585>]"

    assert player.queue.qsize() == 2

    await _cleanup_vc(player, test_vc, ctx)

@pytest.mark.asyncio
async def test_play_song(bots_setup):
    
    ctx, test_vc, player = await join_bots_to_vc()
    
    song_loop = asyncio.create_task(player.play_song(ctx, "Neon Genesis Evangelion — FLY ME TO THE MOON — CLAIRE (ED Ending Full NGE OST Soundtrack Lyrics"))
    vc = ctx.voice_client
    
    await wait_for_song_to_start(vc, 10)
        
    assert vc.is_playing()

    await _cleanup_vc(player, test_vc, ctx)

@pytest.mark.asyncio
async def test_commands_while_joined_but_not_playing(bots_setup):
    text_channel = bot_test.bot.get_guild(TEST_GUILD_ID).text_channels[2]

    # Make the test bot join the voice channel
    ctx, test_vc, player = await join_bots_to_vc()
    assert main.bot.user.id in [member.id for member in test_vc.channel.members]

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.join(ctx) 
    response_msg = await response_msg
    assert response_msg is None

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.pause(ctx) 
    response_msg = await response_msg
    assert response_msg.content == (_("No audio is currently playing."))

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.unpause(ctx) 
    response_msg = await response_msg
    assert response_msg.content == (_("No audio is currently playing."))

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.skip(ctx) 
    response_msg = await response_msg
    assert response_msg.content == (_("Error: Voice client is not connected."))

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.volume(ctx, 100) 
    response_msg = await response_msg
    assert response_msg.content == (_("No audio is currently playing."))

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.stop(ctx) 
    response_msg = await response_msg
    assert response_msg is None
    assert main.bot.user.id not in [member.id for member in test_vc.channel.members]

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.join(ctx) 
    response_msg = await response_msg
    assert response_msg is None
    assert main.bot.user.id in [member.id for member in test_vc.channel.members]

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.stop(ctx) 
    response_msg = await response_msg
    assert response_msg == None
    assert main.bot.user.id not in [member.id for member in test_vc.channel.members]
    
    # Cleanup
    await _cleanup_vc(player, test_vc, ctx)

@pytest.mark.asyncio
async def test_get_source(bots_setup):
    player = main.bot.get_cog('PlayerCommands').player
    url_search_term = "rick astley - never gonna give you up (official music video)"
    url_direct_link = "https://www.youtube.com/watch?v=Ixi0sUpLVRc"

    source, video = await player._get_source(url_search_term)
    url_search_title = "Rick Astley - Never Gonna Give You Up (Official Music Video)"
    url_search_link = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    assert source.title == url_search_title and video == url_search_link

    url_direct_link_title = "Neon Genesis Evangelion — FLY ME TO THE MOON — CLAIRE (ED Ending Full NGE OST Soundtrack Lyrics)"
    source, video = await player._get_source(url_direct_link)
    assert source.title == url_direct_link_title and video == url_direct_link

@pytest.mark.asyncio
async def test_commands_while_not_in_voice_channel(bots_setup):
    guild = bot_test.bot.get_guild(TEST_GUILD_ID)
    text_channel: TextChannel = guild.text_channels[2]
    player = main.bot.get_cog('PlayerCommands').player

    await text_channel.send(',join')
    ctx = player.ctx

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.join(ctx) 
    response_msg = await response_msg
    assert response_msg.content == (_("Error: Voice client is not connected."))

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.stop(ctx) 
    response_msg = await response_msg
    assert response_msg.content == (_("Error: Voice client is not connected."))

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.play_song(ctx, None) 
    response_msg = await response_msg
    assert response_msg.content == (_("Error: Voice client is not connected."))

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.pause(ctx) 
    response_msg = await response_msg
    assert response_msg.content == (_("Error: Voice client is not connected."))

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.unpause(ctx) 
    response_msg = await response_msg
    assert response_msg.content == _("No audio is currently playing.")

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.stop(ctx) 
    response_msg = await response_msg
    assert response_msg.content == (_("Error: Voice client is not connected."))

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.skip(ctx) 
    response_msg = await response_msg
    assert response_msg.content == (_("Error: Voice client is not connected."))

    response_msg = asyncio.create_task(wait_for_message(text_channel, timeout=5))
    await player.volume(ctx, 100) 
    response_msg = await response_msg
    assert response_msg.content == _("No audio is currently playing.")

@pytest.mark.asyncio
async def test_join_command_while_in_other_voice_channel(bots_setup):
    guild = bot_test.bot.get_guild(TEST_GUILD_ID)
    text_channel: TextChannel = guild.text_channels[2]
    ctx, test_vc, player = await join_bots_to_vc() 
    
    # Move the test bot to another channel
    await test_vc.move_to(guild.get_channel(1085346054905528421))
    await text_channel.send(',join')
    ctx = player.ctx

    # Execute join command with ctx
    await player.join(ctx)    
    voice_channel = guild.get_channel(1085346054905528421)
    await asyncio.sleep(2)
    assert main.bot.user.id in [member.id for member in voice_channel.members]
    # Cleanup
    await _cleanup_vc(player, test_vc, ctx)

