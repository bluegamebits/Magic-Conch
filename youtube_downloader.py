import discord
from yt_dlp import YoutubeDL
import aiohttp
import asyncio
import json

ytdl_format_options_get_info = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": False,
    "nocheckcertificate": True,
    "ignoreerrors": True,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # Bind to ipv4 since ipv6 addresses cause issues at certain times
    'geo_bypass': True,# add geo-bypass option,
    'extract_flat': True,
    'skip_download': True,
    'lazy_playlist': True,
}

ytdl_format_options_get_stream = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": True,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # Bind to ipv4 since ipv6 addresses cause issues at certain times
    'geo_bypass': True,# add geo-bypass option,
    'skip_download': True,
}


# Before_options specified for avoiding disconnections when straming
ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                  "options": "-vn"}

ytdl_info = YoutubeDL(ytdl_format_options_get_info)
ytdl_stream = YoutubeDL(ytdl_format_options_get_info)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def get_video_url(self, loop, data, counter=0):
        print("Entering data loop")
        
        if "url" in data:
            data = await loop.run_in_executor(
                None, lambda: ytdl_info.extract_info(data['url'], download=False)
            )    
            data = ytdl_info.sanitize_info(data)
            counter += 1
            print(f"Extractor run: {counter}")
            if data is None:
                print("DATA IS NONE")
                return None

            try:
                if isinstance(data[0], str):
                    print("Data is a astring.")
                    return data
            except Exception as e:
                print(f"Exception at checking if string error: {e}")
            
        if "entries" in data:
            playlist_title = data["title"]
            data = data["entries"]
            song_info = [] 
            song_info.append(playlist_title)
            for song in data:
                video_url = song["url"]
                name_video = song["title"]
                song_info.append([video_url, name_video])
                
            
            return song_info

        elif len(data) != 78:
            data = await YTDLSource.get_video_url(loop, data, counter)
        print("Exit download_loop")
        print(f"Data before video url: {data}")
        try:
            if isinstance(data[0], str):
                print("Data is a astring.")
                return data
        except:
            pass
        video_url = data["url"]
        video_title = data["title"]
        return [video_url, video_title]
        

    @classmethod
    async def play_final(cls, url, *, loop=None, stream=True, verbose=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
                None, lambda: ytdl_stream.extract_info(url, download=False)
            )
        # ℹ️ ydl.sanitize_info makes the info json-serializable
        data = ytdl_stream.sanitize_info(data)
        # open the file for writing
        if(data is None):
            return None
        filename = data["url"] if stream else ytdl_format_options_get_stream.prepare_filename(data)
        print(f"Filename: {filename}")
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True, verbose=False):
        loop = loop or asyncio.get_event_loop()
        
        # serches for video if not a link and chooses the first result, if it is a link it just passes it to youtube-dl to download

        # TODO: Implement choosing between multiple search results

        async def fetch_url(session, url):
            async with session.get(url) as response:
                return await response.text()
            
        async with aiohttp.ClientSession() as session:        
            try:
                await fetch_url(session, url)
            except:
                data = await loop.run_in_executor(
                    None, lambda: ytdl_info.extract_info(f"ytsearch:{url}", download=False)['entries'][0]
                )
                video_url = data["url"]
                video_title = data["title"]
                return [video_url, video_title]
                
            else:
                data = {}
                data["url"] = url
                data = await YTDLSource.get_video_url(loop, data)

        return data