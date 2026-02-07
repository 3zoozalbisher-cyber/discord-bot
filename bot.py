import discord
from discord.ext import commands
import os
import time
import sqlite3

# ================= CONFIG =================
TOKEN = os.getenv("DISCORD_TOKEN")

WELCOME_CHANNEL_ID = 1414762426758463598
GOODBYE_CHANNEL_ID = 1460384380437659710
LOG_CHANNEL_ID = 1460366893994086554

APPLICATION_ID = 1460013127063175229
# =========================================

# ================= DATABASE =================
db = sqlite3.connect("bot.db", check_same_thread=False)
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
# ==========================================

# ================= INTENTS =================
intents = discord.Intents.default()
intents.members = True          # 🔴 REQUIRED
intents.message_content = True
intents.voice_states = True
# ==========================================

# ================= BOT =====================
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    application_id=APPLICATION_ID
)
# ==========================================

# ================= STATE ===================
voice_sessions = {}  # user_id -> start_time
# ==========================================

# ================= HELPERS =================
def ensure_user(user_id):
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user_id,)
    )
    db.commit()
# ==========================================

# ================= EVENTS ==================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

# --------- MEMBER JOIN ---------
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(
            f"🎉 Welcome {member.mention}!",
            file=discord.File("images/welcome.png")
        )

# -------- MEMBER LEAVE --------
@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(GOODBYE_CHANNEL_ID)
    if channel:
        await channel.send(
            f"👋 {member.name} left the server",
            file=discord.File("images/goodbye.png")
        )

# -------- ROLE ADD / REMOVE --------
@bot.event
async def on_member_update(before, after):
    log = bot.get_channel(LOG_CHANNEL_ID)
    if not log:
        return

    added = set(after.roles) - set(before.roles)
    removed = set(before.roles) - set(after.roles)

    for role in added:
        if not role.is_default():
            await log.send(
                f"✅ added role\n👤 {after.mention}\n🎭 {role.name}"
            )

    for role in removed:
        if not role.is_default():
            await log.send(
                f"❌ removed role\n👤 {after.mention}\n🎭 {role.name}"
            )

# -------- VOICE JOIN / LEAVE --------
@bot.event
async def on_voice_state_update(member, before, after):
    now = time.time()
    log = bot.get_channel(LOG_CHANNEL_ID)

    # JOIN
    if before.channel is None and after.channel is not None:
        if member.id in voice_sessions:
            return

        voice_sessions[member.id] = now
        ensure_user(member.id)

        if log:
            await log.send(
                f"🔊 joined voice channel\n"
                f"👤 {member.mention}\n"
                f"🎧 {after.channel.name}"
            )

    # LEAVE
    elif before.channel is not None and after.channel is None:
        start = voice_sessions.pop(member.id, None)
        if not start:
            return

        duration = int(now - start)

        cursor.execute(
            "UPDATE users SET voice_time = voice_time + ? WHERE user_id = ?",
            (duration, member.id)
        )
        db.commit()

        h = duration // 3600
        m = (duration % 3600) // 60
        s = duration % 60

        if log:
            await log.send(
                f"🔇 left voice channel\n"
                f"👤 {member.mention}\n"
                f"🎧 {before.channel.name}\n"
                f"⏱️ {h}h {m}m {s}s"
            )

# ================= SLASH COMMANDS =================
@bot.tree.command(name="ping", description="Check latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 Pong! `{round(bot.latency * 1000)}ms`"
    )

@bot.tree.command(name="profile", description="View your profile")
async def profile(interaction: discord.Interaction):
    ensure_user(interaction.user.id)

    cursor.execute(
        "SELECT xp, level, voice_time FROM users WHERE user_id = ?",
        (interaction.user.id,)
    )
    xp, level, voice = cursor.fetchone()

    h = voice // 3600
    m = (voice % 3600) // 60
    s = voice % 60

    await interaction.response.send_message(
        f"👤 {interaction.user.mention}\n"
        f"⭐ Level: {level}\n"
        f"📊 XP: {xp}/{level*100}\n"
        f"🎙️ Voice: {h}h {m}m {s}s"
    )

# ================= RUN =====================
bot.run(TOKEN)
