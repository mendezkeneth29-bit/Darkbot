import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import string
import json
import time
import threading
from flask import Flask

TOKEN = os.getenv("TOKEN")
COLOR = 0x000000
DB_FILE = "data.json"

data = {}
tienda = {}
inventario = {}
objetos = {"casa🏠": {"precio": 5000, "stock": 999}}
casas = {}
prestamos = []

# -------------------------
# DATA
# -------------------------
def load_data():
    global data, inventario
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            contenido = json.load(f)
            data = contenido.get("data", {})
            inventario = contenido.get("inventario", {})

def save_data():
    with open(DB_FILE, "w") as f:
        json.dump({
            "data": data,
            "inventario": inventario
        }, f)

# -------------------------
# UTIL
# -------------------------
def generar_codigo():
    return "DB-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))

def init_user(uid):
    if uid not in data:
        data[uid] = {
            "creditos": 0,
            "id_banco": generar_codigo(),
            "veces_presto": 0,
            "veces_debe": 0
        }
    if uid not in inventario:
        inventario[uid] = []

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
# EVENTOS
# -------------------------
@bot.event
async def on_ready():
    print("Bot listo")

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
# CUENTA
# -------------------------
@bot.tree.command(name="cuenta")
async def cuenta(i: discord.Interaction, usuario: discord.Member = None):

    usuario = usuario or i.user
    uid = str(usuario.id)
    init_user(uid)

    embed = discord.Embed(title="Cuenta bancaria 🏦", color=COLOR)
    embed.description = (
        f"{usuario.mention}\n\n"
        f"💰 Créditos: {data[uid]['creditos']}\n"
        f"🆔 ID: {data[uid]['id_banco']}\n"
        f"📉 Debe: {data[uid]['veces_debe']}\n"
        f"📈 Prestó: {data[uid]['veces_presto']}"
    )

    embed.set_thumbnail(url=usuario.display_avatar.url)
    await i.response.send_message(embed=embed)

# -------------------------
# TRANSACCION
# -------------------------
@bot.tree.command(name="transaccion")
async def transaccion(i: discord.Interaction, cuenta_bancaria: str, cantidad: int):

    uid_sender = str(i.user.id)
    init_user(uid_sender)

    for uid, info in data.items():
        if info["id_banco"] == cuenta_bancaria:

            if data[uid_sender]["creditos"] < cantidad:
                return await i.response.send_message("No tienes dinero", ephemeral=True)

            data[uid_sender]["creditos"] -= cantidad
            data[uid]["creditos"] += cantidad
            save_data()

            await i.response.send_message(f"💸 Transferiste {cantidad} créditos")
            return

    await i.response.send_message("ID no encontrado", ephemeral=True)

# -------------------------
# BONUS
# -------------------------
@bot.tree.command(name="bonus")
@app_commands.checks.has_permissions(administrator=True)
async def bonus(i: discord.Interaction, cuenta_bancaria: str, cantidad: int):

    for uid, info in data.items():
        if info["id_banco"] == cuenta_bancaria:

            data[uid]["creditos"] += cantidad
            save_data()

            await i.response.send_message(f"🎁 Bonus dado correctamente")
            return

    await i.response.send_message("ID no encontrado", ephemeral=True)

# -------------------------
# TIENDA ROLES
# -------------------------
@bot.tree.command(name="tienda-config")
async def tienda_config(i: discord.Interaction, rol: discord.Role, precio: int):
    tienda[rol.id] = precio
    await i.response.send_message("Rol agregado")

@bot.tree.command(name="tienda")
async def tienda_cmd(i: discord.Interaction):

    embed = discord.Embed(title="Tienda 🛒", color=COLOR)

    for rid, precio in tienda.items():
        rol = i.guild.get_role(rid)
        embed.add_field(name=rol.name, value=f"${precio}", inline=False)

    await i.response.send_message(embed=embed)

