import discord
from discord.ext import commands
import os

WELCOME_CHANNEL_ID = 1414762426758463598
GOODBYE_CHANNEL_ID = 1460384380437659710
LOG_CHANNEL_ID     = 1460366893994086554

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=None, intents=intents)

bot = MyBot()

@bot.event
async def on_ready():
    print(f"🟢 Logged in as {bot.user}")

# ---- WELCOME ----
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(f"👋 Welcome {member.mention}!")

# ---- GOODBYE ----
@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(GOODBYE_CHANNEL_ID)
    if channel:
        await channel.send(f"👋 Goodbye **{member.name}**!")

# ---- ROLE LOG (NO DUPLICATES) ----
@bot.event
async def on_member_update(before, after):
    if before.roles == after.roles:
        return

    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    before_roles = set(before.roles)
    after_roles = set(after.roles)

    added = after_roles - before_roles
    removed = before_roles - after_roles

    for role in added:
        if not role.is_default():
            await channel.send(
                f"✅ added role\n"
                f"👤 {after.mention}\n"
                f"🎭 {role.name}"
            )

    for role in removed:
        if not role.is_default():
            await channel.send(
                f"❌ removed role\n"
                f"👤 {after.mention}\n"
                f"🎭 {role.name}"
            )

# ---- VOICE LOG ----
@bot.event
async def on_voice_state_update(member, before, after):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    if before.channel is None and after.channel:
        await channel.send(f"🔊 joined voice channel\n👤 {member.mention}")

    elif before.channel and after.channel is None:
        await channel.send(f"🔇 left voice channel\n👤 {member.mention}")

bot.run(TOKEN)
