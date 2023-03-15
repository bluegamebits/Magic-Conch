# Magic-Conch
Magic conch discord bot

Working discord multi-functional bot with discord.py

Has music bot functionality that takes direct links from youtube (or anything supported by youtube-dl) and plays it on a voice channel

Initial features:
- Join whatever voice channel the user is on and can switch channels if already on a channel
- Downloads youtube sound using youtube-dl and plays the music on a voice channel
- Pause, unpause and stop functionality implemented
- Volume can be changed

Implemented initial voice functionality with googlevoice api
- Users custom-built api wrapper for googlevoice
- Return what is said as a .mp3 file that is then played on the voice chat

Not yet implemented / restrictions:

Voice bot:
- Does not allow for any change in configuration or language
- No logic implemented for voice bot, only repeats what is said on chat( Thinking of implementing chatgpt)

Music bot:
- Does not allow for any queing of songs, only one song can be played at a time
- Looping music not implemented
- Only way to play music is by entering full link, searching is not yet implemented
- Autoplay songs based on history not implemented
- Only one music bot can be activated on one voice channel, does not support playing music on multiple voice channels

General:
- / commands are not implemented yet
- No common structure decided yet for bot commands in general
- You can't ask the magic conch anything yet ( will be added soon )
