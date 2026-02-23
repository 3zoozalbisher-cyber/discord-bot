import discord
from discord.ext import commands
import os
import time
import sqlite3
import random

# ================= CONFIG =================
TOKEN = os.getenv("DISCORD_TOKEN")

WELCOME_CHANNEL_ID = 1414762426758463598
GOODBYE_CHANNEL_ID = 1460384380437659710
LOG_CHANNEL_ID = 1460366893994086554
APPLICATION_ID = 1460013127063175229
# =========================================

# ================= DATABASE =================
db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    voice_time INTEGER DEFAULT 0,
    coins INTEGER DEFAULT 0
)
""")
db.commit()
# ==========================================

# ================= INTENTS =================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True
# ==========================================

# ================= BOT =====================
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    application_id=APPLICATION_ID
)

voice_sessions = {}
message_cooldown = {}
daily_cooldown = {}

# ================= HELPERS =================
def ensure_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    db.commit()

async def level_up_announce(user_id, level):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        user = bot.get_user(user_id)
        if user:
            await channel.send(
                f"🎉 LEVEL UP!\n"
                f"👤 {user.mention}\n"
                f"⭐ New Level: {level}"
            )

def add_coins(user_id, amount):
    ensure_user(user_id)
    cursor.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,))
    coins = cursor.fetchone()[0]
    coins = max(0, coins + amount)
    cursor.execute("UPDATE users SET coins = ? WHERE user_id = ?", (coins, user_id))
    db.commit()

async def add_xp(user_id, amount):
    ensure_user(user_id)
    cursor.execute("SELECT xp, level FROM users WHERE user_id = ?", (user_id,))
    xp, level = cursor.fetchone()

    xp += amount
    needed = level * 100
    leveled_up = False

    while xp >= needed:
        xp -= needed
        level += 1
        needed = level * 100
        leveled_up = True

    cursor.execute("UPDATE users SET xp = ?, level = ? WHERE user_id = ?", (xp, level, user_id))
    db.commit()

    if leveled_up:
        await level_up_announce(user_id, level)

# ==========================================

# ================= EVENTS ==================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    now = time.time()
    last = message_cooldown.get(message.author.id, 0)

    if now - last >= 30:
        await add_xp(message.author.id, 5)
        add_coins(message.author.id, 3)
        message_cooldown[message.author.id] = now

    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    now = time.time()

    if before.channel is None and after.channel is not None:
        voice_sessions[member.id] = now
        ensure_user(member.id)

    if before.channel is not None and after.channel is None:
        start = voice_sessions.pop(member.id, None)
        if not start:
            return

        duration = int(now - start)
        minutes = duration // 60

        if minutes > 0:
            await add_xp(member.id, minutes * 10)
            add_coins(member.id, minutes * 5)

        cursor.execute(
            "UPDATE users SET voice_time = voice_time + ? WHERE user_id = ?",
            (duration, member.id)
        )
        db.commit()

@bot.event
async def on_member_join(member):
    ch = bot.get_channel(WELCOME_CHANNEL_ID)
    if ch:
        await ch.send(
            f"🎉 Welcome {member.mention}!",
            file=discord.File("images/welcome.png")
        )

@bot.event
async def on_member_remove(member):
    ch = bot.get_channel(GOODBYE_CHANNEL_ID)
    if ch:
        await ch.send(
            f"👋 {member.name} left the server",
            file=discord.File("images/goodbye.png")
        )

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

# ================= SLASH COMMANDS =================

@bot.tree.command(name="profile")
async def profile(interaction: discord.Interaction):
    ensure_user(interaction.user.id)
    cursor.execute(
        "SELECT xp, level, voice_time, coins FROM users WHERE user_id = ?",
        (interaction.user.id,)
    )
    xp, level, voice, coins = cursor.fetchone()

    needed = level * 100
    progress = int((xp / needed) * 20)
    bar = "🟩" * progress + "⬛" * (20 - progress)

    h = voice // 3600
    m = (voice % 3600) // 60
    s = voice % 60

    await interaction.response.send_message(
        f"👤 {interaction.user.mention}\n"
        f"⭐ Level: {level}\n"
        f"📊 XP: {xp}/{needed}\n"
        f"{bar}\n"
        f"🎙️ Voice: {h}h {m}m {s}s\n"
        f"💰 Coins: {coins}"
    )

@bot.tree.command(name="voicetop")
async def voicetop(interaction: discord.Interaction):
    cursor.execute(
        "SELECT user_id, voice_time FROM users ORDER BY voice_time DESC LIMIT 10"
    )
    rows = cursor.fetchall()

    text = "🏆 Voice Leaderboard\n\n"
    for i, (uid, seconds) in enumerate(rows, start=1):
        member = interaction.guild.get_member(uid)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        name = member.name if member else f"User {uid}"
        text += f"{i}. {name} — {hours}h {minutes}m\n"

    await interaction.response.send_message(text)

@bot.tree.command(name="balance")
async def balance(interaction: discord.Interaction):
    ensure_user(interaction.user.id)
    cursor.execute("SELECT coins FROM users WHERE user_id = ?", (interaction.user.id,))
    coins = cursor.fetchone()[0]
    await interaction.response.send_message(f"💰 You have {coins} coins.")

@bot.tree.command(name="daily")
async def daily(interaction: discord.Interaction):
    now = time.time()
    last = daily_cooldown.get(interaction.user.id, 0)

    if now - last < 86400:
        await interaction.response.send_message("⏳ Already claimed today.", ephemeral=True)
        return

    reward = 200
    add_coins(interaction.user.id, reward)
    daily_cooldown[interaction.user.id] = now
    await interaction.response.send_message(f"💰 You claimed {reward} coins!")

@bot.tree.command(name="gamble")
async def gamble(interaction: discord.Interaction, amount: int):
    ensure_user(interaction.user.id)
    cursor.execute("SELECT coins FROM users WHERE user_id = ?", (interaction.user.id,))
    coins = cursor.fetchone()[0]

    if amount <= 0 or amount > coins:
        await interaction.response.send_message("❌ Invalid amount.", ephemeral=True)
        return

    if random.randint(1, 2) == 1:
        add_coins(interaction.user.id, amount)
        await interaction.response.send_message(f"🎉 You won {amount} coins!")
    else:
        add_coins(interaction.user.id, -amount)
        await interaction.response.send_message(f"💀 You lost {amount} coins.")

@bot.tree.command(name="addcoins")
async def addcoins(interaction: discord.Interaction, user: discord.Member, amount: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No permission.", ephemeral=True)
        return
    add_coins(user.id, amount)
    await interaction.response.send_message(f"Added {amount} coins to {user.mention}")

@bot.tree.command(name="removecoins")
async def removecoins(interaction: discord.Interaction, user: discord.Member, amount: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No permission.", ephemeral=True)
        return
    add_coins(user.id, -amount)
    await interaction.response.send_message(f"Removed {amount} coins from {user.mention}")

@bot.tree.command(name="shop")
async def shop(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🛒 SHOP\n\n"
        "xpboost - 500 coins (+50 XP)\n"
        "lottery - 1000 coins (50% win 2000 coins)"
    )

@bot.tree.command(name="buy")
async def buy(interaction: discord.Interaction, item: str):
    ensure_user(interaction.user.id)

    if item.lower() == "xpboost":
        cost = 500
        cursor.execute("SELECT coins FROM users WHERE user_id = ?", (interaction.user.id,))
        coins = cursor.fetchone()[0]
        if coins < cost:
            await interaction.response.send_message("Not enough coins.")
            return
        add_coins(interaction.user.id, -cost)
        await add_xp(interaction.user.id, 50)
        await interaction.response.send_message("You bought XP Boost!")

    elif item.lower() == "lottery":
        cost = 1000
        cursor.execute("SELECT coins FROM users WHERE user_id = ?", (interaction.user.id,))
        coins = cursor.fetchone()[0]
        if coins < cost:
            await interaction.response.send_message("Not enough coins.")
            return
        add_coins(interaction.user.id, -cost)
        if random.randint(1, 2) == 1:
            add_coins(interaction.user.id, 2000)
            await interaction.response.send_message("🎉 You won the lottery!")
        else:
            await interaction.response.send_message("💀 You lost the lottery.")

@bot.tree.command(name="jl5")
async def jl5(interaction: discord.Interaction):
    await interaction.response.send_message("Your ASCII art here")

# ================= RUN =====================
bot.run(TOKEN)
