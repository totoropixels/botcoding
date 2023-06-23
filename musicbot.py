
import discord
import os
from discord import app_commands
import ytportion
import asyncio
from typing import Optional

songQueue = []
song_files_delete = []

async def clearSongs():
    await asyncio.sleep(2)
    global song_files_delete

    if not song_files_delete:
        return

    for file in song_files_delete:
        try:
            os.remove(os.path.join(os.getcwd(), file))
        except OSError as e:
            print(e)
    
    song_files_delete.clear()

def run(tree, client):
    @tree.command(name = "ping", description= "Ping Pong")
    async def help(interaction):
        await interaction.response.send_message("Pong!")

    @tree.command(name = "join", description= "Join the user's voice channel")
    async def join(interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("Not in channel")
            return
        elif discord.utils.get(client.voice_clients) != None:
            await interaction.response.send_message("Already connected to VC")
            return
        else:
            channel = interaction.user.voice.channel
        await channel.connect()
        await interaction.response.send_message("Joined!!")

    @tree.command(name = "leave", description= "Leaves the voice channel")
    async def leave(interaction):
        if discord.utils.get(client.voice_clients) == None:
            await interaction.response.send_message("Not in voice channel")
            return

        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("Disconnected")
        return

    @tree.command(name = "playsong", description= "Play the song with the requested URL")
    async def playsong(interaction, url: str):
        global songQueue, song_files_delete
        voice_channel = interaction.guild.voice_client 
        channel = interaction.channel
        await interaction.response.defer()
        if discord.utils.get(client.voice_clients) == None:
            await interaction.followup.send("Bot is not in voice channel")
            return

        try:                             
            file = await ytportion.YTDLSource.from_url(url, loop = client.loop)
            if type(file) == list:
                for f in file:
                    songQueue.append([f[0], f[1], interaction.user.mention])
                    song_files_delete.append(f[0])
            
                await interaction.followup.send("Your songs have been added to the queue. The song will play shortly.\nThe requested playlist: {0}".format(url))
                if not voice_channel.is_playing():
                    await playmusic(channel, voice_channel) 
                return
            else:
                songQueue.append([file, url, interaction.user.mention])
                song_files_delete.append(file)
            if voice_channel.is_playing():
                await interaction.followup.send("There is already a song being played at the moment. Your song has been queued")
                return
            elif not voice_channel.is_playing() and len(songQueue) > 1:
                await interaction.followup.send("There is already a queue of songs. Your song has been added to the queue")
                await playmusic(channel, voice_channel)
                return

            await interaction.followup.send("Your song has been added to the queue. The song will play shortly")
            await playmusic(channel, voice_channel) 

            return
        except:
            await interaction.followup.send("The bot is not connected to a voice channel")

    @tree.command(name= "stopmusic", description= "Stop the music that is currently playing")
    async def stopmusic(interaction):  
        voice_client = discord.utils.get(client.voice_clients, guild= interaction.guild)

        if (voice_client.is_playing()):
            await interaction.response.send_message("The music has now been stopped D:")
            voice_client.stop()
        else:
            await interaction.response.send_message("The bot is not playing anything")

    @tree.command(name= "pausemusic", description= "Pause the music that is currently playing")
    async def pausemusic(interaction):
        voiceClient = interaction.guild.voice_client
        if (voiceClient.is_playing()):
            await interaction.response.send_message("The music has been paused. Type /resume to resume playing")
            voiceClient.pause()
        else:
            await interaction.response.send_message("The bot is not playing anything")

    @tree.command(name= "resumemusic", description= "Resume the music that has currently been paused")
    async def resumemusic(interaction):
        voiceClient = interaction.guild.voice_client
        if (voiceClient.is_paused()):
            await interaction.response.send_message("The music will now unpause.")       
            voiceClient.resume()
        else:
            await interaction.response.send_message("The bot is not playing anything")

    @tree.command(name= "skip", description= "Skips the current song that is playing")
    async def skip(interaction):
        voiceClient = interaction.guild.voice_client
        if voiceClient.is_playing():
            await interaction.response.send_message("The song has been skipped")  
            voiceClient.stop()
        else:
            await interaction.response.send_message("There is no song that is currently playing")

    @tree.command(name= "queuesong", description= "Add the song to the queue")
    async def queuesong(interaction, url: str):
        global songQueue, song_files_delete
        file = await ytportion.YTDLSource.from_url(url, loop = client.loop)
        interaction.response.defer()

        if type(file) == list:
            for f in file:
                songQueue.append([f[0], f[1], interaction.user.mention])
                song_files_delete.append(f[0])
        else:
            songQueue.append([file, url, interaction.user.mention])
            song_files_delete.append(file)

        await interaction.followup.send("Your song has been queued")

    async def playmusic(channel, voice_channel):
        global songQueue, song_files_delete     

        if not songQueue:
            await clearSongs()
            await channel.send(content= "The queue has finished. Use /playsong to play more music or use /queuesong to add more songs to the song queue")
            return      

        song = songQueue.pop(0)   

        voice_channel.play(discord.FFmpegPCMAudio(executable= "ffmpeg.exe", source= song[0]), after= lambda e: print(e) 
                           if e else asyncio.run_coroutine_threadsafe(playmusic(channel, voice_channel), client.loop))    
        await channel.send(content= "**Now Playing:** {0} | Requested by: {1}".format(song[1], song[2]))
        return
    
    @tree.command(name= "pinguser")
    async def pinguser(interaction, user: str, message: Optional[str] = ""):
        """
        Pings the given user x amount of times

        Parameters
        -----------
        user: str
            The user you want to ping
        
        message:
            The message you want to ping the user with
        """ 
        await channel.send(content= user + message, allowed_mentions= discord.AllowedMentions(roles=False, users=True, everyone=False))
        channel = interaction.channel

    @tree.command(name= "clearqueue", description= "Clears the queue of songs that is currently playing")
    async def clearqueue(interaction):
        global songQueue
        songQueue.clear()
        voice_channel = interaction.guild.voice_client
        if voice_channel.is_playing():
            voice_channel.stop()

        await interaction.response.send_message("The queue has been cleared.")
        
    return