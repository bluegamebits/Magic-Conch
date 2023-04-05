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
    'simulate': True,
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
ytdl_stream = YoutubeDL(ytdl_format_options_get_stream)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def get_video_url(self, loop, data, counter=0):
        # Initial extraction to get video url from youtube
        data = await loop.run_in_executor(
                None, lambda: ytdl_info.extract_info(data['url'], download=False)
            )
        
        # If video is a url and needs further extraction
        if data.get("_type") == "url":
            print("url")
            data = await loop.run_in_executor(
                None, lambda: ytdl_info.extract_info(data['url'], download=False)
            )

        # if video is a playlist
        if data.get("_type") == "playlist":
            print("Playlist")
            playlist_title = data["title"]
            playlist = [playlist_title]
            data = data["entries"]

            for song in data:
                playlist.append([song["url"], song['title']])
            return playlist
        
        # if video is a single video or a livestream
        if data.get("duration") or data.get("live_status"):
            print("Single video")
            return [data["original_url"], data["title"]]
        
        

    @classmethod
    async def play_final(cls, url, *, loop=None, stream=True, verbose=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
                None, lambda: ytdl_info.extract_info(url, download=False)
            )
        # ℹ️ ydl.sanitize_info makes the info json-serializable
        data = ytdl_stream.sanitize_info(data)

        # If video is unavailable, returns None so next song can be played
        if(data is None):
            return None
        
        filename = data["url"] if stream else ytdl_format_options_get_stream.prepare_filename(data)
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