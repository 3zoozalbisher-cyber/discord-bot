import os
import discord

intents = discord.Intents.default()

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"LOGGED IN AS {client.user}")

client.run(os.getenv("DISCORD_TOKEN"))
