from discord.ext import commands
import discord
import translations

import google_voice
import openai_module
_ = translations.setup_i18n('es')

class voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    async def join(self, ctx):
        """Joins a voice channel, if already in a voice channel it switches to the user's voice channel"""

        voice_channel = ctx.author.voice.channel
        
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(voice_channel)

        await voice_channel.connect()

    @commands.command()
    async def say(self, ctx, *, query):
        """Uses google voice to say the entered message"""
        
        google_voice.talk(query) # Sends the message to google's API and generates file "output.mp3" with recorded message
        vc = await self.join(ctx) # Joins voice channel
        vc = ctx.voice_client # Gets updated voice channel of the bot
        
        try:
            if vc.is_connected():

                # TODO: change this to stream directly from API instead of saving to .mp3 and then playing it
                player = vc.play(discord.FFmpegPCMAudio("output.mp3"))
            else:
                print(_("Error: Voice client is not connected."))
            
        except Exception as e:
            print(_("Error playing audio file: ") + e)

    @commands.command()
    async def ask(self, ctx, *, query):
        """
        Asks the magic conch a question.
        Currently uses Open AI API using the gpt3-turbo model with a modified intial prompt message.
        """
        print("Ask started.")

        try:
            reply = await openai_module.ask_gpt(query)
            await ctx.send(reply)
        except Exception as e:
            print(e)
        print("Ask ended.")

async def setup(bot):
    await bot.add_cog(voice(bot)) 




    