import threading
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "Bot activo"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()
import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import string
import json
import asyncio
import time

TOKEN = os.getenv("TOKEN")
COLOR = 0x000000
DB_FILE = "data.json"

data = {}
prestamos = []
tienda = {}

# -------------------------
# 💾 DATA
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
"inventario": {}
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
# EVENTOS
# -------------------------
@bot.event
async def on_ready():
    print("Bot listo")
    bot.loop.create_task(revisar_prestamos())

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = str(message.author.id)
    init_user(uid)

    data[uid]["creditos"] += 1
    save_data()

    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    if member.bot:
        return
    init_user(str(member.id))
    save_data()

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

    usuario_objetivo = None
    uid_receiver = None

    for uid, info in data.items():
        if info["id_banco"] == cuenta_bancaria:
            uid_receiver = uid
            usuario_objetivo = i.guild.get_member(int(uid))
            break

    if not usuario_objetivo:
        return await i.response.send_message("ID bancario no encontrado", ephemeral=True)

    if data[uid_sender]["creditos"] < cantidad:
        return await i.response.send_message("No tienes suficiente dinero", ephemeral=True)

    data[uid_sender]["creditos"] -= cantidad
    data[uid_receiver]["creditos"] += cantidad
    save_data()

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
                f"ID bancario: {data[uid]['id_banco']}\n"
                "----------------------------------------------\n"
                "> - usa el dinero con inteligencia\n"
                "> - no pidas más credito a los admin\n"
                f"> - ahora {usuario.mention} tiene {data[uid]['creditos']} creditos\n"
                "----------------------------------------------\n"
                "creditado por: DarkyBot"
            )

            embed.set_thumbnail(url=usuario.display_avatar.url)
            return await i.response.send_message(embed=embed)

    await i.response.send_message("ID no encontrado", ephemeral=True)

# -------------------------
# OBJETOS
# -------------------------
objetos = {
    "espada⚔️": {"precio": 100, "stock": 10},
    "escudo🛡️": {"precio": 80, "stock": 10},
    "pocion🧪": {"precio": 30, "stock": 50},
    "libro📚": {"precio": 25, "stock": 30},
    "telefono📱": {"precio": 200, "stock": 5},
    "laptop💻": {"precio": 500, "stock": 3},
    "carro🚗": {"precio": 2000, "stock": 2},
    "casa🏠": {"precio": 5000, "stock": 1},
    "anillo💍": {"precio": 150, "stock": 10},
    "reloj⌚": {"precio": 120, "stock": 10},
    "gafas🕶️": {"precio": 60, "stock": 15},
    "mochila🎒": {"precio": 70, "stock": 15},
    "camara📷": {"precio": 180, "stock": 8},
    "microfono🎤": {"precio": 140, "stock": 8},
    "consola🎮": {"precio": 400, "stock": 5},
    "audifonos🎧": {"precio": 90, "stock": 10},
    "zapatillas👟": {"precio": 110, "stock": 12},
    "chaqueta🧥": {"precio": 130, "stock": 10},
    "sombrero🎩": {"precio": 75, "stock": 10},
    "maletin💼": {"precio": 160, "stock": 6}
}

# -------------------------
# SELECTOR
# -------------------------
class ObjetosSelect(discord.ui.Select):
    def __init__(self):

        opciones = [
            discord.SelectOption(
                label=nombre,
                description=f"${item['precio']} | stock {item['stock']}",
                value=nombre
            )
            for nombre, item in objetos.items()
        ]

        super().__init__(placeholder="Selecciona un objeto", options=opciones)

    async def callback(self, i: discord.Interaction):

        uid = str(i.user.id)
        init_user(uid)

        nombre = self.values[0]
        item = objetos[nombre]

        if data[uid]["creditos"] < item["precio"]:
            return await i.response.send_message("No tienes dinero", ephemeral=True)

        if item["stock"] <= 0:
            return await i.response.send_message("Sin stock", ephemeral=True)

        # COBRAR
        data[uid]["creditos"] -= item["precio"]
        item["stock"] -= 1

        # INVENTARIO
        inv = data[uid]["inventario"]
        inv[nombre] = inv.get(nombre, 0) + 1

        save_data()

        await i.response.send_message(f"Compraste {nombre}", ephemeral=True)

# -------------------------
# VIEW
# -------------------------
class ObjetosView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ObjetosSelect())

# -------------------------
# COMANDO TIENDA OBJETOS
# -------------------------
@bot.tree.command(name="tienda-objetos")
async def tienda_objetos(i: discord.Interaction):

    embed = discord.Embed(
        title="Tienda de Objetos 🛒",
        color=COLOR
    )

    for idx, (nombre, item) in enumerate(objetos.items(), 1):
        embed.add_field(
            name=f"{idx}. {nombre}",
            value=f"Precio: {item['precio']} | Stock: {item['stock']}",
            inline=False
        )

    await i.response.send_message(embed=embed, view=ObjetosView())

