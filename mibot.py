import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
import time
import random
import string

# --- CONFIG ---
TOKEN = os.getenv("TOKEN")
COLOR = 0x000000

# --- BASE DE DATOS ---
data = {}
tienda_roles = {}
prestamos = []
bank_accounts = {}

# --- BOT ---
class DarkyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        await self.tree.sync()

bot = DarkyBot()

# -------------------------
# 🧠 SISTEMA BANCARIO
# -------------------------

def generate_bank_code():
    return "DB-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))

def init_user(uid: str):
    if uid not in data:
        data[uid] = {
            "credito": 0,
            "dinero_transferido": 0,
            "ha_transferido": 0,
            "debe": 0,
            "prestado": 0
        }

# --- CUENTAS AL ENTRAR ---
@bot.event
async def on_member_join(member: discord.Member):

    if member.bot:
        return

    uid = str(member.id)
    init_user(uid)

    if uid not in bank_accounts:
        bank_accounts[uid] = generate_bank_code()

# --- CUENTAS AL INICIAR ---
@bot.event
async def on_ready():
    print("Bot listo")

    for guild in bot.guilds:
        for member in guild.members:
            if member.bot:
                continue

            uid = str(member.id)
            init_user(uid)

            if uid not in bank_accounts:
                bank_accounts[uid] = generate_bank_code()

    bot.loop.create_task(revisar_prestamos())

# --- DINERO PASIVO ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = str(message.author.id)
    init_user(uid)

    data[uid]["credito"] += 5

    await bot.process_commands(message)

# -------------------------
# 💳 CUENTA
# -------------------------
@bot.tree.command(name="cuenta")
async def cuenta(i: discord.Interaction, usuario: discord.Member = None):

    usuario = usuario or i.user
    uid = str(usuario.id)
    init_user(uid)

    codigo = bank_accounts.get(uid, "SIN CUENTA")

    embed = discord.Embed(
        title="CUENTA BANCARIA",
        description=(
            f"Usuario: {usuario.name}\n"
            f"Código bancario: {codigo}\n"
            f"Créditos: {data[uid]['credito']}$"
        ),
        color=COLOR
    )

    embed.set_thumbnail(url=usuario.display_avatar.url)

    await i.response.send_message(embed=embed)

# -------------------------
# 💰 CARTERA
# -------------------------
@bot.tree.command(name="cartera")
async def cartera(i: discord.Interaction, usuario: discord.Member = None):

    usuario = usuario or i.user
    uid = str(usuario.id)
    init_user(uid)

    d = data[uid]

    embed = discord.Embed(title=f"Cartera de {usuario.name}", color=COLOR)
    embed.description = (
        f"credito: {d['credito']}$\n"
        f"dinero transferido: {d['dinero_transferido']}$\n"
        f"-----------------------\n"
        f"ha transferido: {d['ha_transferido']}$\n"
        f"debe: {d['debe']}$\n"
        f"prestado: {d['prestado']}$"
    )

    embed.set_thumbnail(url=usuario.display_avatar.url)

    await i.response.send_message(embed=embed)

# -------------------------
# 🎁 REGALAR (ADMIN)
# -------------------------
@bot.tree.command(name="regalar")
@app_commands.checks.has_permissions(administrator=True)
async def regalar(i: discord.Interaction, cantidad: int, usuario: discord.Member):

    uid = str(usuario.id)
    init_user(uid)

    data[uid]["credito"] += cantidad

    embed = discord.Embed(
        title="REGALO DE PARTE DE ADMINISTRACION! 🎁",
        color=COLOR
    )

    embed.description = (
        f"{usuario.name} Has recibido {cantidad} de dinero\n"
        "------------------------------------------------------------------------------\n"
        f"> - ahora tienes {data[uid]['credito']} creditos en tu cartera\n"
        "> - sé inteligente usando tu dinero\n"
        "> - no puedes pedir más dinero !\n"
        "--------------------------------------\n"
        f"de parte de: {i.user.name}, y creditado por: darky bank."
    )

    embed.set_thumbnail(url=usuario.display_avatar.url)

    await i.response.send_message(embed=embed)

