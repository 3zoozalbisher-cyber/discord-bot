import os
import discord
from discord.ext import commands

# ---------------- INTENTS ----------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# ---------------- BOT ----------------
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- CHANNEL IDS ----------------
WELCOME_CHANNEL_ID = 1414762426758463598     # welcome channel
GOODBYE_CHANNEL_ID = 1460384380437659710     # goodbye channel
ROLE_MESSAGE_CHANNEL_ID = 1460009709875761354  # public role messages
LOG_CHANNEL_ID = 1460366893994086554         # private log channel

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

# ---------------- WELCOME ----------------
@bot.event
async def on_member_join(member):
    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(f"👋 Welcome {member.mention}! 🎉")

# ---------------- GOODBYE ----------------
@bot.event
async def on_member_remove(member):
    channel = member.guild.get_channel(GOODBYE_CHANNEL_ID)
    if channel:
        await channel.send(f"👋 **{member.name}** has left the server.")

# ---------------- ROLE ADD / REMOVE ----------------
@bot.event
async def on_member_update(before, after):
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
                f"✅ ROLE ADDED | User: {after} | Role: {role.name}"
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
                f"❌ ROLE REMOVED | User: {after} | Role: {role.name}"
            )

# ---------------- RUN ----------------
bot.run(os.getenv("DISCORD_TOKEN"))
