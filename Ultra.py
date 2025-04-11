bot = commands.Bot(command_prefix="!",intents=intents)

from flask import Flask
from threading import Thread
import discord
from discord.ext import commands, tasks
import random
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!", "/"), intents=intents)

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
    try:
        synced = await bot.tree.sync()
        print(f"📡 Slash-Commands synchronisiert: {len(synced)}")
    except Exception as e:
        print(f"❌ Fehler beim Slash-Sync: {e}")

@tasks.loop(minutes=5)
async def update_king_role():
    with open(data_file, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return

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
        kommentar = "Klein, aber stinkt wie 'n großer! 🤏"
    elif cm < 12:
        kommentar = "Nice Schwons Bro 🍌"
    elif cm < 16:
        kommentar = "Du kannst mit 'nem harten gegen die Wand rennen und brichst dir trotzdem die Nase! 🍌"
    elif cm < 20:
        kommentar = "Ohjoo Bro, chill mo dei Bux 💦"
    else:
        kommentar = "Unreal im Bananen-Game 🚀"

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

@bot.command(name="ranking")
async def ranking(ctx):
    with open(data_file, "r") as f:
        data = json.load(f)

    if not data:
        await ctx.send("Noch keine 🍌-Daten vorhanden!")
        return

    sorted_data = sorted(data.values(), key=lambda x: x["length"], reverse=True)

    msg = "**🍌 Bananometer Ranking:**\n"
    for i, entry in enumerate(sorted_data[:10], 1):
        msg += f"**{i}. {entry['name']}** – {entry['length']}cm | *{entry['rank']}*\n"

    await ctx.send(msg)

@bot.command(name="size")
async def size(ctx, member: discord.Member = None):
    member = member or ctx.author
    with open(data_file, "r") as f:
        data = json.load(f)

    user_id = str(member.id)

    if user_id not in data:
        await ctx.send(f"{member.display_name} hat sich noch nicht messen lassen! 📏")
        return

    eintrag = data[user_id]
    verlauf = eintrag.get("history", [])
    verlaufs_text = "\n".join([f"{i+1}. {val}cm" for i, val in enumerate(verlauf[-5:])])
    await ctx.send(
        f"📦 **{member.display_name}’s letzter Bananometer-Wert:**\n"
        f"📏 {eintrag['length']}cm\n"
        f"🏷️ Titel: *{eintrag['rank']}*\n"
        f"📈 Verlauf:\n{verlaufs_text}"
    )

@bot.command(name="spritzquote")
async def spritzquote(ctx, member: discord.Member = None):
    member = member or ctx.author
    with open(data_file, "r") as f:
        data = json.load(f)

    user_id = str(member.id)
    if user_id not in data:
        await ctx.send(f"{member.display_name} hat noch nie gespritzt! 💦")
        return

    count = data[user_id].get("count", 0)
    await ctx.send(f"💦 **{member.display_name}** hat den Bananometer bereits **{count}x** benutzt!")

@bot.command(name="reset")
@commands.has_permissions(administrator=True)
async def reset(ctx, member: discord.Member):
    with open(data_file, "r") as f:
        data = json.load(f)

    user_id = str(member.id)
    if user_id in data:
        del data[user_id]
        with open(data_file, "w") as f:
            json.dump(data, f, indent=4)
        await ctx.send(f"🔄 Daten von {member.display_name} wurden gelöscht!")
    else:
        await ctx.send(f"{member.display_name} hat keine gespeicherten Daten.")

@reset.error
async def reset_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 Nur Admins dürfen User zurücksetzen!")

@bot.command(name="alltime-average")
async def average(ctx):
    with open(data_file, "r") as f:
        data = json.load(f)
    if not data:
        await ctx.send("Noch keine 🍌-Daten vorhanden!")
        return
    werte = [entry["length"] for entry in data.values()]
    durchschnitt = round(sum(werte) / len(werte), 2)
    await ctx.send(f"📊 Der aktuelle Durchschnitt liegt bei **{durchschnitt}cm**!")

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

# Webserver für Render + UptimeRobot
app = Flask('')

@app.route('/')
def home():
    return "Ich bin wach!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Bot starten
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
