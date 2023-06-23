import os
import musicbot
import musicgame
import casino
import guessquotes
import discord
from discord import app_commands
from dotenv import load_dotenv

class aclient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.synced = False #we use this so the bot doesn't sync commands more than once

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync()
            self.synced = True
        print(f"Ready & logged in as {self.user}.")

load_dotenv()
BOT_TOKEN = "MTEwNTk4ODE2NDU0MTIyMjk2Mw.GTLvbw.DYj78LCIdyDWq1b-5NFeSAoUvzM3ZkQYFhpkBE"

intents = discord.Intents.all()
intents.message_content = True
client = aclient(intents = intents)
client.allowed_mentions = discord.AllowedMentions(roles=False, users=False, everyone=False)
tree = app_commands.CommandTree(client)

musicbot.run(tree, client)
musicgame.run(tree, client)
guessquotes.run(tree, client)
casino.run(tree, client)

client.run(BOT_TOKEN)