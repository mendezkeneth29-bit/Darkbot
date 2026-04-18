import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import string
import json
import time

TOKEN = os.getenv("TOKEN")
COLOR = 0x000000
DB_FILE = "data.json"

data = {}
prestamos = []
habitaciones = {}

# -------------------------
# OBJETOS
# -------------------------
objetos = {
    "Habitacion🛌": {"precio": 5000, "stock": 999},
    "celular📞": {"precio": 800, "stock": 999},
    "computadora🖥️": {"precio": 2000, "stock": 999},
    "automovil🚙": {"precio": 7000, "stock": 999},
    "varita🪄": {"precio": 1500, "stock": 100},
    "avion✈️": {"precio": 20000, "stock": 50},
    "ojos👁️": {"precio": 2500, "stock": 200},
    "café☕": {"precio": 5, "stock": 999}
}

# -------------------------
# DATA
# -------------------------
def load_data():
    global data
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            data.update(json.load(f))

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
            "veces_debe": 0,
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
        "informacion garantizada por: AcademyBank"
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
                f"> - ahora {usuario.mention} tiene {data[uid]['creditos']} Sadicos\n"
                "> - usalos con inteligencia\n"
                "------------------------------\n"
                f"enviado por: {i.user.mention}, creditado por: AcademyBank"
            )

            embed.set_thumbnail(url=usuario.display_avatar.url)

            return await i.response.send_message(embed=embed)

    await i.response.send_message("ID no encontrado", ephemeral=True)

# -------------------------
# OBJETOS
# -------------------------
objetos = {
    "Habitacion🛌": {"precio": 5000, "stock": 999},
    "celular📞": {"precio": 800, "stock": 999},
    "computadora🖥️": {"precio": 2000, "stock": 999},
    "automovil🚙": {"precio": 7000, "stock": 999},
    "varita🪄": {"precio": 1500, "stock": 100},
    "avion✈️": {"precio": 20000, "stock": 50},
    "ojos👁️": {"precio": 2500, "stock": 200},
    "café☕": {"precio": 5, "stock": 999}
}

# -------------------------
# SELECTOR
# -------------------------
class ObjetoSelect(discord.ui.Select):
    def __init__(self):

        opciones = [
            discord.SelectOption(
                label=nombre,
                description=f"💰 {info['precio']} | stock {info['stock']}",
                value=nombre
            )
            for nombre, info in objetos.items()
        ]

        super().__init__(
            placeholder="Selecciona un objeto ",
            options=opciones
        )

    async def callback(self, i: discord.Interaction):

        uid = str(i.user.id)
        init_user(uid)

        objeto = self.values[0]
        item = objetos[objeto]

        if data[uid]["creditos"] < item["precio"]:
            return await i.response.send_message("No tienes dinero", ephemeral=True)

        if item["stock"] <= 0:
            return await i.response.send_message("Sin stock", ephemeral=True)

        # COBRAR
        data[uid]["creditos"] -= item["precio"]

        # STOCK
        item["stock"] -= 1

        # INVENTARIO
        inv = data[uid]["inventario"]
        inv[objeto] = inv.get(objeto, 0) + 1

        # CASA AUTOMÁTICA
        if objeto == "habitacion🛌":
            categoria = discord.utils.get(i.guild.categories, name="⚊⚊⚊⚊        000 .    HABITACIONES")
            if not categoria:
                categoria = await i.guild.create_category("⚊⚊⚊⚊        000 .    HABITACIONES")

            numero = len(casas) + 1

            canal = await i.guild.create_text_channel(
                f"Habitacion-{numero}",
                category=categoria
            )

            casas[uid] = canal.id

            embed = discord.Embed(title="Controls", color=COLOR)
            embed.set_thumbnail(url=i.user.display_avatar.url)

            await canal.send(embed=embed, view=CasaView(i.user.id))

        save_data()

        await i.response.send_message(f"Compraste {objeto} ", ephemeral=True)

# -------------------------
# VIEW
# -------------------------
class ObjetoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ObjetoSelect())

# -------------------------
# COMANDO TIENDA
# -------------------------
@bot.tree.command(name="tienda-objetos")
async def tienda_objetos(i: discord.Interaction):

    embed = discord.Embed(
        title="Tienda 🏚️",
        color=COLOR
    )

    for idx, (nombre, info) in enumerate(objetos.items(), 1):

        embed.add_field(
            name=f"{idx}. {nombre}",
            value=(
                f" Precio: {info['precio']}\n"
                f" Stock: {info['stock']}"
                
            ),
            inline=False
        )

    await i.response.send_message(
        embed=embed,
        view=ObjetoView()
    )

