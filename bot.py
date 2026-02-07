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
# ==========================================

# ================= INTENTS =================
intents = discord.Intents.default()
intents.members = True
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

# ============ VOICE TRACKING ===============
voice_sessions = {}          # user_id -> start_time
voice_event_cooldown = {}    # user_id -> last_event_time
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

# --------- MEMBER JOIN (WITH IMAGE) --------
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(
            f"🎉 Welcome {member.mention}!",
            file=discord.File("images/welcome.png")
        )

# -------- MEMBER LEAVE (WITH IMAGE) --------
@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(GOODBYE_CHANNEL_ID)
    if channel:
        await channel.send(
            f"👋 {member.name} left the server",
            file=discord.File("images/goodbye.png")
        )

# -------- ROLE ADD / REMOVE ----------------
@bot.event
async def on_member_update(before, after):
    log = bot.get_channel(LOG_CHANNEL_ID)
    if not log:
        return

    for role in set(after.roles) - set(before.roles):
        if not role.is_default():
            await log.send(
                f"✅ added role\n"
                f"👤 {after.mention}\n"
                f"🎭 {role.name}"
            )

    for role in set(before.roles) - set(after.roles):
        if not role.is_default():
            await log.send(
                f"❌ removed role\n"
                f"👤 {after.mention}\n"
                f"🎭 {role.name}"
            )

# -------- VOICE JOIN / LEAVE (NO DUPES) ----
@bot.event
async def on_voice_state_update(member, before, after):
    now = time.time()
    log = bot.get_channel(LOG_CHANNEL_ID)

    # ---- DUPLICATE PROTECTION ----
    last = voice_event_cooldown.get(member.id, 0)
    if now - last < 2:
        return
    voice_event_cooldown[member.id] = now
    # -----------------------------

    # ===== JOIN =====
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

    # ===== LEAVE =====
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

# -------- XP + LEVEL SYSTEM ----------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    ensure_user(message.author.id)

    cursor.execute(
        "SELECT xp, level FROM users WHERE user_id = ?",
        (message.author.id,)
    )
    xp, level = cursor.fetchone()

    xp += 10
    needed = level * 100

    if xp >= needed:
        xp = 0
        level += 1

        log = bot.get_channel(LOG_CHANNEL_ID)
        if log:
            await log.send(
                f"⭐ LEVEL UP!\n"
                f"👤 {message.author.mention}\n"
                f"🏆 Level {level}"
            )

    cursor.execute(
        "UPDATE users SET xp = ?, level = ? WHERE user_id = ?",
        (xp, level, message.author.id)
    )
    db.commit()

    await bot.process_commands(message)

# ================= SLASH COMMANDS =================
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

@bot.tree.command(name="voicetop", description="Top voice users")
async def voicetop(interaction: discord.Interaction):
    cursor.execute(
        "SELECT user_id, voice_time FROM users ORDER BY voice_time DESC LIMIT 10"
    )
    rows = cursor.fetchall()

    text = "🏆 **Voice Time Leaderboard**\n"
    for i, (uid, seconds) in enumerate(rows, 1):
        member = interaction.guild.get_member(uid)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        text += f"{i}. {member.name if member else 'User'} — {h}h {m}m\n"

    await interaction.response.send_message(text)

@bot.tree.command(name="ping", description="Check latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 Pong! `{round(bot.latency * 1000)}ms`"
    )

# ================= RUN =====================
bot.run(TOKEN)
