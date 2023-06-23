import discord
import database as db
import random

playerInfo = {}
payouts = {
    "🍎" : 10,
    "🍉" : 50,
    "🍓" : 100,
    "🍇" : 500,
    "🍒" : 1000,
    "💎" : 15000,
}

def insertDB():
    database = db.database("botdatabase.db")

    return

def loadData():
    global playerInfo

    database = db.database("botdatabase.db")
    database.connect()

    records = database.readTable("slotinformation")
    for tup in records:
        playerInfo[tup[0]] = [tup[1], tup[2], tup[3]]

    db.sqliteconnection.close()
    print("Slot data Loaded Successfully")
    return

def probability(x):
    if x <= 40: # 40% 10x payout
        return "🍎"
    elif x <= 70: # 30% 50x payout
        return "🍉"
    elif x <= 85: # 15% 100x payout
        return "🍓"
    elif x <= 95: # 10% 500x payout
        return "🍇"
    elif x <= 99: # 4% 1000 payout
        return "🍒"
    elif x == 100: # 1% 15000x payout
        return "💎"

def updateDB(id):
    x = playerInfo[str(id)]

    database = db.database("botdatabase.db")
    database.connect()
    query = "UPDATE slotinformation SET userBalance = {0}, timesPlayed = {1}, timesWon = {3} WHERE userID = {2}".format(x[0], x[1], id, x[2])
    database.updateDB(query)

    db.sqliteconnection.close()

    return
    
def addInto(interaction):
    database = db.database("botdatabase.db")
    database.connect()

    query = "INSERT INTO slotinformation (userID, userBalance, timesPlayed, timesWon) VALUES (?,?,?,?)"
    database.insert(query, (interaction.user.id,1000,0,0))
    playerInfo[str(interaction.user.id)] = [1000,0,0]

    db.sqliteconnection.close()
    return

def run(tree, client):
    loadData()

    @tree.command(name= "slots", description= "Play slots and gamble your money away")
    async def slots(interaction):
        global playerInfo

        if str(interaction.user.id) not in playerInfo:
            addInto(interaction)

        lis = playerInfo[str(interaction.user.id)]

        # Print User Information
        embed = discord.Embed(title= "---- Slot Machine User Info ----", color= discord.Color.purple())
        embed.description = f"{interaction.user.mention}'s information"
        embed.add_field(name= "Balance", value= f"{lis[0]} tks")
        embed.add_field(name= "Times Played", value= lis[1]) 
        embed.add_field(name= "Times Won", value= f"{lis[2]}")

        await interaction.response.send_message(embed=embed)     

        """ def check(reaction, user):
            return user == interaction.user and str(reaction.emoji) == "✅"
        
        try:
            reaction, user = await client.wait_for('reaction_add', timeout= 60, check= check)
        except:
            await channel.send("No")
        else:
            await channel.send("Success") """

        return
    
    @tree.command(name= "slotspin", description= "Place a bet and spin the slot machine")
    async def slotspin(interaction, bet: int):
        global payouts, playerInfo
        """
        Parameters
        -----------
        bet: int
            The amount of tokens you want to bet
        """

        id = str(interaction.user.id)

        if playerInfo[id][0] < bet:
            await interaction.response.send_message("You do not have the required number of credits to bet that amount")
            return
        elif playerInfo[id][0] == 0:
            await interaction.response.send_message("Your balance is 0")

        if id not in playerInfo:
            addInto(interaction)
        x = [[probability(random.randint(1,100)) for x in range(4)] for x in range(5)]

        s = "**[--- Crazy Slots ---]**\n"

        for i, lis in enumerate(x):
            s += " {} {} {} {}".format(lis[0], lis[1], lis[2], lis[3])

            if i == 2:
                s += "**<--**"
            s += '\n'

        middleRow = set(x[2])
        if len(middleRow) == 1:
            bet *= payouts[list(middleRow)[0]]
            s += "You have won!!! Payout: {}".format(bet)
            playerInfo[interaction.user.id][2] += 1
        else:
            bet *= -1
            s += "You have lost :("
            
        playerInfo[id][0] += bet
        playerInfo[id][1] += 1

        updateDB(id)

        await interaction.response.send_message(s)

        return

    return