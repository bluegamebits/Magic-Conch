import main
import pytest
import asyncio
import pytest_asyncio
import os
from unittest.mock import AsyncMock, MagicMock
import bot_test
from discord import TextChannel
import Player
from discord.ext import commands

import translations
_ = translations.setup_i18n('es')

TEST_CHANNEL_ID = 1088963044916346972
player = Player.MusicPlayer(main.bot)

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

    yield

    print("Tearing down.")

    try:
        await main.bot.close()
        await main_bot
    
        await bot_test.bot.close()
        await tester_bot
    except Exception as e:
        pass

@pytest.mark.asyncio
async def test_first(bots_setup):

    test_message_content = ",ping"

    # Send the test message using the test bot
    sent_message = await bot_test.send_test_message(TEST_CHANNEL_ID, test_message_content)

    async def wait_for_main_bot_reply():
        def is_main_bot_reply(message):
            return message.author == main.bot.user and message.reference.message_id == sent_message.id

        try:
            reply = await main.bot.wait_for("message", check=is_main_bot_reply, timeout=4)
        except asyncio.TimeoutError:
            raise AssertionError("Main bot did not reply in time")
        return reply
    
    main_bot_reply = await wait_for_main_bot_reply()
    assert main_bot_reply.content == "Pong!", f"Expected 'Pong!', but got '{main_bot_reply.content}'"


@pytest.mark.asyncio
async def test_commands_while_not_connected_to_vc(bots_setup):
    single_commands = {
        "join": _("Not currently connected to a voice channel"),
        "pause": _("Not currently connected to a voice channel"),
        "unpause": _("Not currently connected to a voice channel"),
        "stop": _("Not currently connected to a voice channel"),
        "skip": _("Not currently connected to a voice channel"),
        "volume": _("Not currently connected to a voice channel"), 
    }

    for command, expected_output in single_commands.items():
        try:
            
            
            if command in globals():
                player.globals()[command]()


        except Exception as e:
            print(e)

@pytest.mark.asyncio
async def test_join_command(bots_setup):
    
    await player.join(player.bot)