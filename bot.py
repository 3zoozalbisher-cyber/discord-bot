import discord
from discord.ext import commands
import os

# -------- CHANNEL IDS --------
WELCOME_CHANNEL_ID = 1414762426758463598
GOODBYE_CHANNEL_ID = 1460384380437659710
LOG_CHANNEL_ID     = 1460366893994086554

TOKEN = os.getenv("DISCORD_TOKEN")

# -------- INTENTS --------
intents = discord.Intents.default()
intents.members = True
intents.voice_states = True

# -------- BOT --------
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=None, intents=intents)

bot = MyBot()

# -------- READY --------
@bot.event
async def on_ready():
    print(f"🟢 Logged in as {bot.user}")

# -------- MEMBER JOIN (WELCOME CHANNEL) --------
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if not channel:
        return

    file = discord.File("images/welcome.png")
    await channel.send(
        f"👋 Welcome {member.mention} to **{member.guild.name}**!",
        file=file
    )

# -------- MEMBER LEAVE (GOODBYE CHANNEL) --------
@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(GOODBYE_CHANNEL_ID)
    if not channel:
        return

    file = discord.File("images/goodbye.png")
    await channel.send(
        f"👋 Goodbye **{member.name}**, we will miss you!",
        file=file
    )

# -------- ROLE ADD / REMOVE (FORMATTED, NO EXTRA LINE) --------
@bot.event
async def on_member_update(before, after):
    before_roles = set(before.roles)
    after_roles = set(after.roles)

    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    # Added roles
    for role in after_roles - before_roles:
        if role.is_default():
            continue
        await channel.send(
            f"✅ added role\n"
            f"👤 {after.mention}\n"
            f"🎭 {role.name}"
        )

    # Removed roles
    for role in before_roles - after_roles:
        if role.is_default():
            continue
        await channel.send(
            f"❌ removed role\n"
            f"👤 {after.mention}\n"
            f"🎭 {role.name}"
        )

# -------- VOICE JOIN / LEAVE (FORMATTED) --------
@bot.event
async def on_voice_state_update(member, before, after):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    if before.channel is None and after.channel is not None:
        await channel.send(
            f"🔊 joined voice channel\n"
            f"👤 {member.mention}"
        )

    elif before.channel is not None and after.channel is None:
        await channel.send(
            f"🔇 left voice channel\n"
            f"👤 {member.mention}"
        )

# -------- RUN --------
bot.run(TOKEN)
