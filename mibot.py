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
tienda = {}
objetos = {"casa🏠": {"precio": 5000, "stock": 999}}
casas = {}

# -------------------------
# 💾 DATA
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
            "veces_debe": 0
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

    @discord.ui.button(label="⚙️ Comandos", style=discord.ButtonStyle.blurple)
    async def comandos(self, i: discord.Interaction, b: discord.ui.Button):

        if not self.es_dueno(i):
            return await i.response.send_message("No es tu casa", ephemeral=True)

        await i.response.send_message(
            "❤️ /kiss\n🤗 /hug\n😈 +18 comandos incluidos",
            ephemeral=True
        )

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

    categoria = discord.utils.get(i.guild.categories, name="CASAS")
    if not categoria:
        categoria = await i.guild.create_category("CASAS")

    numero = len(casas) + 1

    canal = await i.guild.create_text_channel(
        f"casa-{numero}",
        category=categoria
    )

    casas[uid] = canal.id
    save_data()

    embed = discord.Embed(title="Controls", color=COLOR)
    embed.set_thumbnail(url=i.user.display_avatar.url)

    await canal.send(embed=embed, view=CasaView(i.user.id))

    await i.response.send_message(f"Tienes casa #{numero} 🏠", ephemeral=True)

# -------------------------
# CONTROLS
# -------------------------
@bot.tree.command(name="controls")
async def controls(i: discord.Interaction):

    embed = discord.Embed(title="Controls", color=COLOR)
    embed.set_thumbnail(url=i.user.display_avatar.url)

    await i.response.send_message(embed=embed, view=CasaView(i.user.id))

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
tienda = {}
objetos = {"casa🏠": {"precio": 5000, "stock": 999}}
casas = {}

# -------------------------
# 💾 DATA
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
            "veces_debe": 0
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

    @discord.ui.button(label="⚙️ Comandos", style=discord.ButtonStyle.blurple)
    async def comandos(self, i: discord.Interaction, b: discord.ui.Button):

        if not self.es_dueno(i):
            return await i.response.send_message("No es tu casa", ephemeral=True)

        await i.response.send_message(
            "❤️ /kiss\n🤗 /hug\n😈 +18 comandos incluidos",
            ephemeral=True
        )

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

    categoria = discord.utils.get(i.guild.categories, name="CASAS")
    if not categoria:
        categoria = await i.guild.create_category("CASAS")

    numero = len(casas) + 1

    canal = await i.guild.create_text_channel(
        f"casa-{numero}",
        category=categoria
    )

    casas[uid] = canal.id
    save_data()

    embed = discord.Embed(title="Controls", color=COLOR)
    embed.set_thumbnail(url=i.user.display_avatar.url)

    await canal.send(embed=embed, view=CasaView(i.user.id))

    await i.response.send_message(f"Tienes casa #{numero} 🏠", ephemeral=True)

# -------------------------
# CONTROLS
# -------------------------
@bot.tree.command(name="controls")
async def controls(i: discord.Interaction):

    embed = discord.Embed(title="Controls", color=COLOR)
    embed.set_thumbnail(url=i.user.display_avatar.url)

    await i.response.send_message(embed=embed, view=CasaView(i.user.id))

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
load_data()
bot.run(TOKEN)
