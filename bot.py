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

# -------- MEMBER JOIN --------
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

# -------- MEMBER LEAVE --------
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

# -------- ROLE ADD / REMOVE --------
@bot.event
async def on_member_update(before, after):
    before_roles = set(before.roles)
    after_roles = set(after.roles)

    for role in after_roles - before_roles:
        if role.is_default():
            continue
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(
                f"🎉 {after.mention} was given role **{role.name}**"
            )

    for role in before_roles - after_roles:
        if role.is_default():
            continue
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(
                f"❌ {after.mention} lost role **{role.name}**"
            )

# -------- VOICE JOIN / LEAVE --------
@bot.event
async def on_voice_state_update(member, before, after):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    if before.channel is None and after.channel is not None:
        await channel.send(
            f"🔊 {member.mention} joined voice channel **{after.channel.name}**"
        )

    elif before.channel is not None and after.channel is None:
        await channel.send(
            f"🔇 {member.mention} left voice channel **{before.channel.name}**"
        )

# -------- RUN --------
bot.run(TOKEN)
