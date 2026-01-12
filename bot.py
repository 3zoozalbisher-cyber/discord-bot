import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True  # REQUIRED

bot = commands.Bot(command_prefix="!", intents=intents)

WELCOME_CHANNEL = "welcome"  # 👋😢 channel
ROLES_CHANNEL = "الترقيات"          # 🎭 roles channel

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# 👋 Member joins
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name=WELCOME_CHANNEL)
    if channel is None:
        return

    file = discord.File("images/welcome.png")
    await channel.send(
        content=f"👋 Welcome to the server, {member.mention}! 🎉",
        file=file
    )

# 😢 Member leaves
@bot.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.text_channels, name=WELCOME_CHANNEL)
    if channel is None:
        return

    file = discord.File("images/goodbye.png")
    await channel.send(
        content=f"😢 {member.name} has left the server. Goodbye!",
        file=file
    )

# 🎭 Roles added / removed
@bot.event
async def on_member_update(before, after):
    before_roles = set(before.roles)
    after_roles = set(after.roles)

    added_roles = after_roles - before_roles
    removed_roles = before_roles - after_roles

    channel = discord.utils.get(after.guild.text_channels, name=ROLES_CHANNEL)
    if channel is None:
        return

    # Role added
    for role in added_roles:
        if role.is_default():
            continue
        await channel.send(
            f"🎉 {after.mention} received the **{role.name}** role!"
        )

    # Role removed
    for role in removed_roles:
        if role.is_default():
            continue
        await channel.send(
            f"❌ {after.mention} lost the **{role.name}** role."
        )

bot.run(os.getenv("DISCORD_TOKEN"))
