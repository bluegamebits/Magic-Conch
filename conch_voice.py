from discord.ext import commands
import google_voice


import discord


class voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    async def join(self, ctx):
        """Joins a voice channel, if already in a voice channel it switches to the user's voice channel"""
        
        print(self.bot.user)

        voice_channel = ctx.author.voice.channel
        
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(voice_channel)

        await voice_channel.connect()

    @commands.command()
    async def say(self, ctx, *, query):
        """Uses google voice to say the entered message"""
        
        google_voice.talk(query) # Sends the message to google's API and generates file "output.mp3" with recorded message


        vc = await self.join(ctx) 



        vc = ctx.voice_client # Gets updated voice channel of the bot
    
        
        try:
            #player = vc.play(discord.FFmpegPCMAudio("output.mp3"), after=disconnect)
            if vc.is_connected():
                #player = vc.play(discord.FFmpegPCMAudio("output.mp3"))

                # TODO: change this to stream directly from API instead of saving to .mp3 and then playing it
                player = vc.play(discord.FFmpegPCMAudio("output.mp3"))
            else:
                print("Voice client is not connected.")
            
        
        except Exception as e:
            print(f"Error playing audio file: {e}")

async def setup(bot):
    await bot.add_cog(voice(bot)) 




    