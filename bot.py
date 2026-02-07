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
voice_sessions = {}  # user_id -> (channel_id, start_time)
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

# -------- VOICE STATE (FINAL FIX) --------
@bot.event
async def on_voice_state_update(member, before, after):
    log = bot.get_channel(LOG_CHANNEL_ID)
    now = time.time()

    before_channel = before.channel
    after_channel = after.channel

    # ===== JOIN =====
    if before_channel is None and after_channel is not None:
        # prevent duplicate join for same channel
        if member.id in voice_sessions:
            return

        voice_sessions[member.id] = (after_channel.id, now)
        ensure_user(member.id)

        if log:
            await log.send(
                f"🔊 joined voice channel\n"
                f"👤 {member.mention}\n"
                f"🎧 {after_channel.name}"
            )

    # ===== LEAVE =====
    elif before_channel is not None and after_channel is None:
        session = voice_sessions.pop(member.id, None)
        if not session:
            return

        _, start = session
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
                f"🎧 {before_channel.name}\n"
                f"⏱️ {h}h {m}m {s}s"
            )

    # ===== MOVE CHANNEL (OPTIONAL – IGNORED) =====
    # If you ever want to log moves, we can add it cleanly.
    else:
        return  # ignore mute/deafen/state updates

# ================= RUN =====================
bot.run(TOKEN)
