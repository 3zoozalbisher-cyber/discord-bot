import discord
from discord.ext import commands
import os
import time

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

# -------- VOICE TIME TRACKING --------
voice_join_times = {}

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
    if before.roles == after.roles:
        return

    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    before_roles = set(before.roles)
    after_roles = set(after.roles)

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

# -------- VOICE JOIN / LEAVE / SWITCH + TIME --------
@bot.event
async def on_voice_state_update(member, before, after):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    now = time.time()

    # Joined voice
    if before.channel is None and after.channel is not None:
        voice_join_times[member.id] = now
        await channel.send(
            f"🔊 joined voice channel\n"
            f"👤 {member.mention}\n"
            f"📢 {after.channel.name}"
        )

    # Left voice
    elif before.channel is not None and after.channel is None:
        joined_at = voice_join_times.pop(member.id, None)

        duration_text = "unknown"
        if joined_at:
            seconds = int(now - joined_at)
            mins, secs = divmod(seconds, 60)
            hours, mins = divmod(mins, 60)

            if hours > 0:
                duration_text = f"{hours}h {mins}m {secs}s"
            elif mins > 0:
                duration_text = f"{mins}m {secs}s"
            else:
                duration_text = f"{secs}s"

        await channel.send(
            f"🔇 left voice channel\n"
            f"👤 {member.mention}\n"
            f"📢 {before.channel.name}\n"
            f"⏱️ {duration_text}"
        )

    # Switched voice
    elif before.channel and after.channel and before.channel != after.channel:
        joined_at = voice_join_times.get(member.id)

        duration_text = "unknown"
        if joined_at:
            seconds = int(now - joined_at)
            mins, secs = divmod(seconds, 60)
            hours, mins = divmod(mins, 60)

            if hours > 0:
                duration_text = f"{hours}h {mins}m {secs}s"
            elif mins > 0:
                duration_text = f"{mins}m {secs}s"
            else:
                duration_text = f"{secs}s"

        voice_join_times[member.id] = now

        await channel.send(
            f"🔁 switched voice channel\n"
            f"👤 {member.mention}\n"
            f"📢 {before.channel.name} ➜ {after.channel.name}\n"
            f"⏱️ {duration_text}"
        )

# -------- RUN --------
bot.run(TOKEN)
