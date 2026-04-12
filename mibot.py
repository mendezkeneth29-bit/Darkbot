import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
import time
import random
import string
import json

# --- CONFIG ---
TOKEN = os.getenv("TOKEN")
COLOR = 0x000000
DB_FILE = "data.json"

# 🔥 CAMBIA ESTO PARA RESETEAR TODO
SYSTEM_VERSION = "1.0"

# --- DATA ---
data = {}
tienda_roles = {}
prestamos = []
bank_accounts = {}

# -------------------------
# 💾 SAVE / LOAD
# -------------------------
def load_data():
    global data, tienda_roles, prestamos, bank_accounts

    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            raw = json.load(f)

            saved_version = raw.get("version")

            if saved_version != SYSTEM_VERSION:
                print("⚠️ CAMBIO DE VERSION → RESETEANDO")

                data.clear()
                tienda_roles.clear()
                prestamos.clear()
                bank_accounts.clear()

                save_data()
                return

            data = raw.get("data", {})
            tienda_roles = raw.get("tienda_roles", {})
            prestamos = raw.get("prestamos", [])
            bank_accounts = raw.get("bank_accounts", {})

def save_data():
    with open(DB_FILE, "w") as f:
        json.dump({
            "version": SYSTEM_VERSION,
            "data": data,
            "tienda_roles": tienda_roles,
            "prestamos": prestamos,
            "bank_accounts": bank_accounts
        }, f)

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
# UTIL
# -------------------------
def generate_bank_code():
    return "DB-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))

def init_user(uid):
    if uid not in data:
        data[uid] = {
            "credito": 0,
            "dinero_transferido": 0,
            "ha_transferido": 0,
            "debe": 0,
            "prestado": 0
        }

# -------------------------
# SYNC
# -------------------------
def refresh_user(uid):
    init_user(uid)
    data[uid]["credito"] = max(0, data[uid]["credito"])
    data[uid]["debe"] = max(0, data[uid]["debe"])
    data[uid]["prestado"] = max(0, data[uid]["prestado"])

def refresh_all(guilds):
    for g in guilds:
        for m in g.members:
            if m.bot:
                continue

            uid = str(m.id)

            if uid not in bank_accounts:
                bank_accounts[uid] = generate_bank_code()

            refresh_user(uid)

# -------------------------
# EVENTS
# -------------------------
@bot.event
async def on_member_join(member):
    if member.bot:
        return

    uid = str(member.id)
    init_user(uid)

    if uid not in bank_accounts:
        bank_accounts[uid] = generate_bank_code()

    save_data()

@bot.event
async def on_ready():
    print("Bot listo")

    refresh_all(bot.guilds)
    save_data()

    bot.loop.create_task(revisar_prestamos())

# -------------------------
# MONEY
# -------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = str(message.author.id)
    init_user(uid)

    data[uid]["credito"] += 5

    refresh_user(uid)
    save_data()

    await bot.process_commands(message)

# -------------------------
# CUENTA
# -------------------------
@bot.tree.command(name="cuenta")
async def cuenta(i: discord.Interaction, usuario: discord.Member = None):

    usuario = usuario or i.user
    uid = str(usuario.id)

    refresh_user(uid)

    embed = discord.Embed(
        title="CUENTA BANCARIA",
        description=(
            f"Usuario: {usuario.name}\n"
            f"Código: {bank_accounts.get(uid, 'SIN CUENTA')}\n"
            f"Créditos: {data[uid]['credito']}$"
        ),
        color=COLOR
    )

    embed.set_thumbnail(url=usuario.display_avatar.url)

    await i.response.send_message(embed=embed)

# -------------------------
# CARTERA
# -------------------------
@bot.tree.command(name="cartera")
async def cartera(i: discord.Interaction, usuario: discord.Member = None):

    usuario = usuario or i.user
    uid = str(usuario.id)

    refresh_user(uid)
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
# REGALAR
# -------------------------
@bot.tree.command(name="regalar")
@app_commands.checks.has_permissions(administrator=True)
async def regalar(i, cantidad: int, usuario: discord.Member):

    uid = str(usuario.id)
    init_user(uid)

    data[uid]["credito"] += cantidad

    refresh_user(uid)
    save_data()

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
# PRESTAMOS
# -------------------------
class PrestamoView(discord.ui.View):
    def __init__(self, p, r, c, d):
        super().__init__(timeout=60)
        self.p = p
        self.r = r
        self.c = c
        self.d = d

    async def disable(self, i):
        for x in self.children:
            x.disabled = True
        await i.message.edit(view=self)

    @discord.ui.button(label="Aceptar", style=discord.ButtonStyle.green)
    async def aceptar(self, i, b):

        if i.user != self.r:
            return await i.response.send_message("No es tu préstamo", ephemeral=True)

        p = str(self.p.id)
        r = str(self.r.id)

        data[p]["credito"] -= self.c
        data[r]["credito"] += self.c

        data[r]["debe"] += self.c
        data[p]["prestado"] += self.c

        prestamos.append({
            "prestador": p,
            "receptor": r,
            "cantidad": self.c,
            "tiempo": time.time() + (self.d * 86400)
        })

        save_data()

        await i.response.send_message(
            embed=discord.Embed(
                title="PRÉSTAMO ACEPTADO",
                description=f"{self.r.mention} recibió ${self.c}",
                color=COLOR
            )
        )

        await self.disable(i)

    @discord.ui.button(label="Rechazar", style=discord.ButtonStyle.red)
    async def rechazar(self, i, b):

        if i.user != self.r:
            return await i.response.send_message("No es tu préstamo", ephemeral=True)

        await i.response.send_message(
            embed=discord.Embed(
                title="PRÉSTAMO RECHAZADO",
                description="El préstamo fue rechazado",
                color=COLOR
            )
        )

        await self.disable(i)

@bot.tree.command(name="prestar")
async def prestar(i, cantidad: int, usuario: discord.Member, dias: int):

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
# LOOP
# -------------------------
async def revisar_prestamos():
    while True:
        now = time.time()

        for d in prestamos[:]:
            if now >= d["tiempo"]:
                r = d["receptor"]
                p = d["prestador"]
                c = d["cantidad"]

                if data.get(r, {}).get("credito", 0) >= c:
                    data[r]["credito"] -= c
                    data[p]["credito"] += c

                prestamos.remove(d)
                save_data()

        await asyncio.sleep(60)

# -------------------------
# RUN
# -------------------------
load_data()
bot.run(TOKEN)