# -------------------------
# INVENTARIO
# -------------------------
@bot.tree.command(name="inventario")
async def inventario_cmd(i: discord.Interaction, usuario: discord.Member = None):

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
        title=f"mochila de {usuario.name} 🎒",
        description=texto,
        color=COLOR
    )

    embed.set_thumbnail(url=usuario.display_avatar.url)

    await i.response.send_message(embed=embed)

# -------------------------
# CASA BOTONES
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
        await i.channel.set_permissions(i.user, view_channel=True)

        await i.response.send_message("Casa bloqueada", ephemeral=True)

    @discord.ui.button(label="🔓 Desbloquear", style=discord.ButtonStyle.green)
    async def desbloquear(self, i: discord.Interaction, b: discord.ui.Button):
        if not self.es_dueno(i):
            return await i.response.send_message("No es tu casa", ephemeral=True)

        await i.channel.set_permissions(i.guild.default_role, view_channel=True)

        await i.response.send_message("Casa desbloqueada", ephemeral=True)
    
    @discord.ui.button(label="⚙️ Comandos", style=discord.ButtonStyle.blurple)
    async def comandos(self, i: discord.Interaction, b):

        if not self.es_dueno(i):
            return await i.response.send_message("No es tu casa", ephemeral=True)

        await i.response.send_message(
            "❤️ /kiss\n🤗 /hug\n😈 comandos +18 incluidos",
            ephemeral=True
        )

# -------------------------
# PRESTAMOS
# -------------------------
class PrestamoView(discord.ui.View):
    def __init__(self, p, r, c, d):
        super().__init__(timeout=60)
        self.p, self.r, self.c, self.d = p, r, c, d

    @discord.ui.button(label="Aceptar", style=discord.ButtonStyle.green)
    async def aceptar(self, i: discord.Interaction, b):

        if i.user != self.r:
            return await i.response.send_message("No es tu préstamo", ephemeral=True)

        uid_p = str(self.p.id)
        uid_r = str(self.r.id)

        if data[uid_p]["creditos"] < self.c:
            return await i.response.send_message("El prestamista no tiene dinero", ephemeral=True)

        data[uid_p]["creditos"] -= self.c
        data[uid_r]["creditos"] += self.c

        data[uid_p]["veces_presto"] += 1
        data[uid_r]["veces_debe"] += 1

        save_data()

        await i.response.send_message("Préstamo aceptado", ephemeral=True)

    @discord.ui.button(label="Rechazar", style=discord.ButtonStyle.red)
    async def rechazar(self, i: discord.Interaction, b):

        if i.user != self.r:
            return await i.response.send_message("No es tu préstamo", ephemeral=True)

        await i.response.send_message("Préstamo rechazado", ephemeral=True)

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
                "creditado por: AcademyBank"
            )

            embed.set_thumbnail(url=receptor.display_avatar.url)

            return await i.response.send_message(
                embed=embed,
                view=PrestamoView(prestamista, receptor, cantidad, dias)
            )

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

            embed = discord.Embed(title="Sadicos ! 👁️", color=COLOR)
            embed.description = (
                f"{i.user.mention} ha dado un Sadicos a {usuario.mention}\n"
                f"ID bancario: {info['id_banco']}\n"
                "----------------------------------------------\n"
                f"> - ahora {usuario.mention} tiene {data[uid]['creditos']} creditos\n"
                "----------------------------------------------\n"
                "creditado por: AcademyBot"
            )

            embed.set_thumbnail(url=usuario.display_avatar.url)

            return await i.response.send_message(embed=embed)

    await i.response.send_message("ID no encontrado", ephemeral=True)

# -------------------------
# CONTROLES CASA
# -------------------------
@bot.tree.command(name="controls")
async def controls(i: discord.Interaction):

    embed = discord.Embed(title="Controls", color=COLOR)
    embed.description = (
        "🔒 Bloquear casa\n"
        "🔓 Desbloquear casa\n"
        "⚙️ Comandos interactivos\n"
    )

    embed.set_thumbnail(url=i.user.display_avatar.url)

    await i.response.send_message(embed=embed, view=CasaView(i.user.id))

