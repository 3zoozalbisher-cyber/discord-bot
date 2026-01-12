raise RuntimeError("BOT FILE EXECUTED")
print("BOT FILE LOADED")
import os
import json
import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta

# ================== TOKEN ==================
TOKEN = os.getenv("DISCORD_TOKEN")

# ================== CHANNEL IDS (CHANGE THESE) ==================
WELCOME_CHANNEL_ID = "1414762426758463598"
GOODBYE_CHANNEL_ID = "1460384380437659710"
ROLE_UPDATE_CHANNEL_ID = "1460009709875761354"
LOG_CHANNEL_ID = "1460366893994086554"

# ================== XP SYSTEM ==================
XP_FILE = "xp.json"

def load_xp():
    try:
        with open(XP_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_xp(data):
    with open(XP_FILE, "w") as f:
        json.dump(data, f)

xp_data = load_xp()

# ================== INTENTS ==================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        guild = discord.Object(id=998563480581963906)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

bot = MyBot()

# ================== READY ==================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    # Optional: test message
    guild = bot.guilds[0]
    channel = guild.get_channel(WELCOME_CHANNEL_ID)

    if channel:
        await channel.send("✅ Bot is online and can send messages!")

# ================== WELCOME ==================
@bot.event
async def on_member_join(member):
    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(
            content=f"🎉 Welcome {member.mention}!",
            file=discord.File("images/welcome.png")
        )

    log = member.guild.get_channel(LOG_CHANNEL_ID)
    if log:
        await log.send(f"📥 {member} joined the server")

# ================== GOODBYE ==================
@bot.event
async def on_member_remove(member):
    channel = member.guild.get_channel(GOODBYE_CHANNEL_ID)
    if channel:
        await channel.send(
            content=f"👋 Goodbye {member.name}",
            file=discord.File("images/goodbye.png")
        )

    log = member.guild.get_channel(LOG_CHANNEL_ID)
    if log:
        await log.send(f"📤 {member} left the server")

# ================== ROLE ADD / REMOVE ==================
@bot.event
async def on_member_update(before, after):
    role_channel = after.guild.get_channel(ROLE_UPDATE_CHANNEL_ID)
    log_channel = after.guild.get_channel(LOG_CHANNEL_ID)

    added_roles = set(after.roles) - set(before.roles)
    removed_roles = set(before.roles) - set(after.roles)

    for role in added_roles:
        if role_channel:
            await role_channel.send(
                f"🎉 {after.mention} has been given the **{role.name}** role!"
            )
        if log_channel:
            await log_channel.send(
                f"➕ {after} received role {role.name}"
            )

    for role in removed_roles:
        if role_channel:
            await role_channel.send(
                f"👋 {after.mention} lost the **{role.name}** role."
            )
        if log_channel:
            await log_channel.send(
                f"➖ {after} lost role {role.name}"
            )

# ================== MESSAGE DELETE LOG ==================
@bot.event
async def on_message_delete(message):
    if message.author.bot or not message.guild:
        return

    log = message.guild.get_channel(LOG_CHANNEL_ID)
    if log:
        await log.send(f"🗑️ Deleted message from {message.author}")

# ================== XP SYSTEM ==================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    xp_data.setdefault(user_id, {"xp": 0, "level": 1})
    xp_data[user_id]["xp"] += 5

    next_level = xp_data[user_id]["level"] * 100
    if xp_data[user_id]["xp"] >= next_level:
        xp_data[user_id]["level"] += 1
        await message.channel.send(
            f"🎉 {message.author.mention} reached **Level {xp_data[user_id]['level']}**!"
        )

    save_xp(xp_data)
    await bot.process_commands(message)

# ================== SLASH COMMANDS ==================
@bot.tree.command(name="ping", description="Check if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

@bot.tree.command(name="level", description="Check your level")
async def level(interaction: discord.Interaction):
    data = xp_data.get(str(interaction.user.id), {"xp": 0, "level": 1})
    await interaction.response.send_message(
        f"⭐ Level: {data['level']}\n✨ XP: {data['xp']}"
    )

# ================== MODERATION ==================
@bot.tree.command(name="kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    await member.kick(reason=reason)
    await interaction.response.send_message(f"👢 Kicked {member}")

@bot.tree.command(name="ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 Banned {member}")

@bot.tree.command(name="mute")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int):
    await member.timeout(timedelta(minutes=minutes))
    await interaction.response.send_message(
        f"🔇 Muted {member} for {minutes} minutes"
    )

# ================== RUN ==================
@bot.event
async def on_ready():
    print("BOT READY")

    guild = bot.guilds[0]
    channel = guild.get_channel(WELCOME_CHANNEL_ID)

    print("CHANNEL:", channel)

    if channel:
        await channel.send("✅ TEST MESSAGE FROM BOT")
    else:
        print("CHANNEL IS NONE")

bot.run(TOKEN)
