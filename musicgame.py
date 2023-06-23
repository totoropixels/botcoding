import os
import discord
from discord import app_commands
import random
import ytportion
from typing import Optional
import asyncio
import database

# Globals

# bools
musicGame = False # Used to determine if there is a music game currently running
type2 = False # Used to determine the music game type
ableSkip = False # Used to determine if the song can be skipped(if all players have guessed and type2 is true)

# ints
songCount = 0 # The number of songs submitted by players
nPlayers = 0 # Number of players in the music game
nSongs = 0 # Number of songs in the music game
currentSong = 0 # The current song the music game is playing/at

# dictionaries 
mention_nick = {} # Key: userMention, Value: user's nickname(as displayed in server)
submissionCount = {} # Key: userMention, Value: Number of songs submitted
userIDs = {} # Key: userMention, Value: userID. Used for the /leaderboard command
scores = {} # Key: userMention, Value: Score of each player(int value)
guessRecords = {} #Key: userMention, Value: userMention of the player they gussed that round

# lists
msgs_to_edit = [] # List of messages sent by the bot to edit (Editing song links in for each round)
songList = [] # The list of songs submitted from all the players
song_files_delete = [] # The files of the songs downloaded by YTDLP to delete (to save memory space)

# sets
whoGuessed = set() # Set of players who guessed that round
whoSkipped = set() # Set of players who voted to skip the song (If the game is of type2)

# guild
guild = ""

def clearData():
    global musicGame, songCount, nPlayers, nSongs, songList, mention_nick, submissionCount, scores, currentSong, msgs_to_edit, whoGuessed, guessRecords, userIDs

    # Clear data containers
    songList.clear()
    whoGuessed.clear()
    mention_nick.clear()
    submissionCount.clear()
    scores.clear()
    msgs_to_edit.clear()
    guessRecords.clear()
    userIDs.clear()

    # Reset values to 0
    nSongs = 0
    nPlayers = 0
    songCount = 0
    currentSong = 0

def insertDB():
    global scores, nSongs, userIDs, nPlayers
    dataDB = database.database("botdatabase.db")

    dataDB.connect()
    for player, score in scores.items():
        if dataDB.search(userIDs[player], "playerscores", "userID") == []:
            query = "INSERT INTO playerscores (userID, score, roundsPlayed) VALUES (?,?,?)"
            dataDB.insert(query, (userIDs[player], score, (nSongs * nPlayers) - nSongs))
        else:
            lis = dataDB.search(userIDs[player], "playerscores", "userID")
            query = "UPDATE playerscores SET score = {0}, roundsPlayed = {1} WHERE userID = {2}".format(lis[0][1] + score, lis[0][2] + ((nSongs * nPlayers) - nSongs), lis[0][0])
            dataDB.updateDB(query)   
    
    database.sqliteconnection.close()
    return