# -------------------------
# FIESTA_EVENTO
# -------------------------
@bot.tree.command(name="fiesta-invite")
async def fiesta_invite(i: discord.Interaction, hora: str):

    usuario = i.user
    uid = str(usuario.id)
    init_user(uid)

    # verificar si tiene casa
    if uid not in casas:
        return await i.response.send_message("No tienes casa", ephemeral=True)

    canal_id = casas[uid]
    canal = i.guild.get_channel(canal_id)

    if not canal:
        return await i.response.send_message("Tu casa no existe", ephemeral=True)

    embed = discord.Embed(
        title=f"{usuario.mention} invita a todos en la casa {canal.mention} a las {hora} 🪩",
        color=COLOR
    )

    embed.description = (
        f"la fiesta empezara a las: {hora}\n"
        f"en la habitacion: {canal.mention}\n"
        "--------------------------------\n"
        "> - todos deberan estar presente a la hora seleccionada\n"
        "> - ningun miembro que no sea el dueño/a de la fiesta no podra hacer cosas que molesten al organizador.\n"
        "--------------------------------\n"
        f"organizado por: {usuario.mention}, creditado por; AcademyEvents"
    )

    embed.set_thumbnail(url=usuario.display_avatar.url)

    await canal.send(embed=embed)

    await i.response.send_message("Invitación enviada 🪩", ephemeral=True)

# -------------------------
# REGLAS_COMAND
# -------------------------
@bot.tree.command(name="Reglas")

embed = discord.embed( 
    title="{Reglas",
    color=COLOR
)

embed.description = (
    f"> - 𝙍𝙚𝙨𝙥𝙚𝙩𝙤 𝙖𝙣𝙩𝙚 𝙩𝙤𝙙𝙤 ╸𝘴𝘦 𝘢𝘮𝘢𝘣𝘭𝘦 𝘤𝘰𝘯 𝘭𝘰𝘴 𝘥𝘦𝘮𝘢𝘴, 𝘳𝘦𝘴𝘱𝘦𝘵𝘢 𝘨𝘶𝘴𝘵𝘰𝘴 𝘺 𝘢𝘷𝘪𝘴𝘢 𝘢 𝘶𝘯 𝘰𝘸𝘯𝘦𝘳 𝘦𝘭 𝘤𝘰𝘮𝘱𝘰𝘳𝘵𝘢𝘮𝘪𝘦𝘯𝘵𝘰 𝘥𝘦 𝘢𝘭𝘨𝘶𝘪𝘦𝘯\n"
    f"> - 𝙘𝙤𝙣𝙩𝙚𝙣𝙞𝙙𝙤 𝙥𝙖𝙧𝙖 𝙖𝙙𝙪𝙡𝙩𝙤𝙨 ╸𝘯𝘰 𝘦𝘯𝘷𝘪𝘢𝘳 𝘤𝘰𝘯𝘵𝘦𝘯𝘥𝘦𝘳 𝘴𝘦𝘹𝘶𝘢𝘭 𝘦𝘯 𝘓𝘰𝘴 𝘤𝘢𝘯𝘢𝘭𝘦𝘴 𝘲𝘶𝘦 𝘯𝘰 𝘤𝘰𝘳𝘳𝘦𝘴𝘱𝘰𝘯𝘥𝘦𝘯\n"
    f"> - 𝙨𝙥𝙖𝙢 ╸𝘮𝘢𝘯𝘥𝘢𝘳 𝘮𝘶𝘤𝘩𝘰𝘴 𝘮𝘦𝘯𝘴𝘢𝘫𝘦𝘴 𝘢 𝘭𝘢 𝘷𝘦𝘻 𝘤𝘶𝘦𝘯𝘵𝘢 𝘤𝘰𝘮𝘰 𝘴𝘱𝘢𝘮\n"
    f"> - 𝙢𝙚𝙣𝙨𝙖𝙟𝙚𝙨 𝙣𝙤 𝙘𝙤𝙧𝙧𝙚𝙨𝙥𝙤𝙣𝙙𝙚𝙣𝙩𝙚𝙨 ╸𝘦𝘯𝘷𝘪𝘢𝘳 𝘮𝘦𝘯𝘴𝘢𝘫𝘦𝘴 𝘲𝘶𝘦 𝘯𝘰 𝘤𝘰𝘳𝘳𝘦𝘴𝘱𝘰𝘯𝘥𝘦𝘯 𝘢𝘭 𝘤𝘢𝘯𝘢𝘭\n"
)

embed.set_thumbnail(url=usario.display_avatar.url)

await canal.send(embed=embed)

await i.response.send_message("Reglas enviadas 📖", ephemeral=True)

# -------------------------
# RUN
# -------------------------
load_data()
from flask import Flask
import threading

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot activo"

def run_web():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_web).start()
bot.run(TOKEN)
