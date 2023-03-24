import youtube_downloader
import asyncio
import translations

_ = translations.setup_i18n('es')
import discord

from async_timeout import timeout


class Song:
    def __init__(self, source, video_url, added_by):
        self.name = source.title
        self.source = source
        self.video_url = video_url
        self.added_by = added_by

    async def play(self, ctx, bot, song_ended):
        """Plays the given source in the voice channel"""
        print("Playing song: " + self.name)
        print("Added by: " + self.added_by.name)

        try:
            vc = ctx.voice_client
            vc.play(
                self.source, after=lambda _: bot.loop.call_soon_threadsafe(song_ended.set)
            )
            
            embed = discord.Embed(title=_("Now playing"), description=f"[{self.name}]({self.video_url}) [{self.added_by.mention}]", color=0xCFA2D8)
            await ctx.send(embed=embed)
        except asyncio.CancelledError:
                print("Music canceled.")                    
        except Exception as e:
            print(f"Error on Discord player: {e}")
            ctx.send(_("Error on Discord player: ") + e)


class MusicPlayer:
    def __init__(self, bot):
        self.current_song = None
        self.queue = asyncio.Queue()
        self.bot = bot
        self.ctx = None
        self.song_ended = asyncio.Event()
        self.task = None

    def update_ctx(self, ctx):
        self.ctx = ctx


    async def player_loop(self):
        """
        Main player loop
        Plays song when it detect the queue has at least one item
        """
        try:
            while True:
                self.current_song = await self.queue.get()
                await self.current_song.play(self.ctx, self.bot, self.song_ended)
                await self.song_ended.wait()
                self.song_ended.clear()
                self.current_song = None
                    
        except asyncio.CancelledError:
            print("Player disconnected")
            await self.ctx.voice_client.disconnect()

        finally:
            await self.ctx.voice_client.disconnect()

    async def play_song(self, ctx, url):
        if not (await self.join(ctx)):
            return 
        
        task = asyncio.create_task(self.get_source(url))
        source, video_url = await task
        new_song = Song(source, video_url, ctx.author)

        
        await self.queue.put(new_song)

        # Sends message that song has been added to queue only if there is a song playing
        if self.current_song != None:
            print("Added " + new_song.name + " to the queue.")
            embed = discord.Embed(description=_("Queued ") + f"[{new_song.name}]({new_song.video_url}) [{self.ctx.author.mention}]", color=0xCFA2D8)
            await ctx.send(embed=embed)

        # Starts the player loop, only the first time play_song is called
        if not self.task:
            self.task = asyncio.create_task(self.player_loop())
            await self.task

    async def stop(self, ctx):
        """Stops play back and clears current song, queue, stops player task and sets to None"""
        
        if(ctx.voice_client.is_connected()):
            self.current_song = None
            self.queue = asyncio.Queue()
            self.task.cancel()
            await self.task
            self.task = None
            await ctx.send(_("Disconnected from voice channel"))
            print("Stopped playback and cleared queue.")
        else:
            await ctx.send(_("Not playing any music."))

    async def skip(self, ctx):
        if(ctx.voice_client.is_connected()):
            self.ctx.voice_client.stop()
        else:
            await ctx.send(_("Not playing any music."))

    async def join(self, ctx):
        """Joins the voice channel of whoever called the command"""
        try:
            voice_channel = ctx.author.voice.channel 
            #vc = ctx.voice_client
            #vc and vc.is_connected():
            
        except Exception as e:
            if(ctx.voice_client is None):
                await ctx.send(_("Error: Voice client is not connected."))
                return False
            else:
                return True
        
        self.update_ctx(ctx)
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(voice_channel)
        else:
            await voice_channel.connect()
        return voice_channel

    async def get_source(self, url):
        """Retrieves source from url or search"""
        print("Getting source")
        for i in range(10):
            try:
                source, video_url = await youtube_downloader.YTDLSource.from_url(url, loop=self.bot.loop, verbose=True)
                return source, video_url
            except Exception as e:
                print(f"Failed to get source : {e}")
                print(f"Retrying... (attempt {i+1}/10)")
                await asyncio.sleep(1)
        return None