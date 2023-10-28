import discord
from discord.app_commands import CommandTree
import random
import together
import time

together.api_key = "93620393f8368d94029be74aae01279d90adeb5ce407803ecaf974354af59263"

allowed_mentions = discord.AllowedMentions(everyone=False, users=True, roles=True, replied_user=False)
intents = discord.Intents.all()
intents.presences = False
intents.members = False

async def setup_hook():
    pass

client = discord.AutoShardedClient(intents=intents, allowed_mentions=allowed_mentions, chunk_guilds_at_startup=False)
# client.activity = discord.Activity(
#         name='Activity', 
#         type=discord.ActivityType.watching,)

client.setup_hook = setup_hook
client.tree = CommandTree(client)

@client.event
async def on_ready():
    print("Bot started")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.author.id == 396545298069061642 and message.content.lower() == "!reloadcmd":
        await client.tree.sync(guild=None)
        await message.reply("Reloaded global")

    return

@client.tree.command(name="task", description="Get your task of the day.", nsfw=False, auto_locale_strings=True)
async def get_task(interaction: discord.Interaction):
    return

bot_token = "MTE2Nzk1ODU2NDcxNTg5Mjc3Ng.G22gb8.mjfqauMwZxZl3FqyhsvqpubxSWA0OqaFYxfVUE"
if __name__ == "__main__":
    client.run(bot_token)