import discord
import youtube_dl
import asyncio
from requests import get

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

ffmpeg_options = {"options": "-vn"}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, verbose=False):
        loop = loop or asyncio.get_event_loop()
        
        # serches for video if not a link and chooses the first result, if it is a link it just passes it to youtube-dl to download

        # TODO: Implement choosing between multiple search results
        try:
            await get(url)
        except:
            data = await loop.run_in_executor(
                None, lambda: ytdl.extract_info(f"ytsearch:{url}", download=True)['entries'][0]
            )
        
        else:
            data = await loop.run_in_executor(
                None, lambda: ytdl.extract_info(url, download=True)
            )

        if "entries" in data:
            # Takes the first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
    

#class voicespeak(commands.FlagConverter, prefix='zz', delimiter=''):
#    make: str