def clearSongs():
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
    @tree.command(name= "createmusicgame")
    @app_commands.choices(type= [app_commands.Choice(name= "Full", value= "full"), app_commands.Choice(name= 'Partial', value= "partial")])
    async def createmusicgame(interaction, players: int, songs: int, type: app_commands.Choice[str]):
        """
        Creates a music game with the given players and songs

        Parameters
        -----------
        players: int
            The number of players in the game
        
        songs: int
            The number of songs per player to submit
        
        choices: app_commands.Choice
            Decide whether the songs should end early after all guesses or play song fully
            Full = Songs don't end early. Partial = Songs will end early after all guesses are submitted
        """

        global musicGame, nPlayers, nSongs, songCount, currentSong, type2, guild
        clearData()

        if musicGame:
            await interaction.reponse.send_message("There is already a music game going on")
            return
        
        if type.value == "partial":
            type2 = False
        else:
            type2 = True
        
        nPlayers = players
        nSongs = songs
        s = "Player Count: {0} | Songs per player: {1} | Songs are played from start to finish: {2}\nThe game is now ready to accept submissions. Submit songs using /submit".format(players, songs, "Yes" if type2 else "No")

        await interaction.response.send_message(s)
        musicGame = True
        guild = interaction.guild
        return
    
    async def endgame(channel):
        """
        Ends the current music game once all rounds/songs have been played
        """   
        global songCount, nSongs, nPlayers, msgs_to_edit, musicGame, guild
        
        s = "Round Recap:\n"

        for index, entry in enumerate(songList):
            s += "Round {0}: {1} - {2}\n".format(index + 1, entry[0], entry[2])

        s += "```Score Totals: \n"
        for key, val in scores.items():
            s += "{0} - {1}\n".format(mention_nick[key], val)

        s += "```\nThanks for playing!\n"
        s += "Use /guesshistory to see each individual's guesses each round. Can print both specific round or all at once"

        musicGame = False
        await channel.send(s)
        if discord.utils.get(client.voice_clients) != None:
            await guild.voice_client.disconnect()
        
        for index, e in enumerate(msgs_to_edit):
            await e.edit(content= e.content + "\n{}".format(songList[index][2]))

        insertDB()
        clearSongs()
    
    @tree.command(name= "endearly", description= "Cancel the game early if need be")
    async def endearly(interaction):
        clearData()
        clearSongs()
        global musicGame
        musicGame = False
        await interaction.response.send_message("The game has been cancelled")

    @tree.command(name= "guess")
    async def guess(interaction, individual: str):
        """
        Submits the given YT url to be played in the music game

        Parameters
        -----------
        individual: str
            Ping the individual you wish to guess
        """    
        global nSongs, nPlayers, currentSong, guessRecords, msgs_to_edit, song_files_delete, type2, ableSkip

        userID = interaction.user.mention
        s = ""

        if not musicGame:
            await interaction.response.send_message("There is no music game that is currently on")
            return
        elif userID == individual:
            await interaction.response.send_message("You cannot guess yourself\n")
            return
        elif songCount != (nSongs * nPlayers):
            await interaction.response.send_message("The game hasn't started yet. Submit songs using /submit")
            return
        
        if userID not in whoGuessed:
            if individual == songList[currentSong][0]:
                scores[userID] += 1

            if userID in guessRecords:
                guessRecords[userID].append(individual)
            else:
                guessRecords[userID] = [individual]

            whoGuessed.add(userID)
            s = "{} has submitted their guess.".format(userID)
        else:
            s = "You already gussed. Stop trying to farm nerd"

        await interaction.response.send_message(s)

        if len(whoGuessed) == nPlayers:
            ableSkip = True
            voice_client = discord.utils.get(client.voice_clients, guild= interaction.guild)
            channel = interaction.channel
            await channel.send(content= "\nAll players have gussed a player.\n\n")
            if voice_client.is_playing() and not type2:
                await channel.send(content= "The next round will start shortly")
                voice_client.stop()
            else:
                await channel.send(content= "The next round will start after the song ends. Use /voteskip to end the song early")   
        return
    
    async def aftersong(voice_channel, channel):
        global currentSong, whoGuessed, nSongs, nPlayers, ableSkip

        currentSong += 1
        whoGuessed.clear()
        ableSkip = False

        await asyncio.sleep(0.2)

        if currentSong < nSongs * nPlayers:
            s += "\n------------------------ Song {} ------------------------\n".format(currentSong + 1)
            msg = await channel.send(content= s)
            msgs_to_edit.append(msg)
    
        if currentSong < nSongs * nPlayers:

            file = await ytportion.YTDLSource.from_url(songList[currentSong][2], loop = client.loop)
            voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source = file),
                    after= lambda e: print(e) if e else asyncio.run_coroutine_threadsafe(aftersong(voice_channel, channel), client.loop))

            song_files_delete.append(file)

        if currentSong == (nSongs * nPlayers):
            s = "All Songs have been played. The results will be printed shortly\n\n"
            await channel.send(content= s)
            await endgame(channel)

        return

    @tree.command(name= "voteskip", description= "Vote to skip the song that is currently playing")
    async def voteskip(interaction):    
        global type2, musicGame, nPlayers, ableSkip, whoSkipped
        channel = interaction.channel
        if not musicGame:
            await interaction.response.send_message("There is no music game currently going on")
            return
        elif not type2:
            await interaction.response.send_message("The game is not of Type 2 (Songs are played to the end after all guesses are submitted)")
            return
        elif not ableSkip:
            await interaction.response.send_message("The song is not able to be skipped at the moment. Not all players have submitted their guess")
            return
        
        mention = interaction.user.mention
        if mention not in whoSkipped:
            whoSkipped.add(mention)
            await interaction.response.send_message("{0} has voted to skip ({1}/{2})".format(mention, len(whoSkipped), nPlayers))

        if len(whoSkipped) == nPlayers:
            s = "All players have voted to skip the current song. The song will skip shortly"
            await channel.send(content= s)
            vc = interaction.guild.voice_client
            vc.stop()

        return               
    
    @tree.command(name= "guesshistory")
    @app_commands.choices(choices = [app_commands.Choice(name= "All", value= "all"), app_commands.Choice(name= "Round", value= "round"), app_commands.Choice(name= "Everyone", value= "everyone")])
    async def guesshistory(interaction, individual: Optional[str], choices: app_commands.Choice[str], round_index: Optional[int]):
        """
        Used to see the guess history of the specified individual

        Parameters
        -----------
        individual: str
            Individual that you want to see the guess history of
        
        choices: app_commands.Choice[str]
            Choose to either see all guesses or specific round guess
        
        roundIndex: int
            Round to see the individual's guess at
        """  
        
        if musicGame:
            await interaction.response.send_message("Stop trying to cheat. The game isn't finished yet")
            return
        
        global guessRecords
        if choices.value == "all":
            s = "{}'s Guesses:\n".format(individual)
            for index, val in enumerate(guessRecords[individual]):
                s += "Round {0} - {1} | Answer: {2}\n".format(index + 1, val, songList[index][0])

            await interaction.response.send_message(s)
        elif choices.value == "everyone":
            s = ""
            for key, value in guessRecords.items():
                s += "{}'s Guesses:\n".format(key)
                for index, val in enumerate(value):
                     s += "Round {0} - {1} | Answer: {2}\n".format(index + 1, val, songList[index][0])
                s += "\n"

            await interaction.response.send_message(s)
        else:
            await interaction.response.send_message("Round {0} - {1} | Answer: {2}\n".format(round_index, guessRecords[individual][round_index-1], songList[round_index - 1][0]))
        
    @tree.command(name= "submitsong")
    async def submitsong(interaction, songlink: str):
        """
        Submits the given YT url to be played in the music game

        Parameters
        -----------
        songlink: str
            YT Link to the song you want to submit
        """    
        global submissionCount, songCount, nSongs, nPlayers, songList, currentSong, msgs_to_edit, musicGame, song_files_delete

        userID = interaction.user.mention
        userNick = interaction.user.display_name

        if songCount == (nSongs * nPlayers):
            await interaction.response.send_message("The game is currently playing. Join in the next game")
            return

        if userID in submissionCount:
            if submissionCount[userID] == nSongs:
                await interaction.response.send_message("{0} has already submitted {} songs".format(userID, nSongs))
            else:
                submissionCount[userID] += 1
        else:
            submissionCount[userID] = 1

        songCount += 1
        if userID not in mention_nick:
            mention_nick[userID] = userNick
            scores[userID] = 0
            userIDs[userID] = interaction.user.id

        s = "{} has submitted a song".format(userID)
        songList.append((userID, userNick, songlink,))
        await interaction.response.send_message(s)

        if songCount == (nSongs * nPlayers):
            await asyncio.sleep(0.5)
            ss = "\nAll songs have been submitted. The game is now ready to start\n" + "\n------------------------ Song {} ------------------------\n".format(currentSong + 1)
            msg = await client.get_channel(interaction.channel_id).send(content= ss)

            msgs_to_edit.append(msg)

            #Shuffle Song List and start to play game
            random.shuffle(songList)
            
            # Connect bot to channel
            if not interaction.user.voice:
                await client.get_channel(interaction.channel_id).send(content= "Not in channel")
                clearData()
                musicGame = False
                return
            elif discord.utils.get(client.voice_clients, guild= interaction.guild) != None:
                pass
            else:
                channel = interaction.user.voice.channel
                await channel.connect()

            # Now play first song
            server = interaction.guild
            voice_channel = server.voice_client

            file = await ytportion.YTDLSource.from_url(songList[currentSong][2], loop = client.loop)
            voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source = file),
                    after = lambda e: print(e) if e else asyncio.run_coroutine_threadsafe(aftersong(voice_channel, interaction.channel), client.loop))  

            song_files_delete.append(file)

        return
    
    @tree.command(name= "leaderboard", description= "Sends an embed containing the music game leaderboard")
    async def leaderboard(interaction):
        dataDB = database.database("musicscores.db")
        dataDB.connect()
        x = dataDB.readTable("playerscores")
        x.sort(key= lambda a: a[1], reverse= True)

        if x == []:
            database.sqliteconnection.close()
            await interaction.response.send_message("There are no records of anyone playing")
            return
        embed = discord.Embed(title= "Music Game All Time Leaderboard")
        s = ""
        for index, tup in enumerate(x):
            s += "{3}. {0} - Score: {1} | Songs Guessed: {2}\n".format("<@{}>".format(tup[0]), tup[1], tup[2], index + 1)

        embed.description = s
        database.sqliteconnection.close()
        await interaction.response.send_message(embed= embed)
    
    @tree.command(name= "test", description= "test")
    async def test(interaction):
        channel = client.get_channel(interaction.channel_id)
        await interaction.response.send_message("Testing Send/Asyncio")

        await asyncio.sleep(1)
        msg = await channel.send(content="Test Message")
        print(msg.id)
    return
