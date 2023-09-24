import youtube_downloader
import asyncio
import translations

_ = translations.setup_i18n('es')
import discord

from async_timeout import timeout
import collections
import itertools

import asyncio

class SongQueue:
    class QueueEmpty(Exception):
        """Exception raised when trying to get an item from an empty queue."""
        pass

    def __init__(self):
        self._deque = collections.deque()
        self._condition = asyncio.Condition()

    async def put(self, item):
        async with self._condition:
            self._deque.append(item)
            self._condition.notify_all()
            
    async def put_left(self, item):
        async with self._condition:
            self._deque.appendleft(item)
            self._condition.notify_all()

    async def get(self):
        async with self._condition:
            while not self._deque:
                await self._condition.wait()
            return self._deque.popleft()
        
    async def get_right_nowait(self):
        async with self._condition:
            return self._deque.pop()
        
    async def get_nowait(self):
        async with self._condition:
            if not self._deque:
                raise self.QueueEmpty("The queue is empty.")
            return self._deque.popleft()
        
    async def size(self):
        async with self._condition:
            return len(self._deque)
    
    async def get_copy(self):
        async with self._condition:
            return list(self._deque)
        
    async def set_copy(self, list):
        if(list):
            async with self._condition:
                self._deque = collections.deque(list)
        else:
            return
        
    async def empty_queue(self):
        async with self._condition:
                queue_size = len(self._deque)
                try:
                    self._deque.clear()
                except:
                    return 0
                return queue_size
        
class Song:
    def __init__(self, video_url, song_title, added_by, autoplay=False):
        self.name = song_title
        self.video_url = video_url
        self.added_by = added_by
        if self.added_by == "Autoplay":
            self.autoplay = " [Autoplay]"
        else:
            self.autoplay = ""

    async def play(self, ctx, bot, song_ended, volume):
        """Plays the given source in the voice channel"""
        print("Playing song: " + self.name)
        if self.autoplay:
            print("Added by: Autoplay")
        else:
            print("Added by: " + self.added_by.name)

        vc = ctx.voice_client

        try:
            source = await youtube_downloader.YTDLSource.play_final(self.video_url)
        except Exception as e:
            print(e)
            source = None

        if(source):
            try:
                source.volume = volume
                vc.play(
                    source, after=lambda _: bot.loop.call_soon_threadsafe(song_ended.set)
                )
            except Exception as e:
                print(f"error on playback {e}")
                bot.loop.call_soon_threadsafe(song_ended.set)
                return

            if self.added_by == "Autoplay":
                embed = discord.Embed(title=_("Now playing") + self.autoplay, description=f"[{self.name}]({self.video_url})", color=0xCFA2D8)
            else: 
                embed = discord.Embed(title=_("Now playing") + self.autoplay, description=f"[{self.name}]({self.video_url}) [{self.added_by.mention}]", color=0xCFA2D8)
            await ctx.send(embed=embed)
        else:
            print("No source")
            bot.loop.call_soon_threadsafe(song_ended.set)

