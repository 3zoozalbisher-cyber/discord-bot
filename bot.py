import discord
from discord.ext import commands
from discord import app_commands
import os
import time
import math

# ================= CONFIG =================
TOKEN = os.getenv("DISCORD_TOKEN")

WELCOME_CHANNEL_ID = 1414762426758463598
GOODBYE_CHANNEL_ID = 1460384380437659710
LOG_CHANNEL_ID = 1460366893994086554

APPLICATION_ID = 1460013127063175229
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
        print("✅ Slash commands synced")

bot = MyBot()
# ==========================================

# ================= STORAGE =================
voice_sessions = {}
total_voice_time = {}   # user_id -> seconds

xp_data = {}            # user_id -> xp
level_data = {}         # user_id -> level
xp_cooldown = {}        # user_id -> timestamp
# ==========================================

# ================= EVENTS ==================
@bot.event
async def on_ready():
    print(f"🟢 Logged in as {bot.user}")

# --------- MEMBER JOIN ---------
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        try:
            file = discord.File("images/welcome.png")
            await channel.send(f"🎉 Welcome {member.mention}!", file=file)
        except:
            pass

# -------- MEMBER LEAVE --------
@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(GOODBYE_CHANNEL_ID)
    if channel:
        try:
            file = discord.File("images/goodbye.png")
            await channel.send(f"👋 {member.name} left the server", file=file)
        except:
            pass

# -------- ROLE LOG --------
@bot.event
async def on_member_update(before, after):
    log = bot.get_channel(LOG_CHANNEL_ID)
    if not log:
        return

    before_roles = set(before.roles)
    after_roles = set(after.roles)

    for role in after_roles - before_roles:
        if not role.is_default():
            await log.send(
                f"✅ added role\n👤 {after.mention}\n🎭 {role.name}"
            )

    for role in before_roles - after_roles:
        if not role.is_default():
            await log.send(
                f"❌ removed role\n👤 {after.mention}\n🎭 {role.name}"
            )

# -------- VOICE TRACKING --------
@bot.event
async def on_voice_state_update(member, before, after):
    log = bot.get_channel(LOG_CHANNEL_ID)
    now = time.time()

    if before.channel is None and after.channel is not None:
        voice_sessions[member.id] = now
        if log:
            await log.send(
                f"🔊 joined voice channel\n👤 {member.mention}\n🎧 {after.channel.name}"
            )

    elif before.channel is not None and after.channel is None:
        start = voice_sessions.pop(member.id, None)
        if start:
            duration = int(now - start)
            total_voice_time[member.id] = total_voice_time.get(member.id, 0) + duration

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

# -------- XP SYSTEM --------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    now = time.time()

    if now - xp_cooldown.get(user_id, 0) < 30:
        return

    xp_cooldown[user_id] = now
    xp_data[user_id] = xp_data.get(user_id, 0) + 10

    level = level_data.get(user_id, 1)
    xp_needed = level * 100

    if xp_data[user_id] >= xp_needed:
        level_data[user_id] = level + 1
        xp_data[user_id] = 0

        log = bot.get_channel(LOG_CHANNEL_ID)
        if log:
            await log.send(
                f"⭐ LEVEL UP!\n"
                f"👤 {message.author.mention}\n"
                f"🏆 Level {level + 1}"
            )

    await bot.process_commands(message)

# ================= SLASH COMMANDS =================

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 Pong! `{round(bot.latency * 1000)}ms`"
    )

@bot.tree.command(name="hello", description="Say hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"👋 Hello {interaction.user.mention}!"
    )

@bot.tree.command(name="level", description="Check your level")
async def level(interaction: discord.Interaction):
    uid = interaction.user.id
    lvl = level_data.get(uid, 1)
    xp = xp_data.get(uid, 0)
    await interaction.response.send_message(
        f"⭐ Level: {lvl}\n📊 XP: {xp}/{lvl*100}"
    )

@bot.tree.command(name="voicetop", description="Top voice time users")
async def voicetop(interaction: discord.Interaction):
    if not total_voice_time:
        await interaction.response.send_message("No voice data yet.")
        return

    leaderboard = sorted(
        total_voice_time.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    text = "🏆 **Voice Time Leaderboard**\n"
    for i, (uid, seconds) in enumerate(leaderboard, 1):
        member = interaction.guild.get_member(uid)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        text += f"{i}. {member.name if member else 'User'} — {h}h {m}m\n"

    await interaction.response.send_message(text)

# ================= RUN =====================
bot.run(TOKEN)
