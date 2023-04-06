import youtube_downloader
import asyncio
import translations

_ = translations.setup_i18n('es')
import discord

from async_timeout import timeout

class Song:
    def __init__(self, video_url, song_title, added_by):
        self.name = song_title
        self.video_url = video_url
        self.added_by = added_by

    async def play(self, ctx, bot, song_ended, volume):
        """Plays the given source in the voice channel"""
        print("Playing song: " + self.name)
        print("Added by: " + self.added_by.name)

        vc = ctx.voice_client
        source = await youtube_downloader.YTDLSource.play_final(self.video_url)
        if(source):
            source.volume = volume
            vc.play(
                source, after=lambda _: bot.loop.call_soon_threadsafe(song_ended.set)
            )
        
            embed = discord.Embed(title=_("Now playing") + " [Autoplay]", description=f"[{self.name}]({self.video_url}) [{self.added_by.mention}]", color=0xCFA2D8)
            await ctx.send(embed=embed)
        else:
            print("No source")
            bot.loop.call_soon_threadsafe(song_ended.set)

class MusicPlayer:
    def __init__(self, bot):
        self.current_song = None
        # TODO: Rewrite to use deque instead of asyncio
        self.queue = asyncio.Queue()
        self.finished_queue = asyncio.Queue()
        self.bot = bot
        self.ctx = None
        self.song_ended = asyncio.Event()
        self.task = None
        self.autoplay = False

    async def update_ctx(self, ctx):
        self.ctx = ctx

    async def player_loop(self):
        """
        Main player loop
        Plays song when it detects the queue has at least one item
        """
        try:
            self.song_ended.clear()
            self.player_volume = 0.5  
            while True:
                print("loopy loop start")
                
                self.current_song = await self.queue.get()
                await self.current_song.play(self.ctx, self.bot, self.song_ended, self.player_volume)
                await self.song_ended.wait()
                if(self.autoplay and self.queue.qsize() == 0):
                    video_url, song_title = await youtube_downloader.YTDLSource.get_recommended(self.current_song.video_url, self.finished_queue)
                    await self.queue.put(Song(video_url, song_title, self.ctx.author))
                if self.current_song:
                    await self.finished_queue.put(self.current_song)
                    self.current_song = None
                self.song_ended.clear()
                    
        except asyncio.CancelledError:
            try:    
                await self.ctx.voice_client.disconnect()
                await self.ctx.voice_client.voice_disconnect()
            except Exception as e:
                pass

    async def _add_to_queue(self, ctx, source):
        print(source)
        if len(source) > 2:
            num_of_songs = len(source) - 1 
            embed = discord.Embed(description=_("Queued ") + f"{num_of_songs} canciones.", color=0xCFA2D8)
            await ctx.send(embed=embed)
            for video_url, song_title in source[1:]:
                new_song = Song(video_url, song_title, ctx.author)
                await self.queue.put(new_song)
                
        else:
            video_url, song_title = source
            new_song = Song(video_url, song_title, ctx.author)
            await self.queue.put(new_song)
            if self.current_song != None:
                embed = discord.Embed(description=_("Queued ") + f"[{new_song.name}]({new_song.video_url}) [{self.ctx.author.mention}]", color=0xCFA2D8)
                await ctx.send(embed=embed)

    async def play_song(self, ctx, url):
        if not (await self.join(ctx, print_message=False)):
            return 
        
        task = asyncio.create_task(self._get_source(url))
        source = await task
        await self._add_to_queue(ctx, source)

        # Starts the player loop, only the first time play_song is called
        if not self.task:
            self.task = asyncio.create_task(self.player_loop())
    async def set_autoplay(self, ctx, autoplay):
        """Sets autoplay on or off"""
        if autoplay.lower() == "on":
           self.autoplay = True
           await ctx.send("🎶 Autoplay on 🔁")
        elif autoplay.lower() == "off":
            self.autoplay = False
            await ctx.send("🎶 Autoplay off 🚫")


    async def join(self, ctx, print_message=True):
        """Joins the voice channel of whoever called the command"""
        try:
            voice_channel = ctx.author.voice.channel 
            
        except Exception as e:
            print("Error on join: Voice client is not connected.")
            return False
        
        try:
            if ctx.voice_client is not None:
                await self.update_ctx(ctx)
                await ctx.voice_client.move_to(voice_channel)
                

            else:
                await self.update_ctx(ctx)
                await voice_channel.connect()
            if print_message:
                await ctx.message.add_reaction('🔊')
        except Exception as e:
            return False
        return True

    async def pause(self, ctx):
        """Pauses the current audio playback"""
        if(ctx.voice_client is None):
            print("Error: Voice client is not connected.")
            return
        
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.message.add_reaction('⏸️')


            #await ctx.send(_("Audio playback paused."))
        else:
            print("No audio is currently playing.")

    async def unpause(self, ctx):
        """Unpauses the currently playing audio"""
        vc = ctx.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await ctx.message.add_reaction('▶️')
        else:
            print("No audio is currently playing.")

    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        vc = ctx.voice_client
        self.current_song = None
        if vc and vc.is_connected() and self.task:
            
            self.current_song = None
            self.queue = asyncio.Queue()
            self.task.cancel()
            await self.task
            self.task = None
            await ctx.message.add_reaction('⏹️') 
        elif vc and vc.is_connected():
            await vc.voice_disconnect()
            await vc.disconnect()
            await ctx.message.add_reaction('⏹️') 
        else:
            print("Error on stop: Voice client is not connected.")

    async def skip(self, ctx, print_messages=True):
        """Skips the current song"""
        vc = ctx.voice_client
        if not print_messages:
            vc.stop()
            return
        if vc and vc.is_playing() or vc and vc.is_paused():
            vc.stop()
            await ctx.message.add_reaction('⏭️') 
        else:
            print("Error on skip: Voice client is not connected.")

    async def play_previous_song(self, ctx):
        """Plays previous song and puts current song in queue"""
        if(self.finished_queue.qsize() < 1):
            return
        temp_list = []
        while not self.finished_queue.empty():
            try:
                temp_list.append(self.finished_queue.get_nowait())
            except asyncio.QueueEmpty:
                break

        previous_song = temp_list.pop()
        for song in temp_list:
            await self.finished_queue.put(song)

        temp_list = []
        while not self.queue.empty():
            try:
                temp_list.append(self.queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        
        temp_list.insert(0, previous_song)
        if(self.current_song):
            temp_list.insert(1, self.current_song)
        for song in temp_list:
            await self.queue.put(song)

        self.current_song = None
        await self.skip(ctx, print_messages=False)
        await ctx.message.add_reaction('⏮️') 
        

    async def purge_queue(self, ctx):
        """Erases all songs from the queue"""
        queue_size = self.queue.qsize()

        while not self.queue.empty():
            try:
                item = self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break
    
        self.current_song = None
        if queue_size == 1:
            await ctx.send(f"{queue_size} song has been removed from the queue.")
        elif queue_size > 1:
            await ctx.send(f"{queue_size} songs have been removed from the queue.")
        else:
            await ctx.send(f"Queue is already empty.")
        return queue_size

    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""
        vc = ctx.voice_client
        if vc and vc.source and vc.is_connected():
            vc.source.volume = volume / 100
            self.player_volume = volume / 100
            await ctx.send(_("Volume changed to ") + str(volume) + "%")
        else:
            await ctx.send(_("No audio is currently playing."))

    async def _get_source(self, url):
        """Retrieves source from url or search"""
        print("Getting source")
        for i in range(10):

            source = await youtube_downloader.YTDLSource.from_url(url, loop=self.bot.loop, verbose=True)
            return source

            print(f"Failed to get source : {e}")
            print(f"Retrying... (attempt {i+1}/10)")
            await asyncio.sleep(1)
        return None