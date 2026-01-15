import discord
from discord.ext import commands
from discord import app_commands
import os
import time

# ================= CONFIG =================
TOKEN = os.getenv("DISCORD_TOKEN")

WELCOME_CHANNEL_ID = 1414762426758463598
GOODBYE_CHANNEL_ID = 1460384380437659710
LOG_CHANNEL_ID = 1460366893994086554
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
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()
# ==========================================

# ============ VOICE TRACKING ===============
voice_sessions = {}
# ==========================================

# ================= EVENTS ==================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# --------- MEMBER JOIN (WITH IMAGE) --------
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        file = discord.File("images/welcome.png")
        await channel.send(
            content=f"🎉 Welcome {member.mention}!",
            file=file
        )

# -------- MEMBER LEAVE (WITH IMAGE) --------
@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(GOODBYE_CHANNEL_ID)
    if channel:
        file = discord.File("images/goodbye.png")
        await channel.send(
            content=f"👋 {member.name} left the server",
            file=file
        )

# -------- ROLE ADD / REMOVE (NO DUPES) -----
@bot.event
async def on_member_update(before, after):
    log = bot.get_channel(LOG_CHANNEL_ID)
    if not log:
        return

    before_roles = set(before.roles)
    after_roles = set(after.roles)

    added_roles = after_roles - before_roles
    removed_roles = before_roles - after_roles

    for role in added_roles:
        if role.is_default():
            continue
        await log.send(
            f"✅ added role\n"
            f"👤 {after.mention}\n"
            f"🎭 {role.name}"
        )

    for role in removed_roles:
        if role.is_default():
            continue
        await log.send(
            f"❌ removed role\n"
            f"👤 {after.mention}\n"
            f"🎭 {role.name}"
        )

# -------- VOICE JOIN / LEAVE + TIME --------
@bot.event
async def on_voice_state_update(member, before, after):
    log = bot.get_channel(LOG_CHANNEL_ID)
    now = time.time()

    # JOIN
    if before.channel is None and after.channel is not None:
        voice_sessions[member.id] = now
        if log:
            await log.send(
                f"🔊 joined voice channel\n"
                f"👤 {member.mention}\n"
                f"🎧 {after.channel.name}"
            )

    # LEAVE
    elif before.channel is not None and after.channel is None:
        start_time = voice_sessions.pop(member.id, None)
        if start_time:
            duration = int(now - start_time)
            minutes = duration // 60
            seconds = duration % 60

            if log:
                await log.send(
                    f"🔇 left voice channel\n"
                    f"👤 {member.mention}\n"
                    f"🎧 {before.channel.name}\n"
                    f"⏱️ {minutes}m {seconds}s"
                )

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

# ================= RUN =====================
bot.run(TOKEN)