class MusicPlayer:
    def __init__(self, bot):
        self.current_song = None
        # TODO: Rewrite to use deque instead of asyncio
        self.queue = SongQueue()
        self.autoplay_queue = SongQueue()
        self.finished_queue = SongQueue()
        self.bot = bot
        self.ctx = None
        self.song_ended = asyncio.Event()
        self.task = None
        self.autoplay = False
        self.guild_data = {}
        print("Finished starting new MusicPlayer class.")

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
                self.current_song = await self.queue.get()
                await self.current_song.play(self.ctx, self.bot, self.song_ended, self.player_volume)
                await self.song_ended.wait()
                if(self.autoplay and await self.queue.size() == 0):
                    if(await self.autoplay_queue.size() == 0):
                        print("getting more autoplay.. ")
                        source = await youtube_downloader.YTDLSource.get_recommended(self.current_song.video_url)
                        for video_url, song_title in source[1:]:
                            new_song = Song(video_url, song_title, "Autoplay", True)
                            await self.autoplay_queue.put(new_song)
                    await self.queue.put(await self.autoplay_queue.get())
                else:
                    print("no autoplay")
                
                if self.current_song:
                    await self.finished_queue.put(self.current_song)
                    self.current_song = None
                self.song_ended.clear()
                    
        except asyncio.CancelledError:
            try:    
                await self.ctx.voice_client.disconnect()
                await self.ctx.voice_client.voice_disconnect()
            except Exception as e:
                print(e)

    async def _add_to_queue(self, ctx, source, autoplay=False, silent=False):
        print(source)
        if len(source) > 2:
            num_of_songs = len(source) - 1 
            embed = discord.Embed(description=_("Queued ") + f"{num_of_songs} canciones.", color=0xCFA2D8)
            await ctx.send(embed=embed)
            for video_url, song_title in source[1:]:
                new_song = Song(video_url, song_title, ctx.author, autoplay)
                await self.queue.put(new_song)
                
        else:
            video_url, song_title = source
            print(f"Autoplay: {autoplay}")
            if autoplay: 
                new_song = Song(video_url, song_title, "Autoplay")
            else:
                new_song = Song(video_url, song_title, ctx.author)
                print("autoplay about to be emptied.")
                await self.autoplay_queue.empty_queue()
            await self.queue.put(new_song)
            print(f"Song = {new_song}")
            if self.current_song != None and autoplay == False:
                embed = discord.Embed(description=_("Queued ") + f"[{new_song.name}]({new_song.video_url}) [{self.ctx.author.mention}]", color=0xCFA2D8)
                await ctx.send(embed=embed)

    async def play_song(self, ctx, url):

        timeout_seconds = 5

        async with ctx.typing():
            if not (await self.join(ctx, print_message=False)):
                print("Unable to join Voice channel.")
                return 
            print("Joined Voice channel.")

            try:
                task = asyncio.create_task(self._get_source(url))
                source = await asyncio.wait_for(task, timeout=timeout_seconds)
            except asyncio.TimeoutError:
                await ctx.send(f"The operation timed out after {timeout_seconds} seconds.")
                return
            except Exception as e:
                await ctx.send(f"An error occured: {str(e)}")
                return

            print("Got source.")
            await self._add_to_queue(ctx, source)
            print("Added to queue.")            
        # Starts the player loop, only the first time play_song is called
            if not self.task:
                print("Started new music loop.")
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
            print(e)
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
            self.queue = SongQueue()
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

    async def skip(self, ctx, print_messages=True, songs=1):
        """Skips the current song"""
        vc = ctx.voice_client
        if not print_messages:
            vc.stop()
        if vc and vc.is_playing() or vc and vc.is_paused():
            vc.stop()
            await ctx.message.add_reaction('⏭️') 
        else:
            print("Error on skip: Voice client is not connected.")

    async def play_previous_song(self, ctx):
        """Plays previous song and puts current song in queue"""
        if(await self.finished_queue.size() < 1):
            return
        
        previous_song = await self.finished_queue.get_right_nowait()
        current_song = self.current_song
        
        if not (self.current_song):
            await self.queue.put_left(previous_song)
        else:
            await self.queue.put_left(current_song)
            await self.queue.put_left(previous_song)

        self.current_song = None
        await self.skip(ctx, print_messages=False)
        await ctx.message.add_reaction('⏮️') 
        

    async def purge_queue(self, ctx):
        """Erases all songs from the queue"""
        queue_size = await self.queue.empty_queue()

        if queue_size == 1:
            await ctx.send(f"{queue_size} song has been removed from the queue.")
        elif queue_size > 1:
            await ctx.send(f"{queue_size} songs have been removed from the queue.")
        else:
            await ctx.send(f"Queue is already empty.")
        return queue_size

    async def list_queue(self, ctx):
        """Shows the current queue"""
        print("Got to list!")
        if await self.queue.size() < 1 and self.current_song == None:
            return
        
        current_queue = await self.queue.get_copy()
        queue_txt = f"```1) {self.current_song.name} <- Current song\n"
        i = 1
        for song in current_queue:
            i += 1
            queue_txt += f"{i}) {song.name}\n"
        queue_txt += "```"
        if(i > 1):
            title = f"Curent Queue ({i} songs)"
        else: 
            title = f"Curent Queue ({i} song)"

        embed = discord.Embed(title=title, description=f"{queue_txt}", color=0xCFA2D8)
        await ctx.send(embed=embed)

    async def volume(self, ctx, volume):
        """Changes the player's volume"""
        volume = int(volume)
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
            try:
                source = await youtube_downloader.YTDLSource.from_url(url, loop=self.bot.loop, verbose=True)
                return source
            except Exception as e:
                print(f"Error on getting source: {e}")
            print(f"Failed to get source : {e}")
            print(f"Retrying... (attempt {i+1}/10)")
            await asyncio.sleep(1)
        return None