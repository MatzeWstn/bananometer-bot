from flask import Flask
from threading import Thread
import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Bot Setup
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)
tree = bot.tree  # Für Slash-Commands

data_file = "banana_data.json"

if not os.path.exists(data_file):
    with open(data_file, "w") as f:
        json.dump({}, f)

# ==========  Rangliste ========== #
    "MiniPimmel 🍒", "Gurkengurgler 🥒", "Kleinpimmliger Schnellspritzer 💦",
    "PimmelPirat 🏴‍☠️", "Benanenbaron 🍌", "Schlaffi des Monats 😔",
    "Wichsender-Wicht 🌱", "Vorhaut-Virtuose 🔍",
    "Dödel-Desperado 🚀", "Schwanzschwenker 😎"


# ========== BOT READY ========== #
@bot.event
async def on_ready():
    print(f"✅ Bananometer ist online als {bot.user}")
    try:
        synced = await tree.sync()
        print(f"📡 Slash-Commands synchronisiert: {len(synced)}")
    except Exception as e:
        print(f"❌ Fehler beim Slash-Sync: {e}")
    update_king_role.start()

# ========== AUTO ROLE ========== #
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
    guild = bot.guilds[0]
    role = discord.utils.get(guild.roles, name="🍌 King Banana")
    if not role:
        return

    for member in guild.members:
        if role in member.roles and str(member.id) != top_user_id:
            await member.remove_roles(role)
        elif str(member.id) == top_user_id and role not in member.roles:
            await member.add_roles(role)