# -------------------------
# INVENTARIO
# -------------------------
@bot.tree.command(name="inventario")
async def inventario_cmd(i: discord.Interaction):

    uid = str(i.user.id)
    init_user(uid)

    items = inventario[uid]

    embed = discord.Embed(title="Inventario 🎒", color=COLOR)
    embed.description = "\n".join(items) if items else "Vacío"

    await i.response.send_message(embed=embed)

# -------------------------
# CASAS
# -------------------------
class CasaView(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    def es_dueno(self, i):
        return i.user.id == self.owner_id

    @discord.ui.button(label="🔒 Bloquear", style=discord.ButtonStyle.red)
    async def bloquear(self, i: discord.Interaction, b: discord.ui.Button):
        if not self.es_dueno(i):
            return await i.response.send_message("No es tu casa", ephemeral=True)

        await i.channel.set_permissions(i.guild.default_role, view_channel=False)
        await i.response.send_message("Casa bloqueada", ephemeral=True)

    @discord.ui.button(label="🔓 Desbloquear", style=discord.ButtonStyle.green)
    async def desbloquear(self, i: discord.Interaction, b: discord.ui.Button):
        if not self.es_dueno(i):
            return await i.response.send_message("No es tu casa", ephemeral=True)

        await i.channel.set_permissions(i.guild.default_role, view_channel=True)
        await i.response.send_message("Casa desbloqueada", ephemeral=True)

# -------------------------
# COMPRAR CASA
# -------------------------
@bot.tree.command(name="tienda-objetos")
async def tienda_objetos(i: discord.Interaction):

    uid = str(i.user.id)
    init_user(uid)

    precio = objetos["casa🏠"]["precio"]

    if data[uid]["creditos"] < precio:
        return await i.response.send_message("No tienes dinero", ephemeral=True)

    data[uid]["creditos"] -= precio
    inventario[uid].append("casa🏠")

    categoria = discord.utils.get(i.guild.categories, name="CASAS")
    if not categoria:
        categoria = await i.guild.create_category("CASAS")

    numero = len(casas) + 1
    canal = await i.guild.create_text_channel(f"casa-{numero}", category=categoria)

    casas[uid] = canal.id
    save_data()

    embed = discord.Embed(title="Controls", color=COLOR)
    embed.set_thumbnail(url=i.user.display_avatar.url)

    await canal.send(embed=embed, view=CasaView(i.user.id))
    await i.response.send_message(f"🏠 Casa #{numero} comprada")

# -------------------------
# CONTROLS
# -------------------------
@bot.tree.command(name="controls")
async def controls(i: discord.Interaction):
    embed = discord.Embed(title="Controls", color=COLOR)
    await i.response.send_message(embed=embed, view=CasaView(i.user.id))

# -------------------------
# PRESTAMOS
# -------------------------
class PrestamoView(discord.ui.View):
    def __init__(self, prestamista, receptor, cantidad):
        super().__init__(timeout=60)
        self.p = prestamista
        self.r = receptor
        self.c = cantidad

    @discord.ui.button(label="Aceptar", style=discord.ButtonStyle.green)
    async def aceptar(self, i: discord.Interaction, b):
        if i.user != self.r:
            return

        data[str(self.p.id)]["creditos"] -= self.c
        data[str(self.r.id)]["creditos"] += self.c
        save_data()

        await i.response.send_message("Aceptado")

@bot.tree.command(name="prestamos")
async def prestamos_cmd(i: discord.Interaction, cuenta_bancaria: str, cantidad: int):

    for uid, info in data.items():
        if info["id_banco"] == cuenta_bancaria:
            receptor = i.guild.get_member(int(uid))

            embed = discord.Embed(title="Préstamo 💰", color=COLOR)
            embed.set_thumbnail(url=receptor.display_avatar.url)

            await i.response.send_message(
                embed=embed,
                view=PrestamoView(i.user, receptor, cantidad)
            )
            return

# -------------------------
# WEB (RENDER FIX)
# -------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot activo"

def run_web():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_web).start()

# -------------------------
# RUN
# -------------------------
load_data()
bot.run(TOKEN)
