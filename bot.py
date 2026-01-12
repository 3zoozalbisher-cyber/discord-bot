import os
import time
import discord
from discord.ext import commands

# ---------------- INTENTS ----------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

# ---------------- BOT ----------------
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- CHANNEL IDS ----------------
WELCOME_CHANNEL_ID = 1414762426758463598
GOODBYE_CHANNEL_ID = 1460384380437659710
ROLE_MESSAGE_CHANNEL_ID = 1460009709875761354
LOG_CHANNEL_ID = 1460366893994086554

# ---------------- ROLE EVENT CACHE (ANTI-DUPLICATE) ----------------
role_event_cache = {}
ROLE_EVENT_COOLDOWN = 2  # seconds

# ---------------- READY ----------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ---------------- SLASH COMMAND ----------------
@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

@bot.event
async def setup_hook():
    await bot.tree.sync()

# ---------------- WELCOME (IMAGE) ----------------
@bot.event
async def on_member_join(member):
    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if not channel:
        return

    file = discord.File("images/welcome.png", filename="welcome.png")
    embed = discord.Embed(
        title="👋 Welcome!",
        description=f"Welcome {member.mention} to the server 🎉",
        color=0x2ecc71
    )
    embed.set_image(url="attachment://welcome.png")

    await channel.send(embed=embed, file=file)

# ---------------- GOODBYE (IMAGE) ----------------
@bot.event
async def on_member_remove(member):
    channel = member.guild.get_channel(GOODBYE_CHANNEL_ID)
    if not channel:
        return

    file = discord.File("images/goodbye.png", filename="goodbye.png")
    embed = discord.Embed(
        title="👋 Goodbye!",
        description=f"**{member.name}** has left the server.",
        color=0xe74c3c
    )
    embed.set_image(url="attachment://goodbye.png")

    await channel.send(embed=embed, file=file)

# ---------------- ROLE ADD / REMOVE (NO DUPLICATES) ----------------
@bot.event
async def on_member_update(before, after):
    now = time.time()
    cache_key = (after.id, after.guild.id)

    if cache_key in role_event_cache:
        if now - role_event_cache[cache_key] < ROLE_EVENT_COOLDOWN:
            return

    role_event_cache[cache_key] = now

    if before.roles == after.roles:
        return

    public_channel = after.guild.get_channel(ROLE_MESSAGE_CHANNEL_ID)
    log_channel = after.guild.get_channel(LOG_CHANNEL_ID)

    added_roles = set(after.roles) - set(before.roles)
    removed_roles = set(before.roles) - set(after.roles)

    for role in added_roles:
        if role.is_default():
            continue

        if public_channel:
            await public_channel.send(
                f"🎉 {after.mention} received the **{role.name}** role!"
            )

        if log_channel:
            await log_channel.send(
                f"✅ **ROLE ADDED**\n👤 {after.mention}\n🎭 `{role.name}`"
            )

    for role in removed_roles:
        if role.is_default():
            continue

        if public_channel:
            await public_channel.send(
                f"❌ {after.mention} lost the **{role.name}** role."
            )

        if log_channel:
            await log_channel.send(
                f"❌ **ROLE REMOVED**\n👤 {after.mention}\n🎭 `{role.name}`"
            )

# ---------------- VOICE CHANNEL LOGGING ----------------
@bot.event
async def on_voice_state_update(member, before, after):
    log_channel = member.guild.get_channel(LOG_CHANNEL_ID)
    if not log_channel:
        return

    if before.channel is None and after.channel is not None:
        await log_channel.send(
            f"🔊 **VOICE JOIN**\n👤 {member.mention}\n📺 `{after.channel.name}`"
        )

    elif before.channel is not None and after.channel is None:
        await log_channel.send(
            f"🔇 **VOICE LEAVE**\n👤 {member.mention}\n📺 `{before.channel.name}`"
        )

    elif before.channel != after.channel:
        await log_channel.send(
            f"🔁 **VOICE MOVE**\n👤 {member.mention}\n➡️ `{before.channel.name}` → `{after.channel.name}`"
        )

# ---------------- RUN ----------------
bot.run(os.getenv("DISCORD_TOKEN"))
