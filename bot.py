import discord
from discord.ext import commands, tasks
from discord import app_commands
import sqlite3
import os
import time

# ---------- CONFIG ----------
TOKEN = os.getenv("DISCORD_TOKEN")
XP_PER_MESSAGE = 5
XP_PER_MINUTE_VOICE = 10

LOG_CHANNEL_ID = 1460366893994086554  # <-- change
WELCOME_CHANNEL_ID = 1414762426758463598
GOODBYE_CHANNEL_ID = 1460384380437659710
# ----------------------------

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True
# ----------------------------

# ---------- DATABASE ----------
db = sqlite3.connect("bot.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    voice_time INTEGER DEFAULT 0
)
""")
db.commit()
# ----------------------------

voice_sessions = {}

def get_user(user_id):
    cursor.execute("SELECT xp, level, voice_time FROM users WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    if not data:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        db.commit()
        return (0, 1, 0)
    return data

def add_xp(user_id, amount):
    xp, level, voice = get_user(user_id)
    xp += amount
    needed = level * 100
    leveled = False

    if xp >= needed:
        xp -= needed
        level += 1
        leveled = True

    cursor.execute("UPDATE users SET xp=?, level=? WHERE user_id=?", (xp, level, user_id))
    db.commit()
    return leveled, level

# ---------- BOT ----------
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

# ---------- EVENTS ----------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    leveled, level = add_xp(message.author.id, XP_PER_MESSAGE)
    if leveled:
        await message.channel.send(
            f"⭐ **LEVEL UP!**\n👤 {message.author.mention}\n🎯 Level {level}"
        )

    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(f"🎉 **Welcome {member.mention}!**")

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(GOODBYE_CHANNEL_ID)
    if channel:
        await channel.send(f"👋 **{member.name} left the server**")

@bot.event
async def on_voice_state_update(member, before, after):
    log = bot.get_channel(LOG_CHANNEL_ID)

    if before.channel is None and after.channel:
        voice_sessions[member.id] = time.time()
        if log:
            await log.send(
                f"🔊 **Joined voice channel**\n👤 {member.mention}\n🎧 {after.channel.name}"
            )

    elif before.channel and after.channel is None:
        start = voice_sessions.pop(member.id, None)
        if start:
            duration = int(time.time() - start)
            minutes = duration // 60
            xp_gain = minutes * XP_PER_MINUTE_VOICE

            xp, level, voice = get_user(member.id)
            voice += duration
            cursor.execute(
                "UPDATE users SET voice_time=? WHERE user_id=?",
                (voice, member.id)
            )
            db.commit()

            add_xp(member.id, xp_gain)

            if log:
                await log.send(
                    f"🔇 **Left voice channel**\n👤 {member.mention}\n⏱️ {minutes} minutes"
                )

# ---------- SLASH COMMANDS ----------
@bot.tree.command(name="ping", description="Bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 Pong! `{round(bot.latency * 1000)}ms`"
    )

@bot.tree.command(name="rank", description="Show your level")
async def rank(interaction: discord.Interaction):
    xp, level, voice = get_user(interaction.user.id)
    await interaction.response.send_message(
        f"⭐ **Your Rank**\n"
        f"🎯 Level: {level}\n"
        f"📊 XP: {xp}/{level*100}"
    )

@bot.tree.command(name="voiceleaderboard", description="Top voice users")
async def voiceleaderboard(interaction: discord.Interaction):
    cursor.execute(
        "SELECT user_id, voice_time FROM users ORDER BY voice_time DESC LIMIT 5"
    )
    rows = cursor.fetchall()

    msg = "🎙️ **Voice Leaderboard**\n"
    for i, (uid, t) in enumerate(rows, start=1):
        user = bot.get_user(uid)
        msg += f"**{i}.** {user} — {t//3600}h {(t%3600)//60}m\n"

    await interaction.response.send_message(msg)

# ---------- MODERATION ----------
@bot.tree.command(name="clear", description="Clear messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(
        f"🧹 Cleared {amount} messages", ephemeral=True
    )

@bot.tree.command(name="kick", description="Kick a member")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    await member.kick(reason=reason)
    await interaction.response.send_message(
        f"👢 {member} was kicked"
    )

@bot.tree.command(name="mute", description="Timeout a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int):
    await member.timeout(discord.utils.utcnow() + discord.timedelta(minutes=minutes))
    await interaction.response.send_message(
        f"🔇 {member} muted for {minutes} minutes"
    )

# ---------- RUN ----------
bot.run(TOKEN)
