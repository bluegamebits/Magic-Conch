from ytmusicapi import YTMusic
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
ytmusic = YTMusic("oauth.json")


def search_ytmusic(search_term):
    search_results = ytmusic.search(search_term, filter = "songs")
    id = search_results[0]["videoId"]
    title = search_results[0]["title"]
    artists = search_results[0]["artists"]
    artists = ", ".join([artist['name'] for artist in artists]) # <- most understandable option I came up with /s
    return [f"https://music.youtube.com/watch?v={id}", title + f" - {artists}"]

def get_recommended(url):
    video_id = url.split('?v=')[1]
    print(f"Video ID: {video_id}")
    watch_playlist = ytmusic.get_watch_playlist(video_id)

    recommended_songs = ["Youtube Music Autoplay"]
    for song in watch_playlist["tracks"]:
        video_url = f"https://music.youtube.com/watch?v={song['videoId']}"
        title = song['title']
        artists = ", ".join([artist['name'] for artist in song["artists"]])
        title += f" - {artists}"
        recommended_songs.append([video_url, title])
    print (f"recommended songs: {recommended_songs}")
    return recommended_songs[:1] + recommended_songs[2:]


def add_to_play_history(url):
    ytmusic = YTMusic("browser.json")
    video_id = url.split('?v=')[1]
    print(f"Video ID{video_id}")
    song = ytmusic.get_song(video_id)
    result = ytmusic.add_history_item(song)
    return result

async def async_wrapper(func, *args):
    loop = asyncio.get_event_loop()
    
    # Use a ThreadPoolExecutor to run the synchronous function in a separate thread
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, func, *args)
    
    return result

async def search_ytmusic_async(search_term):
    
    task = asyncio.create_task(async_wrapper(search_ytmusic, search_term))

    # Wait for the async_wrapper to complete
    result = await task
    return result   

async def get_recommended_async(url):
    
    task = asyncio.create_task(async_wrapper(get_recommended, url))

    # Wait for the async_wrapper to complete
    result = await task
    return result   

async def add_to_play_history_async(url):
    
    task = asyncio.create_task(async_wrapper(add_to_play_history, url))

    # Wait for the async_wrapper to complete
    result = await task
    return result       

