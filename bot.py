import discord
from discord.ext import commands
import os

# ---------- CHANNEL IDS ----------
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
        super().__init__(command_prefix=None, intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

# ---------- READY ----------
@bot.event
async def on_ready():
    print(f"🟢 Logged in as {bot.user}")

# ---------- WELCOME ----------
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if not channel:
        return

    file = discord.File("images/welcome.png", filename="welcome.png")
    embed = discord.Embed(
        title="👋 Welcome!",
        description=f"{member.mention} joined **{member.guild.name}**",
        color=discord.Color.green()
    )
    embed.set_image(url="attachment://welcome.png")
    await channel.send(embed=embed, file=file)

# ---------- GOODBYE ----------
@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(GOODBYE_CHANNEL_ID)
    if not channel:
        return

    file = discord.File("images/goodbye.png", filename="goodbye.png")
    embed = discord.Embed(
        title="👋 Goodbye!",
        description=f"**{member.name}** left the server",
        color=discord.Color.red()
    )
    embed.set_image(url="attachment://goodbye.png")
    await channel.send(embed=embed, file=file)

# ---------- ROLE ADD / REMOVE ----------
@bot.event
async def on_member_update(before, after):
    if before.roles == after.roles:
        return

    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    before_roles = set(before.roles)
    after_roles = set(after.roles)

    for role in after_roles - before_roles:
        if role.is_default():
            continue

        embed = discord.Embed(
            title="🎉 Role Added",
            color=discord.Color.green()
        )
        embed.add_field(name="User", value=after.mention, inline=False)
        embed.add_field(name="Role", value=role.name, inline=False)

        await channel.send(embed=embed)

    for role in before_roles - after_roles:
        if role.is_default():
            continue

        embed = discord.Embed(
            title="❌ Role Removed",
            color=discord.Color.red()
        )
        embed.add_field(name="User", value=after.mention, inline=False)
        embed.add_field(name="Role", value=role.name, inline=False)

        await channel.send(embed=embed)

# ---------- VOICE JOIN / LEAVE (SAME STYLE) ----------
@bot.event
async def on_voice_state_update(member, before, after):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    if before.channel is None and after.channel is not None:
        embed = discord.Embed(
            title="🔊 Voice Channel Joined",
            color=discord.Color.blue()
        )
        embed.add_field(name="User", value=member.mention, inline=False)
        embed.add_field(name="Channel", value=after.channel.name, inline=False)

        await channel.send(embed=embed)

    elif before.channel is not None and after.channel is None:
        embed = discord.Embed(
            title="🔇 Voice Channel Left",
            color=discord.Color.orange()
        )
        embed.add_field(name="User", value=member.mention, inline=False)
        embed.add_field(name="Channel", value=before.channel.name, inline=False)

        await channel.send(embed=embed)

# ---------- RUN ----------
bot.run(TOKEN)
