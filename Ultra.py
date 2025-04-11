import discord
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
import random
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Intents & Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!", "/"), intents=intents)

data_file = "banana_data.json"

# JSON-Datei erstellen, falls nicht vorhanden
if not os.path.exists(data_file):
    with open(data_file, "w") as f:
        json.dump({}, f)

# Rangliste
ränge = [
    "Mini-Schlappi 🍒", "Gurkenlord 🥒", "Schnellspritz-König 💦",
    "Pimmel-Pirat 🏴‍☠️", "Banana Boss 🍌", "Schlaffi des Monats 😔",
    "Wachsender Hoffnungsträger 🌱", "Unterschätzte Legende 🔍",
    "NASA-Material 🚀", "Flexx-Gott 😎"
]

# Flask Webserver für Render/UptimeRobot
app = Flask(__name__)
@app.route('/')
def home():
    return "Ich bin wach!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Bot ist bereit
@bot.event
async def on_ready():
    print(f"✅ Bananometer ist online als {bot.user}")
    update_king_role.start()
    try:
        synced = await bot.tree.sync()
        print(f"📡 Slash-Commands synchronisiert: {len(synced)}")
    except Exception as e:
        print(f"❌ Fehler beim Slash-Sync: {e}")

# King Banana Auto-Rolle
@tasks.loop(minutes=5)
async def update_king_role():
    try:
        with open(data_file, "r") as f:
            data = json.load(f)
    except:
        return

    if not data: return

    top_user_id = max(data.items(), key=lambda x: x[1]["length"])[0]
    guild = discord.utils.get(bot.guilds)
    role = discord.utils.get(guild.roles, name="🍌 King Banana")
    if not role: return

    for member in guild.members:
        if role in member.roles and str(member.id) != top_user_id:
            await member.remove_roles(role)
        elif str(member.id) == top_user_id and role not in member.roles:
            await member.add_roles(role)

# Kommandos (Prefix & Slash)
@bot.command(name="banana")
async def banana(ctx):
    with open(data_file, "r") as f:
        data = json.load(f)

    user_id = str(ctx.author.id)
    now = datetime.utcnow()
    last_used = data.get(user_id, {}).get("last_used")
    if last_used:
        last_used = datetime.strptime(last_used, "%Y-%m-%d %H:%M:%S")
        if now - last_used < timedelta(hours=3):
            remaining = timedelta(hours=3) - (now - last_used)
            minutes = int(remaining.total_seconds() // 60)
            await ctx.send(f"⏳ Noch {minutes} Minuten bis zur nächsten Messung!")
            return

    cm = round(random.uniform(0.5, 25.0), 1)
    rang = random.choice(ränge)
    emojis = ["🍌", "💦", "📏", "😳", "☠️", "🤏", "🔬"]

    kommentar = {
        cm < 3: "Der ist klein UND dünn!! 🔬",
        cm < 7: "Klein, aber stinkt wie 'n großer! 🤏",
        cm < 12: "Nice Schwons Bro 🍌",
        cm < 16: "Du kannst mit 'nem harten gegen die Wand rennen! 🍌",
        cm < 20: "Ohjoo Bro, chill mo dei Bux 💦"
    }.get(True, "Unreal im Bananen-Game 🚀")

    old = data.get(user_id, {})
    history = old.get("history", [])
    history.append(cm)

    data[user_id] = {
        "name": ctx.author.display_name,
        "length": cm,
        "rank": rang,
        "count": old.get("count", 0) + 1,
        "last_used": now.strftime("%Y-%m-%d %H:%M:%S"),
        "history": history
    }

    with open(data_file, "w") as f:
        json.dump(data, f, indent=4)

    await ctx.message.add_reaction("🍌")
    await ctx.send(
        f"📏 **{ctx.author.display_name}’s Ergebnis:** {cm}cm {random.choice(emojis)}\n"
        f"🏷️ Titel: *{rang}*\n💬 _{kommentar}_"
    )

# Weitere Kommandos wie !ranking, !size, !spritzquote etc. können hier wie gehabt folgen...

# Starte Webserver + Bot
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
