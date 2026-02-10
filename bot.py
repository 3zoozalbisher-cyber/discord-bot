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

# ============ VOICE STATE ==================
voice_state = {}  
# user_id -> {"in_voice": bool, "channel_id": int, "start": float}
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
    ch = bot.get_channel(WELCOME_CHANNEL_ID)
    if ch:
        await ch.send(
            f"🎉 Welcome {member.mention}!",
            file=discord.File("images/welcome.png")
        )

# -------- MEMBER LEAVE --------
@bot.event
async def on_member_remove(member):
    ch = bot.get_channel(GOODBYE_CHANNEL_ID)
    if ch:
        await ch.send(
            f"👋 {member.name} left the server",
            file=discord.File("images/goodbye.png")
        )

# -------- ROLE ADD / REMOVE --------
@bot.event
async def on_member_update(before, after):
    log = bot.get_channel(LOG_CHANNEL_ID)
    if not log:
        return

    for role in set(after.roles) - set(before.roles):
        if not role.is_default():
            await log.send(f"✅ added role\n👤 {after.mention}\n🎭 {role.name}")

    for role in set(before.roles) - set(after.roles):
        if not role.is_default():
            await log.send(f"❌ removed role\n👤 {after.mention}\n🎭 {role.name}")

# -------- VOICE (DEDUPLICATED PROPERLY) --------
@bot.event
async def on_voice_state_update(member, before, after):
    log = bot.get_channel(LOG_CHANNEL_ID)
    now = time.time()

    state = voice_state.get(member.id)

    # ===== JOIN =====
    if before.channel is None and after.channel is not None:
        # already marked as in voice → ignore duplicate
        if state and state["in_voice"]:
            return

        voice_state[member.id] = {
            "in_voice": True,
            "channel_id": after.channel.id,
            "start": now
        }
        ensure_user(member.id)

        if log:
            await log.send(
                f"🔊 joined voice channel\n"
                f"👤 {member.mention}\n"
                f"🎧 {after.channel.name}"
            )
        return

    # ===== LEAVE =====
    if before.channel is not None and after.channel is None:
        if not state or not state["in_voice"]:
            return

        duration = int(now - state["start"])
        voice_state[member.id]["in_voice"] = False

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
        return

    # ===== IGNORE EVERYTHING ELSE =====
    return

# ================= SLASH COMMANDS =================
@bot.tree.command(name="profile")
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
        f"🎙️ Voice: {h}h {m}m {s}s"
    )
@bot.tree.command(name="voicetop", description="Top voice time leaderboard")
async def voicetop(interaction: discord.Interaction):
    cursor.execute(
        "SELECT user_id, voice_time FROM users ORDER BY voice_time DESC LIMIT 10"
    )
    rows = cursor.fetchall()

    if not rows:
        await interaction.response.send_message("No voice data yet.")
        return

    text = "🏆 **Voice Time Leaderboard**\n\n"

    for i, (user_id, seconds) in enumerate(rows, start=1):
        member = interaction.guild.get_member(user_id)

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        name = member.name if member else f"User {user_id}"
        text += f"**{i}.** {name} — {hours}h {minutes}m\n"

    await interaction.response.send_message(text)

# ================= RUN =====================
bot.run(TOKEN)

