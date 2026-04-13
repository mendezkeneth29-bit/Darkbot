import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import string
import json
import time
from flask import Flask
from threading import Thread

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
            "veces_debe": 0,
            "compras": 0
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
                return await i.response.send_message("No tienes suficiente dinero", ephemeral=True)

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
                "--------------------------------------------------\n"
                f"> - ahora {usuario.mention} tiene {data[uid]['creditos']} creditos\n"
                "> - usalos con inteligencia\n"
                "------------------------------\n"
                f"enviado por: {i.user.mention}, creditado por: DarkyBank"
            )

            embed.set_thumbnail(url=usuario.display_avatar.url)

            return await i.response.send_message(embed=embed)

    await i.response.send_message("ID bancario no encontrado", ephemeral=True)

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
async def tienda_config(i: discord.Interaction, rol: discord.Role, precio: int, stock: int):

    tienda[rol.id] = {"precio": precio, "stock": stock}
    await i.response.send_message("Agregado", ephemeral=True)

class TiendaSelect(discord.ui.Select):
    def __init__(self):

        if not tienda:
            opciones = [discord.SelectOption(label="Sin items", value="none")]
        else:
            opciones = [
                discord.SelectOption(
                    label=str(rid),
                    description=f"${item['precio']} | stock {item['stock']}",
                    value=str(rid)
                )
                for rid, item in tienda.items()
            ]

        super().__init__(placeholder="Selecciona", options=opciones)

    async def callback(self, i: discord.Interaction):

        if self.values[0] == "none":
            return await i.response.send_message("No hay nada en la tienda", ephemeral=True)

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

        # contar compras
        data[uid]["compras"] = data[uid].get("compras", 0) + 1

        await i.user.add_roles(role)
        save_data()

        await i.response.send_message(f"Compraste {role.mention}", ephemeral=True)

class TiendaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TiendaSelect())

@bot.tree.command(name="tienda-set")
async def tienda_set(i: discord.Interaction):

    if not tienda:
        return await i.response.send_message("La tienda está vacía", ephemeral=True)

    embed = discord.Embed(title="Tienda 🏪", color=COLOR)

    for idx, (rid, item) in enumerate(tienda.items(), 1):
        role = i.guild.get_role(rid)

        embed.add_field(
            name=f"{idx}. {role.name if role else 'Rol eliminado'}",
            value=f"Precio: {item['precio']} | Stock: {item['stock']}",
            inline=False
        )

    await i.response.send_message(embed=embed, view=TiendaView())

@bot.tree.command(name="tienda-reset")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_reset(i: discord.Interaction):

    tienda.clear()
    await i.response.send_message("Tienda reseteada", ephemeral=True)

# -------------------------
# PRESTAMOS
# -------------------------
class PrestamoView(discord.ui.View):
    def __init__(self, p, r, c, d):
        super().__init__(timeout=60)
        self.p, self.r, self.c, self.d = p, r, c, d

    async def disable(self, i):
        for item in self.children:
            item.disabled = True
        await i.message.edit(view=self)

    @discord.ui.button(label="Aceptar", style=discord.ButtonStyle.green)
    async def aceptar(self, i: discord.Interaction, b: discord.ui.Button):

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

        prestamos.append({
            "prestamista": uid_p,
            "receptor": uid_r,
            "cantidad": self.c,
            "tiempo": time.time() + (self.d * 86400)
        })

        save_data()

        await i.response.send_message("Préstamo aceptado", ephemeral=True)
        await self.disable(i)

    @discord.ui.button(label="Rechazar", style=discord.ButtonStyle.red)
    async def rechazar(self, i: discord.Interaction, b: discord.ui.Button):

        if i.user != self.r:
            return await i.response.send_message("No es tu préstamo", ephemeral=True)

        await i.response.send_message("Préstamo rechazado", ephemeral=True)
        await self.disable(i)

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
# FLASK (para Render)
# -------------------------
app = Flask('')

@app.route('/')
def home():
    return "Bot activo"

def run():
    app.run(host='0.0.0.0', port=10000)

Thread(target=run).start()

# -------------------------
# RUN
# -------------------------
load_data()
bot.run(TOKEN)
