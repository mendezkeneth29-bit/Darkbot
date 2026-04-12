import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import string
import json

# --- CONFIG ---
TOKEN = os.getenv("TOKEN")
COLOR = 0x000000
DB_FILE = "data.json"

data = {}

# -------------------------
# 💾 GUARDADO
# -------------------------
def load_data():
    global data
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            data = json.load(f)

def save_data():
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# -------------------------
# 🧠 UTILIDADES
# -------------------------
def generar_codigo():
    return "DB-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))

def init_user(uid):
    if uid not in data:
        data[uid] = {
            "creditos": 0,
            "id_banco": generar_codigo()
        }

# -------------------------
# BOT
# -------------------------
class DarkyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        await self.tree.sync()

bot = DarkyBot()

# -------------------------
# 💬 DINERO POR MENSAJE
# -------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = str(message.author.id)
    init_user(uid)

    data[uid]["creditos"] += 1
    save_data()

    await bot.process_commands(message)

# -------------------------
# 👤 CREAR CUENTAS AL ENTRAR
# -------------------------
@bot.event
async def on_member_join(member):
    if member.bot:
        return

    uid = str(member.id)
    init_user(uid)
    save_data()

# -------------------------
# 🏦 COMANDO CUENTA
# -------------------------
@bot.tree.command(name="cuenta")
async def cuenta(i: discord.Interaction, usuario: discord.Member = None):

    usuario = usuario or i.user
    uid = str(usuario.id)

    init_user(uid)

    embed = discord.Embed(
        title=f"Cuenta bancaria de {usuario.mention} 🏦",
        color=COLOR
    )

    embed.description = (
        f"creditos: {data[uid]['creditos']}\n"
        f"ID bancario: {data[uid]['id_banco']}\n"
        "------------------------------\n"
        "debe: 0\n"
        "presto: 0\n"
        "prestamos totales: 0\n"
        "------------------------------\n"
        "informacion garantizada por: DarkyBank"
    )

    embed.set_thumbnail(url=usuario.display_avatar.url)

    await i.response.send_message(embed=embed)

@bot.tree.command(name="transaccion")
async def transaccion(i: discord.Interaction, cuenta_bancaria: str, cantidad: int):

    uid_sender = str(i.user.id)
    init_user(uid_sender)

    # buscar usuario por ID bancario
    usuario_objetivo = None
    uid_receiver = None

    for uid, info in data.items():
        if info["id_banco"] == cuenta_bancaria:
            uid_receiver = uid
            usuario_objetivo = i.guild.get_member(int(uid))
            break

    if not usuario_objetivo:
        return await i.response.send_message("ID bancario no encontrado", ephemeral=True)

    if uid_sender == uid_receiver:
        return await i.response.send_message("No puedes transferirte a ti mismo", ephemeral=True)

    # validar dinero
    if cantidad <= 0:
        return await i.response.send_message("Cantidad inválida", ephemeral=True)

    if data[uid_sender]["creditos"] < cantidad:
        return await i.response.send_message("No tienes suficiente dinero", ephemeral=True)

    # transferir
    data[uid_sender]["creditos"] -= cantidad
    data[uid_receiver]["creditos"] += cantidad

    save_data()

    # EMBED EXACTO
    embed = discord.Embed(
        title=f"Transaccion a {usuario_objetivo.mention} 💸",
        color=COLOR
    )

    embed.description = (
        f"{cantidad} enviados a {usuario_objetivo.mention}\n"
        f"ID bancario {data[uid_receiver]['id_banco']}\n"
        "--------------------------------------------------\n"
        f"> - ahora {usuario_objetivo.mention} tiene {data[uid_receiver]['creditos']} creditos\n"
        "> - usalos con inteligencia\n"
        "------------------------------\n"
        f"enviado por: {i.user.mention}, creditado por: DarkyBank"
    )

    embed.set_thumbnail(url=usuario_objetivo.display_avatar.url)

    await i.response.send_message(embed=embed)

@bot.tree.command(name="bonus")
@app_commands.checks.has_permissions(administrator=True)
async def bonus(i: discord.Interaction, cuenta_bancaria: str, cantidad: int):

    # buscar usuario por ID bancario
    usuario_objetivo = None
    uid_receiver = None

    for uid, info in data.items():
        if info["id_banco"] == cuenta_bancaria:
            uid_receiver = uid
            usuario_objetivo = i.guild.get_member(int(uid))
            break

    if not usuario_objetivo:
        return await i.response.send_message("ID bancario no encontrado", ephemeral=True)

    if cantidad <= 0:
        return await i.response.send_message("Cantidad inválida", ephemeral=True)

    # dar dinero
    data[uid_receiver]["creditos"] += cantidad

    save_data()

    # EMBED
    embed = discord.Embed(
        title="Bonus ! 🎁",
        color=COLOR
    )

    embed.description = (
        f"{i.user.mention} ha dado un bonus a {usuario_objetivo.mention}\n"
        f"ID bancario: {data[uid_receiver]['id_banco']}\n"
        "----------------------------------------------\n"
        "> - usa el dinero con inteligencia\n"
        "> - no pidas más credito a los admin\n"
        f"> - ahora {usuario_objetivo.mention} tiene {data[uid_receiver]['creditos']} creditos\n"
        "----------------------------------------------\n"
        "creditado por: DarkyBot"
    )

    embed.set_thumbnail(url=usuario_objetivo.display_avatar.url)

    await i.response.send_message(embed=embed)

# -------------------------
# RUN
# -------------------------
load_data()
bot.run(TOKEN)
