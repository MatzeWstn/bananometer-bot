from flask import Flask
from threading import Thread

import discord
from discord.ext import commands, tasks
import random
import json
import os
from datetime import datetime, timedelta

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

data_file = "banana_data.json"

if not os.path.exists(data_file):
    with open(data_file, "w") as f:
        json.dump({}, f)

ränge = [
    "Mini-Schlappi 🍒", "Gurkenlord 🥒", "Schnellspritz-König 💦",
    "Pimmel-Pirat 🏴‍☠️", "Banana Boss 🍌", "Schlaffi des Monats 😔",
    "Wachsender Hoffnungsträger 🌱", "Unterschätzte Legende 🔍",
    "NASA-Material 🚀", "Flexx-Gott 😎"
]

@bot.event
async def on_ready():
    print(f"✅ Bananometer ist online als {bot.user}")
    update_king_role.start()

@tasks.loop(minutes=5)
async def update_king_role():
    with open(data_file, "r") as f:
        data = json.load(f)
    if not data:
        return
    top_user_id = max(data.items(), key=lambda x: x[1]['length'])[0]
    guild = discord.utils.get(bot.guilds)
    role = discord.utils.get(guild.roles, name="🍌 King Banana")
    if not role:
        return
    for member in guild.members:
        if role in member.roles and str(member.id) != top_user_id:
            await member.remove_roles(role)
        elif str(member.id) == top_user_id and role not in member.roles:
            await member.add_roles(role)

@bot.command(name="banana")
async def banana(ctx):
    with open(data_file, "r") as f:
        data = json.load(f)

    user_id = str(ctx.author.id)
    now = datetime.utcnow()
    last_used_str = data.get(user_id, {}).get("last_used")
    if last_used_str:
        last_used = datetime.strptime(last_used_str, "%Y-%m-%d %H:%M:%S")
        if now - last_used < timedelta(hours=3):
            remaining = timedelta(hours=3) - (now - last_used)
            mins = int(remaining.total_seconds() // 60)
            await ctx.send(f"⏳ Du musst noch {mins} Minuten warten, bevor du wieder messen kannst!")
            return

    cm = round(random.uniform(0.5, 25.0), 1)
    rang = random.choice(ränge)
    emojis = ["🍌", "💦", "📏", "😳", "☠️", "🤏", "🔬"]
    kommentar = ""

    if cm < 3:
        kommentar = "Der ist klein UND dünn!! 🔬"
    elif cm < 7:
        kommentar = "Klein, aber stinkt wie nh großer!. 🤏"
    elif cm < 12:
        kommentar = "Nice Schwons Bro 🍌"
    elif cm < 16:
        kommentar = "Du kannst mit nem harten gegen die Wand rennen und brichst dir trotzdem die Nase! 🍌"
    elif cm < 20:
        kommentar = "Ohjoo Bro, chill mo dei Bux 💦"
    else:
        kommentar = "Unreal im Benanengame 🚀"

    old_entry = data.get(user_id, {})
    count = old_entry.get("count", 0) + 1
    history = old_entry.get("history", [])
    history.append(cm)

    data[user_id] = {
        "name": ctx.author.display_name,
        "length": cm,
        "rank": rang,
        "count": count,
        "last_used": now.strftime("%Y-%m-%d %H:%M:%S"),
        "history": history
    }

    with open(data_file, "w") as f:
        json.dump(data, f, indent=4)

    await ctx.message.add_reaction("🍌")
    if cm < 3:
        await ctx.message.add_reaction("☠️")
    elif cm < 7:
        await ctx.message.add_reaction("🤏")
    elif cm > 18:
        await ctx.message.add_reaction("😳")

    await ctx.send(
        f"📏 **{ctx.author.display_name}’s Bananometer-Ergebnis:** {cm}cm {random.choice(emojis)}\n"
        f"🏷️ Titel: *{rang}*\n"
        f"💬 _{kommentar}_"
    )

@bot.command(name="vergleich")
async def vergleichen(ctx, user1: discord.Member, user2: discord.Member):
    with open(data_file, "r") as f:
        data = json.load(f)

    id1 = str(user1.id)
    id2 = str(user2.id)

    if id1 not in data or id2 not in data:
        await ctx.send("🔍 Einer der beiden hat sich noch nicht messen lassen!")
        return

    d1 = data[id1]
    d2 = data[id2]

    msg = f"**🍌 Vergleich:**\n{user1.display_name}: {d1['length']}cm\n{user2.display_name}: {d2['length']}cm\n"
    if d1["length"] > d2["length"]:
        msg += f"➡️ **{user1.display_name}** hat die 🍌 vorne!"
    elif d2["length"] > d1["length"]:
        msg += f"➡️ **{user2.display_name}** hat die 🍌 vorne!"
    else:
        msg += "⚖️ Unentschieden – zwei gleich lange Legenden."

    await ctx.send(msg)

# Webserver für UptimeRobot
app = Flask('')

@app.route('/')
def home():
    return "Ich bin wach!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Starte Webserver und Bot
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