# -------------------------
# 🤝 PRESTAR
# -------------------------
class PrestamoView(discord.ui.View):
    def __init__(self, prestador, receptor, cantidad, dias):
        super().__init__(timeout=60)
        self.prestador = prestador
        self.receptor = receptor
        self.cantidad = cantidad
        self.dias = dias

    @discord.ui.button(label="Aceptar", style=discord.ButtonStyle.green)
    async def aceptar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user != self.receptor:
            return await interaction.response.send_message("No es tu préstamo", ephemeral=True)

        p = str(self.prestador.id)
        r = str(self.receptor.id)

        init_user(p)
        init_user(r)

        data[p]["credito"] -= self.cantidad
        data[r]["credito"] += self.cantidad

        data[r]["debe"] += self.cantidad
        data[p]["prestado"] += self.cantidad

        prestamos.append({
            "prestador": p,
            "receptor": r,
            "cantidad": self.cantidad,
            "tiempo": time.time() + (self.dias * 86400)
        })

        await interaction.response.send_message(
            embed=discord.Embed(
                title="PRÉSTAMO ACEPTADO",
                description=f"{self.receptor.mention} recibió ${self.cantidad}",
                color=COLOR
            )
        )

    @discord.ui.button(label="Rechazar", style=discord.ButtonStyle.red)
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user != self.receptor:
            return await interaction.response.send_message("No es tu préstamo", ephemeral=True)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="PRÉSTAMO RECHAZADO",
                description="El préstamo fue rechazado",
                color=COLOR
            )
        )

@bot.tree.command(name="prestar")
async def prestar(i: discord.Interaction, cantidad: int, usuario: discord.Member, dias: int):

    embed = discord.Embed(color=COLOR)

    embed.description = (
        f"{i.user.name} quiere prestar dinero a {usuario.name}\n"
        "-------------------------------------------------------\n"
        f"> - el dinero se debera pagar en {dias} dias\n"
        f"> - la cantidad de dinero prestado sera de ${cantidad}\n"
        "> - si este dinero no es entregado la fecha planeada se le quitara el dinero pendiente al que debe\n"
        "-------------------------------------------------------\n"
        f"{usuario.name} aceptas o rechazas el prestamo?."
    )

    embed.set_thumbnail(url=usuario.display_avatar.url)

    await i.response.send_message(embed=embed, view=PrestamoView(i.user, usuario, cantidad, dias))

# -------------------------
# 💸 DEVOLVER
# -------------------------
@bot.tree.command(name="devolver")
async def devolver(i: discord.Interaction, cantidad: int, usuario: discord.Member):

    p = str(i.user.id)
    r = str(usuario.id)

    init_user(p)
    init_user(r)

    data[p]["debe"] -= cantidad
    data[p]["credito"] -= cantidad
    data[r]["credito"] += cantidad

    embed = discord.Embed(color=COLOR)

    embed.description = (
        f"{i.user.name} ha devuelto el dinero prestado a {usuario.name}\n"
        "-----------------------------------------------------------------------------------------------\n"
        f"> - {i.user.name} ahora tiene 0 deudas\n"
        f"> - la cantidad de dinero prestado fue de {cantidad}\n"
        f"> - {i.user.name} devolvio {cantidad}\n"
        "---------------------------------------------------------------------\n"
        "de parte de: darky bank."
    )

    embed.set_thumbnail(url=i.user.display_avatar.url)

    await i.response.send_message(embed=embed)

# -------------------------
# ⏳ SISTEMA DE COBRO
# -------------------------
async def revisar_prestamos():
    while True:
        ahora = time.time()

        for d in prestamos[:]:
            if ahora >= d["tiempo"]:
                r = d["receptor"]
                p = d["prestador"]
                c = d["cantidad"]

                if data.get(r, {}).get("credito", 0) >= c:
                    data[r]["credito"] -= c
                    data[p]["credito"] += c

                prestamos.remove(d)

        await asyncio.sleep(60)

# -------------------------
# RUN
# -------------------------
bot.run(TOKEN)
