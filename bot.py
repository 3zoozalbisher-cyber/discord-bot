import discord
from discord.ext import commands
from discord import app_commands
import os

# ---------- CHANNEL CONFIG ----------
WELCOME_CHANNEL_ID = 1414762426758463598
GOODBYE_CHANNEL_ID = 1460384380437659710
LOG_CHANNEL_ID     = 1460366893994086554

TOKEN = os.getenv("DISCORD_TOKEN")

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.members = True
intents.voice_states = True

# ---------- BOT ----------
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ Slash commands synced")

bot = MyBot()

# ---------- READY ----------
@bot.event
async def on_ready():
    print(f"🟢 Logged in as {bot.user}")

# ---------- SLASH COMMAND ----------
@bot.tree.command(name="ping", description="Check if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! Bot is alive.")

# ---------- MEMBER JOIN (WELCOME CHANNEL) ----------
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if not channel:
        return

    file = discord.File("images/welcome.png", filename="welcome.png")
    embed = discord.Embed(
        title="👋 Welcome!",
        description=f"Welcome {member.mention} to **{member.guild.name}**!",
        color=discord.Color.green()
    )
    embed.set_image(url="attachment://welcome.png")
    await channel.send(embed=embed, file=file)

# ---------- MEMBER LEAVE (GOODBYE CHANNEL) ----------
@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(GOODBYE_CHANNEL_ID)
    if not channel:
        return

    file = discord.File("images/goodbye.png", filename="goodbye.png")
    embed = discord.Embed(
        title="👋 Goodbye!",
        description=f"**{member.name}** has left the server.",
        color=discord.Color.red()
    )
    embed.set_image(url="attachment://goodbye.png")
    await channel.send(embed=embed, file=file)

# ---------- ROLE ADD / REMOVE (LOG CHANNEL) ----------
@bot.event
async def on_member_update(before, after):
    before_roles = set(before.roles)
    after_roles = set(after.roles)

    added_roles = after_roles - before_roles
    removed_roles = before_roles - after_roles

    if not added_roles and not removed_roles:
        return

    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    for role in added_roles:
        if role.is_default():
            continue
        await channel.send(f"🎉 {after.mention} was given **{role.name}**")

    for role in removed_roles:
        if role.is_default():
            continue
        await channel.send(f"❌ {after.mention} lost **{role.name}**")

# ---------- VOICE JOIN / LEAVE (LOG CHANNEL) ----------
@bot.event
async def on_voice_state_update(member, before, after):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    if before.channel is None and after.channel is not None:
        await channel.send(f"🔊 {member.mention} joined **{after.channel.name}**")
    elif before.channel is not None and after.channel is None:
        await channel.send(f"🔇 {member.mention} left **{before.channel.name}**")

# ---------- RUN ----------
bot.run(TOKEN)
