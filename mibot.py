import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import string
import json
import asyncio
import time

# --- CONFIG ---
TOKEN = os.getenv("TOKEN")
COLOR = 0x000000
DB_FILE = "data.json"

data = {}
prestamos = []
advertencias = {}
tienda = {}

# -------------------------
# 💾 SAVE / LOAD
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
# DINERO POR MENSAJE
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
# JOIN
# -------------------------
@bot.event
async def on_member_join(member):
    if member.bot:
        return

    init_user(str(member.id))
    save_data()

# -------------------------
# READY
# -------------------------
@bot.event
async def on_ready():
    print("Bot listo")
    bot.loop.create_task(revisar_prestamos())

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
# TIENDA
# -------------------------
@bot.tree.command(name="tienda-config")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_config(i, rol: discord.Role, precio: int, stock: int):

    tienda[rol.id] = {"precio": precio, "stock": stock}
    await i.response.send_message("Agregado", ephemeral=True)

class TiendaSelect(discord.ui.Select):
    def __init__(self):
        opciones = [
            discord.SelectOption(
                label=str(rid),
                description=f"${item['precio']} | stock {item['stock']}",
                value=str(rid)
            ) for rid, item in tienda.items()
        ]
        super().__init__(placeholder="Selecciona", options=opciones)

    async def callback(self, i: discord.Interaction):

        uid = str(i.user.id)
        init_user(uid)

        rid = int(self.values[0])
        item = tienda[rid]

        if data[uid]["creditos"] < item["precio"]:
            return await i.response.send_message("No tienes dinero", ephemeral=True)

        if item["stock"] <= 0:
            return await i.response.send_message("Sin stock", ephemeral=True)

        role = i.guild.get_role(rid)

        data[uid]["creditos"] -= item["precio"]
        item["stock"] -= 1

        await i.user.add_roles(role)

        save_data()

        await i.response.send_message(f"Compraste {role.mention}", ephemeral=True)

class TiendaView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(TiendaSelect())

@bot.tree.command(name="tienda-set")
async def tienda_set(i):

    embed = discord.Embed(title="Tienda 🏪", color=COLOR)

    for idx, (rid, item) in enumerate(tienda.items(), 1):
        role = i.guild.get_role(rid)
        embed.add_field(
            name=f"{idx}. {role.name}",
            value=f"Precio: {item['precio']} | Stock: {item['stock']}",
            inline=False
        )

    await i.response.send_message(embed=embed, view=TiendaView())

@bot.tree.command(name="tienda-reset")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_reset(i):
    tienda.clear()
    await i.response.send_message("Tienda reseteada")

class PrestamoView(discord.ui.View):
    def __init__(self, prestamista, receptor, cantidad, dias):
        super().__init__(timeout=60)
        self.prestamista = prestamista
        self.receptor = receptor
        self.cantidad = cantidad
        self.dias = dias

    async def disable(self, interaction):
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

    # ✅ ACEPTAR
    @discord.ui.button(label="Aceptar", style=discord.ButtonStyle.green)
    async def aceptar(self, i: discord.Interaction, button: discord.ui.Button):

        if i.user != self.receptor:
            return await i.response.send_message("No es tu préstamo", ephemeral=True)

        uid_p = str(self.prestamista.id)
        uid_r = str(self.receptor.id)

        if data[uid_p]["creditos"] < self.cantidad:
            return await i.response.send_message("El prestamista ya no tiene dinero", ephemeral=True)

        # transferir dinero
        data[uid_p]["creditos"] -= self.cantidad
        data[uid_r]["creditos"] += self.cantidad

        # contadores
        data[uid_p]["veces_presto"] += 1
        data[uid_r]["veces_debe"] += 1

        # guardar préstamo
        prestamos.append({
            "prestamista": uid_p,
            "receptor": uid_r,
            "cantidad": self.cantidad,
            "tiempo": time.time() + (self.dias * 86400)
        })

        save_data()

        await i.response.send_message("Préstamo aceptado", ephemeral=True)
        await self.disable(i)

    # ❌ RECHAZAR
    @discord.ui.button(label="Rechazar", style=discord.ButtonStyle.red)
    async def rechazar(self, i: discord.Interaction, button: discord.ui.Button):

        if i.user != self.receptor:
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
            uid_r = uid
            receptor = i.guild.get_member(int(uid))
            break

    if not receptor:
        return await i.response.send_message("ID bancario no encontrado", ephemeral=True)

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