# ========== HELFER ========== #
def messung(ctx_author):
    with open(data_file, "r") as f:
        data = json.load(f)

    user_id = str(ctx_author.id)
    now = datetime.utcnow()
    last_used_str = data.get(user_id, {}).get("last_used")
    if last_used_str:
        last_used = datetime.strptime(last_used_str, "%Y-%m-%d %H:%M:%S")
        if now - last_used < timedelta(hours=3):
            remaining = timedelta(hours=3) - (now - last_used)
            mins = int(remaining.total_seconds() // 60)
            return f"⏳ Du musst noch {mins} Minuten warten, bevor du wieder messen kannst!"

    cm = round(random.uniform(0.5, 25.0), 1)
    rang = random.choice(ränge)
    emojis = ["🍌", "💦", "📏", "😳", "☠️", "🤏", "🔬"]
    kommentar = (
        "Der ist klein UND dünn!! 🔬" if cm < 3 else
        "Klein, aber stinkt wie 'n großer! 🤏" if cm < 7 else
        "Nice Schwons Bro 🍌" if cm < 15 else
        "Du kannst mit 'nem harten gegen die Wand rennen und brichst dir trotzdem die Nase! 🍌" if cm < 20 else
        "Ohjoo Bro, chill mo dei Bux 💦" if cm < 25 else
        "Unreal im Bananen-Game 🚀"
    )

    old_entry = data.get(user_id, {})
    count = old_entry.get("count", 0) + 1
    history = old_entry.get("history", [])
    history.append(cm)

    data[user_id] = {
        "name": ctx_author.display_name,
        "length": cm,
        "rank": rang,
        "count": count,
        "last_used": now.strftime("%Y-%m-%d %H:%M:%S"),
        "history": history
    }

    with open(data_file, "w") as f:
        json.dump(data, f, indent=4)

    return f"📏 **{ctx_author.display_name}’s Bananometer-Ergebnis:** {cm}cm {random.choice(emojis)}\n🏷️ Titel: *{rang}*\n💬 _{kommentar}_"

# ========== BEFEHLE ========== #
@bot.command(name="banana")
async def banana(ctx):
    antwort = messung(ctx.author)
    await ctx.send(antwort)

@tree.command(name="schwanzgröße", description="Miss deine 🍌 in Zentimetern")
async def slash_banana(interaction: discord.Interaction):
    await interaction.response.send_message(messung(interaction.user))

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
    if str(member.id) not in data:
        await ctx.send(f"{member.display_name} hat sich noch nicht messen lassen! 📏")
        return
    eintrag = data[str(member.id)]
    verlauf = eintrag.get("history", [])
    verlaufs_text = "\n".join([f"{i+1}. {val}cm" for i, val in enumerate(verlauf[-5:])])
    await ctx.send(
        f"📦 **{member.display_name}’s letzter Bananometer-Wert:**\n"
        f"📏 {eintrag['length']}cm\n"
        f"🏷️ Titel: *{eintrag['rank']}*\n"
        f"📈 Verlauf:\n{verlaufs_text}"
    )

@bot.command(name="spritzquote")
async def spritzquote (ctx, member: discord.Member = None):
    member = member or ctx.author
    with open(data_file, "r") as f:
        data = json.load(f)
    count = data.get(str(member.id), {}).get("count", 0)
    await ctx.send(f"💦 **{member.display_name}** hat das Geodreieck bereits **{count}x** benutzt!")

@bot.command(name="reset")
@commands.has_permissions(administrator=True)
async def reset(ctx, member: discord.Member):
    with open(data_file, "r") as f:
        data = json.load(f)
    if str(member.id) in data:
        del data[str(member.id)]
        with open(data_file, "w") as f:
            json.dump(data, f, indent=4)
        await ctx.send(f"🔄 Daten von {member.display_name} wurden gelöscht!")
    else:
        await ctx.send(f"{member.display_name} hat keine gespeicherten Daten.")

@reset.error
async def reset_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 Nur Admins dürfen User zurücksetzen!")

@bot.command(name="average")
async def average(ctx):
    with open(data_file, "r") as f:
        data = json.load(f)
    werte = [entry["length"] for entry in data.values()]
    if not werte:
        await ctx.send("Noch keine 🍌-Daten vorhanden!")
        return
    durchschnitt = round(sum(werte) / len(werte), 2)
    await ctx.send(f"📊 Der aktuelle Durchschnitt liegt bei **{durchschnitt}cm**!")

@bot.command(name="vergleich")
async def vergleichen(ctx, user1: discord.Member, user2: discord.Member):
    with open(data_file, "r") as f:
        data = json.load(f)
    id1, id2 = str(user1.id), str(user2.id)
    if id1 not in data or id2 not in data:
        await ctx.send("🔍 Einer der beiden hat sich noch nicht messen lassen!")
        return
    d1, d2 = data[id1], data[id2]
    msg = f"**🍌 Vergleich:**\n{user1.display_name}: {d1['length']}cm\n{user2.display_name}: {d2['length']}cm\n"
    msg += f"➡️ **{user1.display_name}** hat die 🍌 vorne!" if d1["length"] > d2["length"] else (
        f"➡️ **{user2.display_name}** hat die 🍌 vorne!" if d2["length"] > d1["length"] else "⚖️ Unentschieden!")
    await ctx.send(msg)

# ========== WEB SERVER ========== #
app = Flask('')

@app.route('/')
def home():
    return "Ich bin wach!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()
    
# ========== / Commands ========== #
@bot.tree.command(name="schwanzgröße", description="Miss deine 🍌")
async def slash_banana(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await banana(ctx)

@bot.tree.command(name="ranking", description="Zeigt die Top 10 🍌")
async def slash_ranking(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await ranking(ctx)

@bot.tree.command(name="größe", description="Zeigt den letzten Wert von dir oder einem anderen")
@app_commands.describe(member="Optional: Member zum Prüfen")
async def slash_size(interaction: discord.Interaction, member: discord.Member = None):
    ctx = await bot.get_context(interaction)
    ctx.author = interaction.user
    await size(ctx, member)

@bot.tree.command(name="spritzer", description="Zeigt wie oft jemand gemessen hat")
@app_commands.describe(member="Optional: Member zum Prüfen")
async def slash_spritzquote(interaction: discord.Interaction, member: discord.Member = None):
    ctx = await bot.get_context(interaction)
    ctx.author = interaction.user
    await spritzquote(ctx, member)

@bot.tree.command(name="im schnitt", description="Zeigt den 🍌 Durchschnitt")
async def slash_average(interaction: discord.Interaction):
    ctx = await bot.get_context(interaction)
    await average(ctx)

@bot.tree.command(name="vergleich", description="Vergleicht zwei Schwänze")
@app_commands.describe(user1="Erster User", user2="Zweiter User")
async def slash_vergleich(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
    ctx = await bot.get_context(interaction)
    await vergleichen(ctx, user1, user2)

# === KEEP ALIVE ===
app = Flask('')
@app.route('/')
def home():
    return "Ich bin wach!"
def run():
    app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# ========== START ========== #
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