# -------------------------
# INVENTARIO
# -------------------------
@bot.tree.command(name="inventario")
async def inventario(i: discord.Interaction, usuario: discord.Member = None):

    usuario = usuario or i.user
    uid = str(usuario.id)
    init_user(uid)

    inv = data[uid].get("inventario", {})

    embed = discord.Embed(
        title=f"Inventario de {usuario.mention} 🎒",
        color=COLOR
    )

    if not inv:
        embed.description = "No tienes objetos"
    else:
        texto = ""
        for obj, cantidad in inv.items():
            texto += f"{obj} x{cantidad}\n"

        embed.description = texto

    embed.set_thumbnail(url=usuario.display_avatar.url)

    await i.response.send_message(embed=embed)

# -------------------------
# SISTEMA AUTO COBRO
# -------------------------
async def revisar_prestamos():
    while True:
        ahora = time.time()

        for deuda in prestamos[:]:
            if ahora >= deuda["tiempo"]:
                uid_r = deuda["receptor"]
                uid_p = deuda["prestamista"]
                cantidad = deuda["cantidad"]

                if data[uid_r]["creditos"] >= cantidad:
                    data[uid_r]["creditos"] -= cantidad
                    data[uid_p]["creditos"] += cantidad

                prestamos.remove(deuda)

        await asyncio.sleep(60)

# -------------------------
# PRESTAMOS
# -------------------------
class PrestamoView(discord.ui.View):
    def __init__(self, prestamista, receptor, cantidad, dias):
        super().__init__(timeout=60)
        self.p = prestamista
        self.r = receptor
        self.c = cantidad
        self.d = dias

    async def disable(self, interaction):
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

    # ✅ ACEPTAR
    @discord.ui.button(label="Aceptar", style=discord.ButtonStyle.green)
    async def aceptar(self, i: discord.Interaction, button: discord.ui.Button):

        if i.user != self.r:
            return await i.response.send_message("No es tu préstamo", ephemeral=True)

        uid_p = str(self.p.id)
        uid_r = str(self.r.id)

        if data[uid_p]["creditos"] < self.c:
            return await i.response.send_message("El prestamista no tiene dinero", ephemeral=True)

        # transferir dinero
        data[uid_p]["creditos"] -= self.c
        data[uid_r]["creditos"] += self.c

        # contadores
        data[uid_p]["veces_presto"] += 1
        data[uid_r]["veces_debe"] += 1

        # guardar préstamo
        prestamos.append({
            "prestamista": uid_p,
            "receptor": uid_r,
            "cantidad": self.c,
            "tiempo": time.time() + (self.d * 86400)
        })

        save_data()

        await i.response.send_message("Préstamo aceptado", ephemeral=True)
        await self.disable(i)

    # ❌ RECHAZAR
    @discord.ui.button(label="Rechazar", style=discord.ButtonStyle.red)
    async def rechazar(self, i: discord.Interaction, button: discord.ui.Button):

        if i.user != self.r:
            return await i.response.send_message("No es tu préstamo", ephemeral=True)

        await i.response.send_message("Préstamo rechazado", ephemeral=True)
        await self.disable(i)


@bot.tree.command(name="prestamos")
async def prestamos_cmd(i: discord.Interaction, cuenta_bancaria: str, cantidad: int, dias: int):

    prestamista = i.user
    uid_p = str(prestamista.id)
    init_user(uid_p)

    receptor = None
    uid_r = None

    # buscar usuario por ID bancario
    for uid, info in data.items():
        if info["id_banco"] == cuenta_bancaria:
            receptor = i.guild.get_member(int(uid))
            uid_r = uid
            break

    if not receptor:
        return await i.response.send_message("ID no encontrado", ephemeral=True)

    if uid_p == uid_r:
        return await i.response.send_message("No puedes prestarte a ti mismo", ephemeral=True)

    if cantidad <= 0:
        return await i.response.send_message("Cantidad inválida", ephemeral=True)

    if data[uid_p]["creditos"] < cantidad:
        return await i.response.send_message("No tienes suficiente dinero para prestar", ephemeral=True)

    embed = discord.Embed(
        title=f"{prestamista.mention} proporciono un prestamo a {receptor.mention} 💰",
        color=COLOR
    )

    embed.description = (
        f"cantidad de creditos: {cantidad}\n"
        f"ID bancario: {data[uid_r]['id_banco']}\n"
        f"dia de devolucion: {dias}\n"
        "------------------------------------------\n"
        "> - el dinero debes ser entregado el dia seleccionado\n"
        "> - si no devuelve el dinero, se le restaran la cantidad del dinero automaticamente\n"
        "> - al aceptar debe seguir las politicas bancarias\n"
        "------------------------------------------\n"
        "creditado por: DarkyBank"
    )

    embed.set_thumbnail(url=receptor.display_avatar.url)

    await i.response.send_message(
        embed=embed,
        view=PrestamoView(prestamista, receptor, cantidad, dias)
    )

# -------------------------
# RUN
# -------------------------
keep_alive()
load_data()
bot.run(TOKEN)
