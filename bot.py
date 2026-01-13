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

# -------- COOLDOWN STORAGE --------
cooldowns = {
    "join": {},
    "leave": {},
    "role": {},
    "voice": {}
}

def on_cooldown(bucket, key, seconds):
    now = time.time()
    last = cooldowns[bucket].get(key, 0)

    if now - last < seconds:
        return True

    cooldowns[bucket][key] = now
    return False

# -------- READY --------
@bot.event
async def on_ready():
    print(f"🟢 Logged in as {bot.user}")

# -------- MEMBER JOIN --------
@bot.event
async def on_member_join(member):
    if on_cooldown("join", member.id, 5):
        return

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
async def on_member_update(before, after):
    guild = after.guild
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    # Check audit log for role changes
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
        if entry.target.id != after.id:
            return

        # Added roles
        for role in entry.changes.after:
            if role not in before.roles:
                await channel.send(
                    f"✅ added role\n"
                    f"👤 {after.mention}\n"
                    f"🎭 {role.name}"
                )

        # Removed roles
        for role in entry.changes.before:
            if role not in after.roles:
                await channel.send(
                    f"❌ removed role\n"
                    f"👤 {after.mention}\n"
                    f"🎭 {role.name}"
                )

        break

# -------- VOICE JOIN / LEAVE (ANTI-SPAM SAFE) --------
@bot.event
async def on_voice_state_update(member, before, after):
    if on_cooldown("voice", member.id, 3):
        return

    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    if before.channel is None and after.channel is not None:
        await channel.send(
            f"🔊 joined voice channel\n"
            f"👤 {member.mention}"
        )

    elif before.channel is not None and after.channel is None:
        await channel.send(
            f"🔇 left voice channel\n"
            f"👤 {member.mention}"
        )

# -------- RUN --------
bot.run(TOKEN)
