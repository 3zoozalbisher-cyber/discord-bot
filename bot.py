import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import time
import json
import math
import re

# ================= CONFIG =================
TOKEN = os.getenv("DISCORD_TOKEN")

APPLICATION_ID = 1460013127063175229

WELCOME_CHANNEL_ID = 1414762426758463598
GOODBYE_CHANNEL_ID = 1460384380437659710
LOG_CHANNEL_ID = 1460366893994086554

MEMBER_COUNT_CHANNEL_ID = 1461682139308363779   # <-- PUT CHANNEL ID
VOICE_COUNT_CHANNEL_ID = 1461682183243563164    # <-- PUT CHANNEL ID

LEVEL_ROLES = {
    5: 0,    # level: role_id
    10: 0,
    20: 0
}

DATA_FILE = "data.json"
# =========================================

# ================= INTENTS =================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True
# ==========================================

# ================= BOT =====================
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=APPLICATION_ID
        )

    async def setup_hook(self):
        await self.tree.sync()
        update_stats.start()
        print("✅ Bot ready")

bot = MyBot()
# ==========================================

# ================= DATA ====================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()
voice_sessions = {}
xp_cooldown = {}
# ==========================================

def get_user(uid):
    uid = str(uid)
    if uid not in data:
        data[uid] = {
            "xp": 0,
            "level": 1,
            "voice": 0
        }
    return data[uid]

# ================= EVENTS ==================
@bot.event
async def on_ready():
    print(f"🟢 Logged in as {bot.user}")

# -------- JOIN / LEAVE --------
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(
            f"🎉 Welcome {member.mention}!",
            file=discord.File("images/welcome.png")
        )

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(GOODBYE_CHANNEL_ID)
    if channel:
        await channel.send(
            f"👋 {member.name} left the server",
            file=discord.File("images/goodbye.png")
        )

# -------- ROLE LOG --------
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

# -------- VOICE TRACKING --------
@bot.event
async def on_voice_state_update(member, before, after):
    now = time.time()

    if before.channel is None and after.channel:
        voice_sessions[member.id] = now

    elif before.channel and after.channel is None:
        start = voice_sessions.pop(member.id, None)
        if start:
            duration = int(now - start)
            user = get_user(member.id)
            user["voice"] += duration
            save_data()

# -------- XP + LEVELING --------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = message.author.id
    now = time.time()

    if now - xp_cooldown.get(uid, 0) < 30:
        return

    # Auto-mod (caps + links)
    if len(message.content) > 6 and message.content.isupper():
        await message.delete()
        return

    if re.search(r"https?://", message.content) and (time.time() - message.author.joined_at.timestamp()) < 86400:
        await message.delete()
        return

    xp_cooldown[uid] = now
    user = get_user(uid)

    user["xp"] += 10
    needed = user["level"] * 100

    if user["xp"] >= needed:
        user["xp"] = 0
        user["level"] += 1

        log = bot.get_channel(LOG_CHANNEL_ID)
        if log:
            await log.send(f"⭐ {message.author.mention} leveled up to **{user['level']}**!")

        # Level roles
        role_id = LEVEL_ROLES.get(user["level"])
        if role_id:
            role = message.guild.get_role(role_id)
            if role:
                await message.author.add_roles(role)

    save_data()
    await bot.process_commands(message)

# ================= TASKS ==================
@tasks.loop(minutes=5)
async def update_stats():
    guild = bot.guilds[0]

    members = guild.member_count
    voice = sum(1 for m in guild.members if m.voice)

    mc = bot.get_channel(MEMBER_COUNT_CHANNEL_ID)
    vc = bot.get_channel(VOICE_COUNT_CHANNEL_ID)

    if mc:
        await mc.edit(name=f"👥 Members: {members}")
    if vc:
        await vc.edit(name=f"🔊 In Voice: {voice}")

# ================= COMMANDS =================
@bot.tree.command(name="profile", description="View your profile")
async def profile(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    voice = user["voice"]
    h, rem = divmod(voice, 3600)
    m, s = divmod(rem, 60)

    await interaction.response.send_message(
        f"👤 {interaction.user.mention}\n"
        f"⭐ Level: {user['level']}\n"
        f"📊 XP: {user['xp']}/{user['level']*100}\n"
        f"🎙️ Voice: {h}h {m}m {s}s"
    )

@bot.tree.command(name="voicetop", description="Top voice users")
async def voicetop(interaction: discord.Interaction):
    leaderboard = sorted(data.items(), key=lambda x: x[1]["voice"], reverse=True)[:10]
    text = "🏆 **Voice Leaderboard**\n"
    for i, (uid, u) in enumerate(leaderboard, 1):
        member = interaction.guild.get_member(int(uid))
        h = u["voice"] // 3600
        m = (u["voice"] % 3600) // 60
        text += f"{i}. {member.name if member else 'User'} — {h}h {m}m\n"
    await interaction.response.send_message(text)

# ================= RUN =====================
bot.run(TOKEN)
