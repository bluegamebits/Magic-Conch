import discord
from yt_dlp import YoutubeDL
import aiohttp
import asyncio

ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # Bind to ipv4 since ipv6 addresses cause issues at certain times
    'geo_bypass': True,# add geo-bypass option,

}

# Before_options specified for avoiding disconnections when straming
ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                  "options": "-vn"}

ytdl = YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get("title")
        self.url = data.get("url")

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
                    None, lambda: ytdl.extract_info(f"ytsearch:{url}", download=False)['entries'][0]
                )
                video_url = f"https://www.youtube.com/watch?v={data['id']}"
        
            else:
                data = await loop.run_in_executor(
                    None, lambda: ytdl.extract_info(url, download=False)
                )
                video_url = f"https://www.youtube.com/watch?v={data['id']}"

        if "entries" in data:
            # Takes the first item from a playlist
            data = data["entries"][0]
        

        
        video_url = f"https://www.youtube.com/watch?v={data['id']}"

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data), video_url