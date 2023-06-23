import re
import random
from discord import app_commands

quotes = []
answer = []
guessCount = 0
inProgress = True

def readFile(regexuse):
    global quotes

    with open("quotes.csv", 'r') as f:
        quotes = f.readlines()    

    for i, line in enumerate(quotes):
        quotes[i] = re.findall(regexuse, line)

    return

def run(tree, client):
    regexuse = "^(.*?),\"\"\"(.*?)\"\"\",\"\"\"(.*?)\"\"\"$"
    readFile(regexuse)

    @tree.command(name= "givequote", description= "Gives you a quote")
    @app_commands.choices(gametype= [app_commands.Choice(name= "Pick", value= "pick"), app_commands.Choice(name= 'Random', value= "random"), app_commands.Choice(name= "Ban", value= "ban")])
    async def givequote(interaction, gametype: app_commands.Choice[str]):
        global quotes, answer, inProgress
        x = random.randint(0, len(quotes) - 1)
        answer = quotes[x][0]

        if gametype.value == "pick":
            await interaction.response.send_message("The following quote is a pick quote\n\"{0}\"".format(answer[1]))
        elif gametype.value == "ban":
            await interaction.response.send_message("The following quote is a ban quote\n\"{0}\"".format(answer[2]))
        elif gametype.value == "random":
            type = random.randint(1,2)
            await interaction.response.send_message("The following quote is a {0} quote\n\"{1}\"".format("Pick" if type == 1 else "Ban", answer[type]))

        inProgress = True

    @tree.command(name= "guesschampion", description= "Guess the champion that says the given quote")
    async def guesschampion(interaction, champion: str):
        global answer, guessCount, inProgress
        if not inProgress:
            await interaction.response.send_message("There is no guess game currently going on")
            return

        guessCount += 1
        if champion == answer[0]:
            await interaction.response.send_message("{0} was correct! It took {1} guesses".format(champion, guessCount))
            guessCount = 0
            inProgress = False
        else:
            await interaction.response.send_message("{0} was not correct.".format(champion))

        return
    
    @tree.command(name= "giveup", description= "Give up and reveals the answer")
    async def giveup(interaction):
        global inProgress, answer, guessCount
        
        if not inProgress:
            await interaction.response.send_message("There is no guess game currently going on")
            return

        await interaction.response.send_message("The answer was: {0}".format(answer[0]))
        inProgress = False
        guessCount = 0

        return
    return