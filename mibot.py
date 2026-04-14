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

    embed = discord.Embed(
        title=f"Cuenta bancaria de {usuario.mention} 🏦",
        color=COLOR
    )

    embed.description = (
        f"creditos: {data[uid]['creditos']}\n"
        f"ID bancario: {data[uid]['id_banco']}\n"
        "------------------------------\n"
        f"debe: {data[uid]['veces_debe']}\n"
        f"presto: {data[uid]['veces_presto']}\n"
        f"prestamos totales: {data[uid]['veces_presto']}\n"
        "------------------------------\n"
        "informacion garantizada por: DarkyBank"
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

            usuario = i.guild.get_member(int(uid))

            if data[uid_sender]["creditos"] < cantidad:
                return await i.response.send_message("No tienes dinero", ephemeral=True)

            data[uid_sender]["creditos"] -= cantidad
            data[uid]["creditos"] += cantidad
            save_data()

            embed = discord.Embed(
                title=f"Transaccion a {usuario.mention} 💸",
                color=COLOR
            )

            embed.description = (
                f"{cantidad} enviados a {usuario.mention}\n"
                f"ID bancario {info['id_banco']}\n"
                "------------------------------\n"
                f"> - ahora {usuario.mention} tiene {data[uid]['creditos']} creditos\n"
                "> - usalos con inteligencia\n"
                "------------------------------\n"
                f"enviado por: {i.user.mention}, creditado por: DarkyBank"
            )

            embed.set_thumbnail(url=usuario.display_avatar.url)

            return await i.response.send_message(embed=embed)

    await i.response.send_message("ID no encontrado", ephemeral=True)
# -------------------------
# BONUS
# -------------------------
@bot.tree.command(name="bonus")
@app_commands.checks.has_permissions(administrator=True)
async def bonus(i: discord.Interaction, cuenta_bancaria: str, cantidad: int):

    for uid, info in data.items():
        if info["id_banco"] == cuenta_bancaria:

            usuario = i.guild.get_member(int(uid))
            data[uid]["creditos"] += cantidad
            save_data()

            embed = discord.Embed(title="Bonus ! 🎁", color=COLOR)
            embed.description = (
                f"{i.user.mention} ha dado un bonus a {usuario.mention}\n"
                f"ID bancario: {info['id_banco']}\n"
                "------------------------------\n"
                f"> - ahora {usuario.mention} tiene {data[uid]['creditos']} creditos\n"
                "------------------------------\n"
                "creditado por: DarkyBot"
            )

            embed.set_thumbnail(url=usuario.display_avatar.url)

            return await i.response.send_message(embed=embed)

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
# OBJETOS (TIENDA REAL)
# -------------------------
objetos = {
    "casa🏠": {"precio": 5000, "stock": 999},
    "Ipad📱": {"precio": 800, "stock": 999},
    "laptop💻": {"precio": 2000, "stock": 999},
    "carro🚗": {"precio": 7000, "stock": 999},
    "reloj⌚": {"precio": 400, "stock": 999},
    "tv📺": {"precio": 1200, "stock": 999},
    "moto🏍️": {"precio": 3500, "stock": 999},
    "joya💎": {"precio": 10000, "stock": 999},
    "audifonos🎧": {"precio": 300, "stock": 999},
    "tablet📲": {"precio": 1500, "stock": 999}
    "Dildo🥴": {"precio": 600, "stock": 999}
    "audifonos🎧": {"precio": 167, "stock": 999}
    "avion✈️": {"precio": 10000, "stock": 999}
    "Jet privado💸": {"precio":500000, "stock": 999}
}

# -------------------------
# INVENTARIO INIT
# -------------------------
def init_user(uid):
    if uid not in data:
        data[uid] = {
            "creditos": 0,
            "id_banco": generar_codigo(),
            "veces_presto": 0,
            "veces_debe": 0,
            "inventario": {}
        }

# -------------------------
# VER TIENDA
# -------------------------
@bot.tree.command(name="tienda-objetos")
async def tienda_objetos(i: discord.Interaction):

    texto = ""

    for nombre, info in objetos.items():
        texto += f"{nombre} - 💰 {info['precio']} | stock: {info['stock']}\n"

    embed = discord.Embed(
        title="Tienda de objetos 🛒",
        description=texto,
        color=COLOR
    )

    await i.response.send_message(embed=embed)

# -------------------------
# COMPRAR OBJETO
# -------------------------
@bot.tree.command(name="comprar")
async def comprar(i: discord.Interaction, objeto: str):

    uid = str(i.user.id)
    init_user(uid)

    if objeto not in objetos:
        return await i.response.send_message("Objeto no existe", ephemeral=True)

    item = objetos[objeto]

    if data[uid]["creditos"] < item["precio"]:
        return await i.response.send_message("No tienes dinero", ephemeral=True)

    if item["stock"] <= 0:
        return await i.response.send_message("Sin stock", ephemeral=True)

    # quitar dinero
    data[uid]["creditos"] -= item["precio"]

    # bajar stock
    item["stock"] -= 1

    # agregar al inventario
    inv = data[uid]["inventario"]
    inv[objeto] = inv.get(objeto, 0) + 1

    save_data()

    await i.response.send_message(f"Compraste {objeto} 🛒")

# -------------------------
# INVENTARIO
# -------------------------
@bot.tree.command(name="inventario")
async def inventario(i: discord.Interaction, usuario: discord.Member = None):

    usuario = usuario or i.user
    uid = str(usuario.id)
    init_user(uid)

    inv = data[uid]["inventario"]

    if not inv:
        return await i.response.send_message("Inventario vacío", ephemeral=True)

    texto = ""

    for obj, cant in inv.items():
        texto += f"{obj} x{cant}\n"

    embed = discord.Embed(
        title=f"Inventario de {usuario.name} 🎒",
        description=texto,
        color=COLOR
    )

    embed.set_thumbnail(url=usuario.display_avatar.url)

    await i.response.send_message(embed=embed)
# -------------------------
# CONTROLS
# -------------------------
@bot.tree.command(name="controls")
async def controls(i: discord.Interaction):
    embed = discord.Embed(title="Controles de hogar🏡", color=COLOR)
    embed.description = (
                f"Bienvenido/a a tu nuevo hogar}\n"
                f"ID bancario: {info['id_banco']}\n"
                "------------------------------\n"
                f"Aqui puedes hacer cualquier cosa sin ser advertido\n"
                f"toda queda bajo tu responsabilidad\n"
                "------------------------------\n"
                "creditado por: DarkyHouses"
            )
    await i.response.send_message(embed=embed, view=CasaView(i.user.id))

# -------------------------
# PRESTAMOS
# -------------------------
@bot.tree.command(name="prestamos")
async def prestamos_cmd(i: discord.Interaction, cuenta_bancaria: str, cantidad: int, dias: int):

    prestamista = i.user
    uid_p = str(prestamista.id)
    init_user(uid_p)

    for uid, info in data.items():
        if info["id_banco"] == cuenta_bancaria:

            receptor = i.guild.get_member(int(uid))

            embed = discord.Embed(
                title=f"{prestamista.mention} proporciono un prestamo a {receptor.mention} 💰",
                color=COLOR
            )

            embed.description = (
                f"cantidad de creditos: {cantidad}\n"
                f"ID bancario: {info['id_banco']}\n"
                f"dia de devolucion: {dias}\n"
                "------------------------------------------\n"
                "> - el dinero debes ser entregado el dia seleccionado\n"
                "> - si no devuelve el dinero, se le restaran automaticamente\n"
                "> - al aceptar debe seguir las politicas bancarias\n"
                "------------------------------------------\n"
                "creditado por: DarkyBank"
            )

            embed.set_thumbnail(url=receptor.display_avatar.url)

            return await i.response.send_message(
                embed=embed,
                view=PrestamoView(prestamista, receptor, cantidad, dias)
            )

    await i.response.send_message("ID no encontrado", ephemeral=True)

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
