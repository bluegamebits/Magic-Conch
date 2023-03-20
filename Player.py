import youtube_downloader
import asyncio
import translations

_ = translations.setup_i18n('es')
import discord

from async_timeout import timeout


class Song:
    def __init__(self, source, video_url):
        self.name = source.title
        self.source = source
        self.video_url = video_url


class MusicPlayer:
    def __init__(self, bot):
        self.current_song = None
        self.queue = asyncio.Queue()
        self.bot = bot
        self.ctx = None
        self.next = asyncio.Event()
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
                self.next.clear()
                if self.queue.qsize() > 0:
                    await self.play_next_song()
                    await self.next.wait()
                else:
                    await asyncio.sleep(1)
                    
        except asyncio.CancelledError:
            print("Player disconnected")
                

    async def play_song(self, ctx, url):
        self.update_ctx(ctx)
        task = asyncio.create_task(self.get_source(url))
        source, video_url = await task
        new_song = Song(source, video_url)

        # TODO Reduntant if, else block, all it needs to do is add the song to the queue now

        if self.current_song is None:
            self.current_song = new_song
            await self.join(ctx)
            await self.queue.put(new_song)
            print("added song to queue")
            # Starts the player loop, only the first time play_song is called
            if not self.task:
                self.task = asyncio.create_task(self.player_loop())
                await self.task
            
        else:
            await self.queue.put(new_song)
            print("Added " + new_song.name + " to the queue.")
            embed = discord.Embed(description=_("Queued ") + f"[{new_song.name}]({new_song.video_url}) [{self.ctx.author.mention}]", color=0xCFA2D8)
            try:
                await ctx.send(embed=embed)
            except Exception as e:
                print(e)

    async def play_next_song(self):
        # TODO: Redundant if check as function is only called if there is already a song in the queue
        if not self.queue.empty():
            self.current_song = await self.queue.get()
            await self.join(self.ctx)
            try:
                self.play_music_task = asyncio.create_task(self.play_music(self.current_song))
                await self.play_music_task
            except Exception as e:
                print(f"Error on playing music: {e}")
        else:
            print(self.queue)

    async def stop(self, ctx):
        """Stops play back and clears current song, queue, stops player task and sets to None"""
        self.update_ctx(ctx)
        if(ctx.voice_client.is_connected()):
            self.current_song = None
            self.queue = asyncio.Queue()
            self.task.cancel()
            await self.task
            self.task = None
            print("Stopped playback and cleared queue.")
        else:
            await ctx.send(_("Not playing any music."))

    async def skip(self, ctx):
        self.update_ctx(ctx)
        if(ctx.voice_client.is_connected()):
            self.play_music_task.cancel()
            self.ctx.voice_client.stop()
        else:
            await ctx.send(_("Not playing any music."))

    async def join(self, ctx):
        """Joins the voice channel of whoever called the command"""
        self.update_ctx(ctx)
        voice_channel = ctx.author.voice.channel
        
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(voice_channel)

        await voice_channel.connect()

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
    
    async def play_music(self, song):
        """Plays the given source in the voice channel"""
        print("Playing music")

        try:
            
            vc = self.ctx.voice_client
            try:
                vc.play(
                    song.source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set)
                )
            except asyncio.CancelledError:
                print("Music canceled.")
            embed = discord.Embed(title=_("Now playing"), description=f"[{song.name}]({song.video_url}) [{self.ctx.author.mention}]", color=0xCFA2D8)
            await self.ctx.send(embed=embed)
                           
        except Exception as e:
            print(f"Error on Discord player: {e}")
            self.ctx.send(_("Error on Discord player: ") + e)